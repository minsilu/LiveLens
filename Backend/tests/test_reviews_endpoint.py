import pytest
import os
from fastapi.testclient import TestClient

# Mock environmental vars before importing the app
os.environ["USE_LOCAL_STORAGE"] = "True"
os.environ["DATABASE_URL"] = "sqlite:///./test_dev.db"

# Create a fresh database
from sqlalchemy import create_engine, text
engine = create_engine("sqlite:///./test_dev.db")
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS Reviews;"))
    conn.execute(text("DROP TABLE IF EXISTS Seats;"))
    conn.execute(text("DROP TABLE IF EXISTS Events;"))
    conn.execute(text("DROP TABLE IF EXISTS Venues;"))
    conn.execute(text("DROP TABLE IF EXISTS Users;"))

# Let's import database to trigger the creation of tables (including our new Seats UNIQUE constraint)
import api.database as db_init

# Now we populate some mock data into test_dev.db
with engine.begin() as conn:
    conn.execute(text("INSERT INTO Users (id, email, password_hash) VALUES ('test-user', 'test@example.com', 'h4sh')"))
    conn.execute(text("INSERT INTO Venues (id, name, city) VALUES ('test-venue', 'Test Arena', 'NY')"))
    conn.execute(text("INSERT INTO Events (id, venue_id, name) VALUES ('test-event', 'test-venue', 'Test Concert')"))
    # We consciously DO NOT insert a Seat to see if the upsert logic creates it.

from api.main import app
from api.routes.reviews import get_current_user

client = TestClient(app)

# Override the auth dependency to mock a logged-in user
async def override_get_current_user():
    return "test-user"

app.dependency_overrides[get_current_user] = override_get_current_user

def test_create_review_with_auto_seat_creation():
    payload = {
        "event_id": "test-event",
        "venue_id": "test-venue",
        "section": "101",
        "row": "A",
        "seat_number": "1",
        "rating_visual": 5,
        "rating_sound": 4,
        "rating_value": 3,
        "price_paid": 100.0,
        "text": "Great show!",
        "images": None
    }
    
    response = client.post("/reviews/", json=payload)
    
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert "review_id" in data
    assert data["message"] == "Review submitted successfully"

    # Verify the seat was actually created in the DB
    with engine.begin() as conn:
        seat = conn.execute(text("SELECT id, venue_id, section, row, seat_number FROM Seats")).fetchone()
        assert seat is not None
        assert seat[1] == "test-venue"
        assert seat[2] == "101"

    # Now make a SECOND review for the same exact seat to test the ON CONFLICT DO UPDATE behavior
    payload2 = {
        "event_id": "test-event",
        "venue_id": "test-venue",
        "section": "101",
        "row": "A",
        "seat_number": "1",
        "rating_visual": 5,
        "rating_sound": 5,
        "rating_value": 5,
        "price_paid": 50.0,
        "text": "Second time sitting here",
        "images": None
    }
    
    response2 = client.post("/reviews/", json=payload2)
    assert response2.status_code == 200, f"Second POST failed: {response2.text}"
    
    # We should still only have ONE seat in the database
    with engine.begin() as conn:
        seat_count = conn.execute(text("SELECT COUNT(*) FROM Seats")).scalar()
        assert seat_count == 1, f"Expected 1 seat, got {seat_count}"
        
def test_create_review_invalid_event():
    payload = {
        "event_id": "invalid-event",
        "venue_id": "test-venue",
        "section": "101",
        "row": "A",
        "seat_number": "1",
        "rating_visual": 5,
        "rating_sound": 4,
        "rating_value": 3,
        "price_paid": 100.0,
        "text": "Should fail",
        "images": None
    }
    
    response = client.post("/reviews/", json=payload)
    assert response.status_code == 400
    assert "Invalid event_id" in response.json()["detail"]

def test_update_images_via_patch():
    # First create a review normally to get an ID
    payload = {
        "event_id": "test-event",
        "venue_id": "test-venue",
        "section": "202",
        "row": "B",
        "seat_number": "2",
        "rating_visual": 5,
        "rating_sound": 5,
        "rating_value": 5,
        "price_paid": 200.0,
        "text": "Updating images test",
        "images": None
    }
    
    res = client.post("/reviews/", json=payload)
    review_id = res.json()["review_id"]
    
    # Now test the PATCH endpoint
    patch_payload = {
        "images": ["http://s3.url/image1.jpg", "http://s3.url/image2.jpg"]
    }
    
    res_patch = client.patch(f"/reviews/{review_id}/images", json=patch_payload)
    assert res_patch.status_code == 200
    assert res_patch.json()["message"] == "Review images updated successfully"
    
    # Verify DB update
    with engine.begin() as conn:
        images_json = conn.execute(text("SELECT images FROM Reviews WHERE id = :id"), {"id": review_id}).scalar()
        assert "image1.jpg" in images_json
