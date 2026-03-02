from fastapi.testclient import TestClient
import os

# Ensure local testing DB is used
os.environ["DATABASE_URL"] = "sqlite:///./test_dev.db"

# Import our app and database setup
from api.main import app
import api.database as db_init
from sqlalchemy import create_engine, text

# Populate mock data
engine = create_engine("sqlite:///./test_dev.db")
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS Seats;"))
    conn.execute(text("DROP TABLE IF EXISTS Events;"))
    conn.execute(text("DROP TABLE IF EXISTS Venues;"))

# Let db_init recreate them
with engine.begin() as conn:
    # 1. VENUES
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Venues (
            id TEXT PRIMARY KEY,
            name TEXT,
            city TEXT,
            capacity INTEGER,
            tags TEXT,
            seat_map_2d_url TEXT
        )
    """))
    conn.execute(text("INSERT INTO Venues (id, name, seat_map_2d_url) VALUES ('test-v1', 'Scotiabank Arena', 'http://map1.png')"))
    conn.execute(text("INSERT INTO Venues (id, name, seat_map_2d_url) VALUES ('test-v2', 'MSG', 'http://map2.png')"))

    # 2. EVENTS
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Events (
            id TEXT PRIMARY KEY,
            venue_id TEXT REFERENCES Venues(id),
            name TEXT,
            artist TEXT,
            genre TEXT,
            event_date DATE,
            ticket_url TEXT
        )
    """))
    conn.execute(text("INSERT INTO Events (id, venue_id, name, event_date) VALUES ('test-e1', 'test-v1', 'Taylor Swift Concert', '2026-05-15')"))
    conn.execute(text("INSERT INTO Events (id, venue_id, name, event_date) VALUES ('test-e2', 'test-v1', 'Drake Concert', '2026-06-20')"))
    conn.execute(text("INSERT INTO Events (id, venue_id, name, event_date) VALUES ('test-e3', 'test-v2', 'Hans Zimmer', '2026-07-01')"))

    # 3. SEATS
    conn.execute(text("""
         CREATE TABLE IF NOT EXISTS Seats (
            id TEXT PRIMARY KEY,
            venue_id TEXT REFERENCES Venues(id),
            section TEXT,
            row TEXT,
            seat_number TEXT,
            distance_to_stage FLOAT,
            UNIQUE(venue_id, section, row, seat_number)
         )
    """))
    # We add duplicate sections on purpose to test the DISTINCT query
    conn.execute(text("INSERT INTO Seats (id, venue_id, section, row, seat_number) VALUES ('sid-1', 'test-v1', '101', 'A', '1')"))
    conn.execute(text("INSERT INTO Seats (id, venue_id, section, row, seat_number) VALUES ('sid-2', 'test-v1', '101', 'A', '2')"))
    conn.execute(text("INSERT INTO Seats (id, venue_id, section, row, seat_number) VALUES ('sid-3', 'test-v1', '102', 'B', '1')"))
    conn.execute(text("INSERT INTO Seats (id, venue_id, section, row, seat_number) VALUES ('sid-4', 'test-v1', 'VIP', '1', '1')"))

client = TestClient(app)

def test_events_dictionary():
    # 1. Test fetch all events
    res = client.get("/review-form/events")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    # Check manual formatting
    assert data[0]["display_name"] == "Hans Zimmer (2026-07-01)"

    # 2. Test fetching events with venue filter
    res2 = client.get("/review-form/events?venue_id=test-v1")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2) == 2
    assert all(item["venue_id"] == "test-v1" for item in data2)

def test_venue_metadata():
    res = client.get("/review-form/venues/test-v1")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Scotiabank Arena"
    assert data["seat_map_2d_url"] == "http://map1.png"
    # Important: The available_sections should be unique and match the 3 distinct ones we inserted (101, 102, VIP)
    assert len(data["available_sections"]) == 3
    assert set(data["available_sections"]) == {"101", "102", "VIP"}
    
    # Test not found
    res404 = client.get("/review-form/venues/nonexistent")
    assert res404.status_code == 404

if __name__ == "__main__":
    test_events_dictionary()
    test_venue_metadata()
    print("✅ All Catalog Bridge API tests passed successfully!")
