import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app
from sqlalchemy import text

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Create the Users table inside the local SQLite db before testing."""
    from api.database import engine
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS Users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_incognito BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
        """))
        # Clean up any residual users from previous local runs
        conn.execute(text("DELETE FROM Users WHERE email LIKE '%googleauth%'"))

@patch("api.routes.google_auth.id_token.verify_oauth2_token")
def test_google_auth_registration(mock_verify):
    """Test standard registration flow via Google Auth."""
    # Mock the return value of verify_oauth2_token
    mock_verify.return_value = {"email": "test_googleauth_registration@example.com"}
    
    payload = {
        "token": "dummy_valid_google_token"
    }
    
    response = client.post("/auth/google", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["message"] == "User registered successfully via Google"
    assert data["token_type"] == "bearer"

@patch("api.routes.google_auth.id_token.verify_oauth2_token")
def test_google_auth_login(mock_verify):
    """Test login flow for an existing user via Google Auth."""
    email = "test_googleauth_login@example.com"
    
    # Register first
    mock_verify.return_value = {"email": email}
    payload = {"token": "dummy_first_token"}
    resp1 = client.post("/auth/google", json=payload)
    assert resp1.status_code == 200
    
    # Login again
    mock_verify.return_value = {"email": email} # same email
    payload_login = {"token": "dummy_second_token"}
    resp2 = client.post("/auth/google", json=payload_login)
    
    assert resp2.status_code == 200
    data = resp2.json()
    assert "access_token" in data
    assert data["message"] == "Login successful"

@patch("api.routes.google_auth.id_token.verify_oauth2_token")
def test_google_auth_invalid_token(mock_verify):
    """Test that an invalid token behaves safely."""
    # Setup mock to raise ValueError
    mock_verify.side_effect = ValueError("Invalid signature")
    
    payload = {
        "token": "dummy_invalid_google_token"
    }
    
    response = client.post("/auth/google", json=payload)
    assert response.status_code == 401
    assert "Invalid Google token" in response.json()["detail"]
