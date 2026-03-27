import os
import json
import logging
from typing import List

try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

logger = logging.getLogger(__name__)

# We will initialize the client lazily inside the function 
# to ensure load_dotenv() has already populated os.environ.
_client = None

def get_client():
    global _client
    if _client is None:
        if ZhipuAI is None:
            print("ZhipuAI package is not installed.")
            return None
        
        api_key = os.environ.get("ZHIPUAI_API_KEY")
        if not api_key:
            print("ERROR: ZHIPUAI_API_KEY environment variable is missing!")
            return None
            
        try:
            _client = ZhipuAI(api_key=api_key)
        except Exception as e:
            print(f"Failed to initialize ZhipuAI client: {e}")
            return None
    return _client

def extract_tags(review_text: str) -> List[str]:
    """
    Extracts 1 to 5 concise tags from the given review text using Zhipu AI.
    """
    client = get_client()
    if not client:
        return []

    if not review_text or not review_text.strip():
        return []

    prompt = (
        "You are an AI assistant for a live event review platform. "
        "Your task is to analyze the following review text and extract 1 to 5 highly relevant, "
        "concise tags (1-3 words each) that summarize the key aspects of the user's experience "
        "(e.g., 'Great View', 'Loud Sound', 'Expensive', 'Friendly Staff', 'Comfortable Seats').\n\n"
        "Return ONLY a valid JSON array of strings containing the tags, and nothing else. "
        "Example output: [\"Great View\", \"Loud Sound\"]\n\n"
        f"Review text:\n{review_text}"
    )

    try:
        print(f"DEBUG: Starting ZhipuAI request (review length: {len(review_text)} characters)...")
        response = client.chat.completions.create(
            model="glm-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=60, # Increased timeout for cloud environment
        )
        print("DEBUG: ZhipuAI response received.")
        
        # Extract the content from the response
        content = response.choices[0].message.content
        
        # Clean the response in case the model adds markdown formatting (e.g. ```json ... ```)
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Parse the JSON string into a Python list
        try:
            tags = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"DEBUG: Failed to parse AI response as JSON. Content: {content}")
            return []
        
        if isinstance(tags, list):
            # Limit to max 5 tags just in case
            return tags[:5]
        else:
             print(f"DEBUG: ZhipuAI returned non-list format: {content}")
             return []
             
    except Exception as e:
        print(f"CRITICAL: extract_tags failed. Error type: {type(e).__name__}, Message: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
