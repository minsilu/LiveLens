import os
import json
import time
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from zhipuai import ZhipuAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")

if not DATABASE_URL or not ZHIPUAI_API_KEY:
    print("Error: DATABASE_URL and ZHIPUAI_API_KEY must be set in .env")
    exit(1)

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)

def init_db():
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Ensure tags column exists
    print("Ensuring 'tags' column exists...")
    try:
        cursor.execute("ALTER TABLE Reviews ADD COLUMN IF NOT EXISTS tags JSONB;")
    except Exception as e:
        print(f"Migration note: {e}")
        
    return conn

def fetch_reviews(conn):
    cursor = conn.cursor()
    # Let's fetch the ID, the ratings, and the price.
    cursor.execute("""
        SELECT id, rating_visual, rating_sound, rating_value, overall_rating, price_paid
        FROM Reviews
    """)
    return cursor.fetchall()

def process_review(review_data):
    rev_id, r_vis, r_snd, r_val, r_over, price = review_data
    
    prompt = f"""
You are a real user writing a review for a live event you attended.
Based on your ratings (1 to 5 stars, where 5 is excellent and 1 is terrible):
- Visual Experience: {r_vis}/5
- Sound Quality: {r_snd}/5
- Value for Money: {r_val}/5
- Overall: {r_over}/5
- Ticket Price: ${price:.2f}

Task:
1. Write a short, realistic, and engaging review text (2 to 4 sentences) reflecting these specific ratings. (e.g. If sound is 1/5, complain about it. If everything is 5/5, praise it enthusiastically).
2. Generate 1 to 5 concise tags (1-3 words each) that summarize your experience (e.g. "Great View", "Terrible Acoustics", "Expensive").

Return strictly ONLY a valid JSON object in the following format:
{{
  "text": "Your generated review text here...",
  "tags": ["Tag1", "Tag2"]
}}
"""
    
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="glm-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            content = response.choices[0].message.content.strip()
            
            # Clean up markdown formatting if the model outputs it
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            
            # Validate output format
            if "text" in result and "tags" in result:
                return (rev_id, result["text"], json.dumps(result["tags"]))
            else:
                raise ValueError("Missing 'text' or 'tags' in JSON response")
                
        except Exception as e:
            time.sleep(1) # Backoff
            if attempt == 2:
                print(f"Failed to generate for {rev_id}: {e}")
                return None

def update_db(conn, batch):
    cursor = conn.cursor()
    # Batch update using execute_values
    query = """
        UPDATE Reviews AS r
        SET text = v.text, tags = v.tags::jsonb
        FROM (VALUES %s) AS v(id, text, tags)
        WHERE r.id = v.id::uuid;
    """
    execute_values(cursor, query, batch)
    conn.commit()
    print(f"Successfully updated batch of {len(batch)} reviews.")

def main():
    conn = init_db()
    reviews = fetch_reviews(conn)
    print(f"Fetched {len(reviews)} reviews to process.")
    
    # Process them concurrently
    # Zhipu AI rate limit for glm-4 is usually quite generous, but let's stick to 10 workers to be safe.
    max_workers = 10
    total = len(reviews)
    processed = 0
    batch = []
    BATCH_SIZE = 50
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_review = {executor.submit(process_review, r): r for r in reviews}
        
        for future in as_completed(future_to_review):
            result = future.result()
            processed += 1
            
            if result:
                batch.append(result)
                
            if len(batch) >= BATCH_SIZE:
                update_db(conn, batch)
                batch = []
                
            if processed % 10 == 0 or processed == total:
                elapsed = time.time() - start_time
                print(f"[{processed}/{total}] Elapsed: {elapsed:.1f}s ...")
                
    # Update remaining in the last batch
    if batch:
        update_db(conn, batch)
        
    conn.close()
    print("All reviews have been successfully updated with AI-generated text and tags.")

if __name__ == "__main__":
    main()
