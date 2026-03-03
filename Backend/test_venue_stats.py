import requests
import sys

def test_venue_stats():
    base_url = "http://127.0.0.1:8000"
    endpoint = f"{base_url}/search/venues/stats"
    
    print(f"--- Testing GET {endpoint} ---")
    
    try:
        resp = requests.get(endpoint)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print("Response Data:", data)
            
            # Assertions to ensure the endpoint returns correct structure
            assert "total_venues" in data, "Missing 'total_venues' in response"
            assert "total_reviews" in data, "Missing 'total_reviews' in response"
            assert "avg_rating" in data, "Missing 'avg_rating' in response"
            assert "satisfaction" in data, "Missing 'satisfaction' in response"
            
            print("✅ All basic structural assertions passed!")
            
            print("\nDetailed Stats:")
            print(f"- Total Venues: {data['total_venues']}")
            print(f"- Total Reviews: {data['total_reviews']}")
            print(f"- Average Rating: {data['avg_rating']}")
            print(f"- Satisfaction: {data['satisfaction']}%")
            
        else:
            print(f"❌ Failed to fetch stats. Response: {resp.text}")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Ensure the FastAPI backend is running at {base_url}")
        sys.exit(1)

if __name__ == "__main__":
    test_venue_stats()
