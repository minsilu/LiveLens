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

import uuid

@pytest.fixture(scope="module")
def seed_user():
    """Insert a test user and return a valid JWT token for that user."""
    from api.database import engine
    user_id = "11111111-2222-3333-4444-555555555555" # Use a valid UUID format
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ReviewDrafts WHERE user_id = :id"), {"id": user_id})
        conn.execute(text("DELETE FROM Users WHERE id = :id"), {"id": user_id})
        conn.execute(
            text("INSERT INTO Users (id, email, password_hash) VALUES (:id, :e, :p)"),
            {"id": user_id, "e": "draftuser@test.com", "p": get_password_hash("password")},
        )

    token = create_access_token({"sub": user_id}, expires_delta=timedelta(hours=1))
    yield {"user_id": user_id, "token": token}

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ReviewDrafts WHERE user_id = :id"), {"id": user_id})
        conn.execute(text("DELETE FROM Users WHERE id = :id"), {"id": user_id})

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_save_draft_without_auth():
    """Saving a draft without JWT should return 401."""
    response = client.post("/review-drafts/", json={
        "draft_data": {"event_id": "123", "text": "Draft content"}
    })
    assert response.status_code == 401

def test_save_draft_success(seed_user):
    """Successfully save a review draft."""
    response = client.post(
        "/review-drafts/",
        json={"draft_data": {"event_id": "123", "text": "My first draft"}},
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "draft_id" in data
    assert data["message"] == "Draft saved successfully"
    return data["draft_id"]

def test_get_drafts_success(seed_user):
    """Retrieving drafts should return the one just saved."""
    response = client.get(
        "/review-drafts/",
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    assert response.status_code == 200
    drafts = response.json()
    assert len(drafts) >= 1
    # Check that draft_data is correctly parsed
    assert "event_id" in drafts[0]["draft_data"]
    assert drafts[0]["draft_data"]["text"] == "My first draft"

def test_update_draft_success(seed_user):
    """Updating an existing draft."""
    # First get the drafts to find the ID
    get_res = client.get("/review-drafts/", headers={"Authorization": f"Bearer {seed_user['token']}"})
    draft_id = get_res.json()[0]["id"]
    
    response = client.post(
        "/review-drafts/",
        json={"id": draft_id, "draft_data": {"event_id": "123", "text": "Updated draft"}},
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    assert response.status_code == 200
    
    # Verify update
    get_res2 = client.get("/review-drafts/", headers={"Authorization": f"Bearer {seed_user['token']}"})
    updated_draft = get_res2.json()[0]
    assert updated_draft["draft_data"]["text"] == "Updated draft"

def test_delete_draft_success(seed_user):
    """Deleting a draft should work and it should not be returned anymore."""
    get_res = client.get("/review-drafts/", headers={"Authorization": f"Bearer {seed_user['token']}"})
    drafts = get_res.json()
    assert len(drafts) > 0
    draft_id = drafts[0]["id"]
    
    del_res = client.delete(
        f"/review-drafts/{draft_id}",
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    assert del_res.status_code == 200
    
    get_res_after = client.get("/review-drafts/", headers={"Authorization": f"Bearer {seed_user['token']}"})
    drafts_after = get_res_after.json()
    assert not any(d["id"] == draft_id for d in drafts_after)

def test_delete_draft_not_found(seed_user):
    """Deleting a non-existent draft should return 404."""
    del_res = client.delete(
        "/review-drafts/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {seed_user['token']}"},
    )
    assert del_res.status_code == 404
