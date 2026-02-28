import pytest
from fastapi.testclient import TestClient
from api.main import app
from sqlalchemy import create_engine, text
import os

# Create a TestClient mapped to our FastAPI app
client = TestClient(app)

# The Test Environment is using SQLite directly from the .env reading!
# We can optionally inject a setup script to create tables in SQLite before testing.

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
        conn.execute(text("DELETE FROM Users WHERE email LIKE '%testuser%'"))

def test_health_check():
    """Tests if the core server endpoints respond."""
    response = client.get("/")
    assert response.status_code == 200

def test_user_registration():
    """Test standard registration flow."""
    payload = {
        "email": "testuser_registration@example.com",
        "password": "supersecurepassword123",
        "is_incognito": True
    }
    
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["message"] == "User registered successfully"

def test_duplicate_registration_fails():
    """Test that you cannot register the same user twice."""
    payload = {
        "email": "testuser_duplicate@example.com",
        "password": "password123"
    }
    # Register once
    client.post("/auth/register", json=payload)
    
    # Try again
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_user_login():
    """Test the login flow with valid and invalid credentials."""
    email = "testuser_login@example.com"
    password = "password123"
    payload = {"email": email, "password": password}
    
    # Register
    client.post("/auth/register", json=payload)
    
    # Login success
    resp_success = client.post("/auth/login", json=payload)
    assert resp_success.status_code == 200
    assert "access_token" in resp_success.json()
    
    # Login failure
    payload_bad = {"email": email, "password": "wrongpassword"}
    resp_fail = client.post("/auth/login", json=payload_bad)
    assert resp_fail.status_code == 401
    assert resp_fail.json()["detail"] == "Invalid credentials"
