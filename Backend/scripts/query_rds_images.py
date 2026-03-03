import psycopg2
import os
import json
from dotenv import load_dotenv

# Load env variables from Backend/.env
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def fetch_data_from_rds():
    conn = None
    cursor = None
    
    try:
        # 1. Establish the connection
        print("Connecting to the RDS instance...")
        conn = psycopg2.connect(DATABASE_URL)
        
        # 2. Create a cursor object
        cursor = conn.cursor()
        
        # 3. Execute a SQL query
        query = "SELECT id, name, seat_map_meta FROM Venues;"
        cursor.execute(query)
        
        # 4. Retrieve and process the data
        records = cursor.fetchall()
        print(f"Retrieved {cursor.rowcount} rows:")
        
        for row in records:
            print(row)
            # venue_id, venue_name, seat_map_meta = row
            # print(f"\nVenue: {venue_name} (ID: {venue_id})")
            
            # if seat_map_meta:
            #     try:
            #         meta_json = seat_map_meta if isinstance(seat_map_meta, dict) else json.loads(seat_map_meta)
            #         images = meta_json.get("images", [])
            #         if images:
            #             print(f"  Found {len(images)} images:")
            #             for img_url in images:
            #                 print(f"  - {img_url}")
            #         else:
            #             print("  No images found in seat_map_meta.")
            #     except json.JSONDecodeError:
            #         print("  Failed to parse seat_map_meta as JSON.")
            # else:
            #     print("  No seat_map_meta available.")

    except psycopg2.Error as e:
        print(f"Database connection or execution failed: {e}")
        
    finally:
        # 5. Clean up resources
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    fetch_data_from_rds()
