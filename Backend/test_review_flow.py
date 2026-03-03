import os
import sys
import uuid
import requests
from dotenv import load_dotenv
from sqlalchemy import text

# Adjust path to import api modules
sys.path.insert(0, os.path.abspath('.'))

from api.database import engine
from api.auth_utils import create_access_token

def run_test():
    if not engine:
        print("Error: No database connection")
        return

    # 1. Setup Data
    user_id = str(uuid.uuid4())
    user_id_2 = str(uuid.uuid4())
    venue_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())

    with engine.begin() as conn:
        # SQLite vs Postgres syntax handled mostly by SA text
        conn.execute(text("INSERT INTO Users (id, email, password_hash) VALUES (:id, :email, :pw)"),
                     {"id": user_id, "email": f"test_{user_id}@test.com", "pw": "fakehash"})
        conn.execute(text("INSERT INTO Users (id, email, password_hash) VALUES (:id, :email, :pw)"),
                     {"id": user_id_2, "email": f"test_{user_id_2}@test.com", "pw": "fakehash2"})
        conn.execute(text("INSERT INTO Venues (id, name) VALUES (:id, :name)"),
                     {"id": venue_id, "name": "Test Venue"})
        conn.execute(text("INSERT INTO Events (id, venue_id, name) VALUES (:id, :v_id, :name)"),
                     {"id": event_id, "v_id": venue_id, "name": "Test Event"})

    token = create_access_token(data={"sub": user_id})
    token_2 = create_access_token(data={"sub": user_id_2})

    headers = {"Authorization": f"Bearer {token}"}
    headers_2 = {"Authorization": f"Bearer {token_2}"}

    base_url = "http://127.0.0.1:8000"

    print("--- 1. Testing Create Review ---")
    review_data = {
        "event_id": event_id,
        "venue_id": venue_id,
        "section": "GA",
        "row": "1",
        "seat_number": "1",
        "rating_visual": 5,
        "rating_sound": 5,
        "rating_value": 5,
        "price_paid": 100.0,
        "text": "Great!"
    }
    resp = requests.post(f"{base_url}/reviews/", json=review_data, headers=headers)
    print("Create Response:", resp.status_code, resp.json())
    assert resp.status_code == 200, f"Create review failed: {resp.text}"
    review_id = resp.json()["review_id"]

    print("--- 2. Testing Presigned URL ---")
    resp = requests.get(
        f"{base_url}/reviews/img-presigned-url", 
        params={"review_id": review_id, "pic_num": 1, "filename": "test.png", "content_type": "image/png"},
        headers=headers
    )
    print("Presigned URL Response:", resp.status_code, resp.json())
    assert resp.status_code == 200, "Presigned URL failed"
    future_url = resp.json()["future_url"]

    print("--- 3. Testing PATCH Images with WRONG User ---")
    resp_err = requests.patch(
        f"{base_url}/reviews/img-database?review_id={review_id}",
        json={"images": [future_url]},
        headers=headers_2
    )
    print("PATCH Wrong User Response:", resp_err.status_code, resp_err.json())
    assert resp_err.status_code == 403, f"Expected 403, got {resp_err.status_code}"

    print("--- 4. Testing PATCH Images with CORRECT User ---")
    resp = requests.patch(
        f"{base_url}/reviews/img-database?review_id={review_id}",
        json={"images": [future_url]},
        headers=headers
    )
    print("PATCH Correct User Response:", resp.status_code, resp.json())
    assert resp.status_code == 200, "PATCH with correct user failed"

    # Verify DB
    with engine.begin() as conn:
        imgs = conn.execute(text("SELECT images FROM Reviews WHERE id = :id"), {"id": review_id}).scalar()
        print("Images in DB:", imgs)
        assert future_url in imgs, "Image URL not saved in DB"

    print("All tests passed!")

if __name__ == "__main__":
    run_test()
