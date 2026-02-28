import pytest
from fastapi.testclient import TestClient
from api.main import app
from sqlalchemy import text

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def seed_venues():
    """Insert test venues into the local SQLite database before running tests."""
    from api.database import engine
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS Venues (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT,
                capacity INTEGER,
                tags TEXT
            );
        """))
        # Clean up previous test data
        conn.execute(text("DELETE FROM Venues WHERE name LIKE '%TestVenue%'"))

        # Insert deterministic test venues
        test_venues = [
            ("tv-1", "TestVenue Alpha", "Toronto", 20000, '["concerts"]'),
            ("tv-2", "TestVenue Beta", "New York", 15000, '["sports"]'),
            ("tv-3", "TestVenue Gamma", "Toronto", 5000, '["theater"]'),
            ("tv-4", "TestVenue Delta", "London", 25000, '["arena"]'),
        ]
        conn.execute(
            text("INSERT OR IGNORE INTO Venues (id, name, city, capacity, tags) VALUES (:id, :name, :city, :capacity, :tags)"),
            [{"id": v[0], "name": v[1], "city": v[2], "capacity": v[3], "tags": v[4]} for v in test_venues],
        )

    yield

    # Cleanup after tests
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Venues WHERE name LIKE '%TestVenue%'"))


# --- Search (q parameter) ---

def test_search_venues_by_name():
    """Search should match venue names case-insensitively."""
    response = client.get("/search/venues", params={"q": "alpha"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("Alpha" in v["name"] for v in data["results"])


def test_search_venues_by_city():
    """Search should match city names via the q parameter."""
    response = client.get("/search/venues", params={"q": "london"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(v["city"] == "London" for v in data["results"])


def test_search_venues_no_results():
    """Search for a non-existent term should return empty results."""
    response = client.get("/search/venues", params={"q": "zzz_nonexistent_zzz"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []


# --- Filter ---

def test_filter_venues_by_city():
    """Filter by exact city name."""
    response = client.get("/search/venues", params={"city": "Toronto"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert all(v["city"] == "Toronto" for v in data["results"])


def test_filter_venues_by_min_capacity():
    """Filter venues with capacity >= threshold."""
    response = client.get("/search/venues", params={"min_capacity": 20000})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert all(v["capacity"] >= 20000 for v in data["results"])


def test_filter_combined():
    """Combine city filter with min_capacity filter."""
    response = client.get("/search/venues", params={"city": "Toronto", "min_capacity": 10000})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(v["city"] == "Toronto" and v["capacity"] >= 10000 for v in data["results"])


# --- Sort ---

def test_sort_venues_by_capacity_desc():
    """Sort venues by capacity in descending order."""
    response = client.get("/search/venues", params={"q": "TestVenue", "sort_by": "capacity", "order": "desc"})
    assert response.status_code == 200
    venues = response.json()["results"]
    capacities = [v["capacity"] for v in venues]
    assert capacities == sorted(capacities, reverse=True)


def test_sort_venues_by_name_asc():
    """Sort venues by name in ascending order."""
    response = client.get("/search/venues", params={"q": "TestVenue", "sort_by": "name", "order": "asc"})
    assert response.status_code == 200
    venues = response.json()["results"]
    names = [v["name"] for v in venues]
    assert names == sorted(names)


def test_sort_invalid_field():
    """Invalid sort field should return 400."""
    response = client.get("/search/venues", params={"sort_by": "invalid_field"})
    assert response.status_code == 400


# --- Pagination ---

def test_pagination_limit():
    """Limit should control the number of returned results."""
    response = client.get("/search/venues", params={"q": "TestVenue", "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 2
    assert data["total"] >= 4  # We know there are 4 test venues


def test_pagination_offset():
    """Offset should skip the specified number of results."""
    resp_all = client.get("/search/venues", params={"q": "TestVenue", "sort_by": "name", "order": "asc"})
    resp_offset = client.get("/search/venues", params={"q": "TestVenue", "sort_by": "name", "order": "asc", "offset": 2})

    all_venues = resp_all.json()["results"]
    offset_venues = resp_offset.json()["results"]

    assert offset_venues[0]["name"] == all_venues[2]["name"]


# --- All results (no filters) ---

def test_list_all_venues():
    """No filters should return all venues."""
    response = client.get("/search/venues")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 4
