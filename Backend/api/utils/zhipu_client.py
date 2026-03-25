import os
import json
from zhipuai import ZhipuAI
from typing import List
import logging

logger = logging.getLogger(__name__)

# Initialize the ZhipuAI client. It will automatically pick up the ZHIPUAI_API_KEY environment variable.
try:
    client = ZhipuAI(api_key=os.environ.get("ZHIPUAI_API_KEY"))
except Exception as e:
    logger.warning(f"Failed to initialize ZhipuAI client: {e}")
    client = None

def extract_tags(review_text: str) -> List[str]:
    """
    Extracts 1 to 5 concise tags from the given review text using Zhipu AI.
    """
    if not client:
        logger.error("ZhipuAI client is not initialized. Cannot extract tags.")
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
        response = client.chat.completions.create(
            model="glm-4",  # You can change to a faster/cheaper model if needed, like glm-3-turbo
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # Lower temperature for more consistent, deterministic JSON output
        )
        
        # Extract the content from the response
        content = response.choices[0].message.content
        
        # Clean the response in case the model adds markdown formatting (e.g. ```json ... ```)
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Parse the JSON string into a Python list
        tags = json.loads(content)
        
        if isinstance(tags, list):
            # Limit to max 5 tags just in case
            return tags[:5]
        else:
             logger.warning(f"ZhipuAI returned an invalid format for tags: {content}")
             return []
             
    except Exception as e:
        logger.error(f"Error extracting tags with ZhipuAI: {e}")
        return []
