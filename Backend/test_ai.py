import httpx
import json
import asyncio

async def test_ai_endpoint():
    url = "http://127.0.0.1:8000/ai/analyze"
    
    # Test 1: Plain text input
    print("Testing Plain Text Input...")
    payload1 = {
        "input_data": "I want an app feature that lets me track my daily water intake easily.",
        "instructions": "Summarize the core feature requested and suggest 2 UI components to use."
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response1 = await client.post(url, json=payload1, timeout=30.0)
            print("Status Code:", response1.status_code)
            if response1.status_code == 200:
                print("Response JSON:")
                print(json.dumps(response1.json(), indent=2))
            else:
                print("Error Details:", response1.text)
        except Exception as e:
            print(f"Error connecting to {url}: {e}")
            
    print("\n---------------------------\n")
            
    # Test 2: JSON input
    print("Testing JSON Object Input...")
    payload2 = {
        "input_data": {
            "user_id": 123,
            "recent_searches": ["healthy recipes", "workout routines", "meditation fast"],
            "app_usage_hours": 1.5
        },
        "instructions": "Based on this user profile, what kind of content should we recommend on their dashboard?"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response2 = await client.post(url, json=payload2, timeout=30.0)
            print("Status Code:", response2.status_code)
            if response2.status_code == 200:
                print("Response JSON:")
                print(json.dumps(response2.json(), indent=2))
            else:
                 print("Error Details:", response2.text)
        except Exception as e:
            print(f"Error connecting to {url}: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_endpoint())
