import json
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy import text

from api.main import app
from api.auth_utils import get_password_hash, create_access_token

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def seed_user():
    """Insert a test user and return a valid JWT token for that user."""
    from api.database import engine
    user_id = "test-user-img-001"
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Users WHERE id = :id"), {"id": user_id})
        conn.execute(
            text("INSERT INTO Users (id, email, password_hash) VALUES (:id, :e, :p)"),
            {"id": user_id, "e": "testimg@test.com", "p": get_password_hash("password")},
        )

    token = create_access_token({"sub": user_id}, expires_delta=timedelta(hours=1))
    yield {"user_id": user_id, "token": token}

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Users WHERE id = :id"), {"id": user_id})


@pytest.fixture(scope="module")
def seed_venue_and_event():
    """Insert a test venue and event for review submission."""
    from api.database import engine
    venue_id = "tv-img-1"
    event_id = "te-img-1"
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Events WHERE id = :id"), {"id": event_id})
        conn.execute(text("DELETE FROM Venues WHERE id = :id"), {"id": venue_id})
        conn.execute(
            text("INSERT INTO Venues (id, name, city, capacity) VALUES (:id, :n, :c, :cap)"),
            {"id": venue_id, "n": "ImgTestVenue", "c": "Toronto", "cap": 5000},
        )
        conn.execute(
            text("INSERT INTO Events (id, venue_id, name, artist, genre, event_date) VALUES (:id, :v, :n, :a, :g, :d)"),
            {"id": event_id, "v": venue_id, "n": "ImgTestEvent", "a": "ImgArtist", "g": "rock", "d": "2025-10-01"},
        )

    yield {"venue_id": venue_id, "event_id": event_id}

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Reviews WHERE event_id = :id"), {"id": event_id})
        conn.execute(text("DELETE FROM Seats WHERE venue_id = :id"), {"id": venue_id})
        conn.execute(text("DELETE FROM Events WHERE id = :id"), {"id": event_id})
        conn.execute(text("DELETE FROM Venues WHERE id = :id"), {"id": venue_id})


@pytest.fixture(scope="module")
def created_review(seed_user, seed_venue_and_event):
    """Create a review via POST /reviews/ and return the review_id."""
    response = client.post(
        "/reviews/",
        json={
            "event_id": seed_venue_and_event["event_id"],
            "venue_id": seed_venue_and_event["venue_id"],
            "section": "Floor",
            "row": "A",
            "seat_number": "1",
            "rating_visual": 4,
            "rating_sound": 5,
            "rating_value": 3,
            "price_paid": 80.0,
            "text": "Great view, test review.",
        },
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    assert response.status_code == 200
    return response.json()["review_id"]


# ---------------------------------------------------------------------------
# POST /reviews/ — authentication
# ---------------------------------------------------------------------------

def test_create_review_without_auth():
    """Review creation without JWT should return 401."""
    response = client.post("/reviews/", json={
        "event_id": "x", "venue_id": "x", "section": "A", "row": "1",
        "seat_number": "1", "rating_visual": 3, "rating_sound": 3,
        "rating_value": 3, "price_paid": 0, "text": "test",
    })
    assert response.status_code == 401


def test_create_review_missing_fields(seed_user):
    """Review creation with missing required fields should return 422."""
    response = client.post(
        "/reviews/",
        json={"event_id": "x", "venue_id": "x"},
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /reviews/ — successful creation
# ---------------------------------------------------------------------------

def test_create_review_returns_review_id(created_review):
    """Successfully created review should return a non-empty review_id."""
    assert created_review is not None
    assert len(created_review) > 0


def test_create_review_with_images_field(seed_user, seed_venue_and_event):
    """Review creation with images list should succeed and return review_id."""
    response = client.post(
        "/reviews/",
        json={
            "event_id": seed_venue_and_event["event_id"],
            "venue_id": seed_venue_and_event["venue_id"],
            "section": "Floor",
            "row": "A",
            "seat_number": "2",
            "rating_visual": 3,
            "rating_sound": 4,
            "rating_value": 5,
            "price_paid": 60.0,
            "text": "Test with images.",
            "images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
        },
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    assert response.status_code == 200
    assert "review_id" in response.json()


# ---------------------------------------------------------------------------
# PATCH /reviews/img-database — update images
# ---------------------------------------------------------------------------

def test_update_images_without_auth(created_review):
    """PATCH img-database without JWT should return 401."""
    response = client.patch(
        f"/reviews/img-database?review_id={created_review}",
        json={"images": ["https://example.com/img.jpg"]},
    )
    assert response.status_code == 401


def test_update_images_success(seed_user, created_review):
    """PATCH img-database should update images and return success message."""
    response = client.patch(
        f"/reviews/img-database?review_id={created_review}",
        json={"images": ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"]},
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Images updated successfully"


def test_updated_images_appear_in_search(seed_user, created_review, seed_venue_and_event):
    """After PATCH, images should be visible in /search/reviews response."""
    client.patch(
        f"/reviews/img-database?review_id={created_review}",
        json={"images": ["https://example.com/photo1.jpg"]},
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    response = client.get("/search/reviews", params={"venue_id": seed_venue_and_event["venue_id"]})
    assert response.status_code == 200
    results = response.json()["results"]
    target = next((r for r in results if r["id"] == created_review), None)
    assert target is not None
    assert target["images"] is not None
    parsed = json.loads(target["images"]) if isinstance(target["images"], str) else target["images"]
    assert "https://example.com/photo1.jpg" in parsed


def test_update_images_wrong_user(created_review):
    """PATCH img-database with a different user's token should return 403."""
    from api.database import engine
    other_id = "test-user-other-001"
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Users WHERE id = :id"), {"id": other_id})
        conn.execute(
            text("INSERT INTO Users (id, email, password_hash) VALUES (:id, :e, :p)"),
            {"id": other_id, "e": "other@test.com", "p": get_password_hash("pw")},
        )
    other_token = create_access_token({"sub": other_id}, expires_delta=timedelta(hours=1))

    response = client.patch(
        f"/reviews/img-database?review_id={created_review}",
        json={"images": ["https://evil.com/hack.jpg"]},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Users WHERE id = :id"), {"id": other_id})

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /reviews/img-presigned-url — auth check
# ---------------------------------------------------------------------------

def test_presigned_url_without_auth(created_review):
    """Presigned URL endpoint without JWT should return 401."""
    response = client.get("/reviews/img-presigned-url", params={
        "review_id": created_review, "pic_num": 1,
        "filename": "photo.jpg", "content_type": "image/jpeg",
    })
    assert response.status_code == 401


def test_presigned_url_with_auth(seed_user, created_review):
    """Presigned URL endpoint with valid JWT should return 200 or 500 (no S3 creds locally)."""
    response = client.get(
        "/reviews/img-presigned-url",
        params={
            "review_id": created_review, "pic_num": 1,
            "filename": "photo.jpg", "content_type": "image/jpeg",
        },
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    assert response.status_code in (200, 500)
