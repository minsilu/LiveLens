import pytest
from fastapi.testclient import TestClient
from api.main import app
from sqlalchemy import text

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
        conn.execute(text("DELETE FROM Venues WHERE name LIKE '%TestVenue%'"))

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

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Venues WHERE name LIKE '%TestVenue%'"))


@pytest.fixture(scope="module")
def seed_events(seed_venues):
    """Insert test events linked to test venues."""
    from api.database import engine
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Events WHERE id LIKE 'te-%'"))

        test_events = [
            ("te-1", "tv-1", "TestEvent Alpha Concert", "Artist One", "rock", "2025-06-15", "https://tickets.test/1"),
            ("te-2", "tv-1", "TestEvent Beta Show", "Artist Two", "pop", "2025-07-20", "https://tickets.test/2"),
            ("te-3", "tv-2", "TestEvent Gamma Jazz", "Artist Three", "jazz", "2025-08-10", "https://tickets.test/3"),
            ("te-4", "tv-3", "TestEvent Delta Classic", "Artist Four", "classical", "2025-09-05", "https://tickets.test/4"),
        ]
        conn.execute(
            text("INSERT OR IGNORE INTO Events (id, venue_id, name, artist, genre, event_date, ticket_url) "
                 "VALUES (:id, :venue_id, :name, :artist, :genre, :event_date, :ticket_url)"),
            [{"id": e[0], "venue_id": e[1], "name": e[2], "artist": e[3],
              "genre": e[4], "event_date": e[5], "ticket_url": e[6]} for e in test_events],
        )

    yield

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Events WHERE id LIKE 'te-%'"))


@pytest.fixture(scope="module")
def seed_seats(seed_venues):
    """Insert test seats and their aggregates linked to test venues."""
    from api.database import engine
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM SeatAggregates WHERE seat_id LIKE 'ts-%'"))
        conn.execute(text("DELETE FROM Seats WHERE id LIKE 'ts-%'"))

        test_seats = [
            ("ts-1", "tv-1", "Floor", "A", "1", 5.0),
            ("ts-2", "tv-1", "Floor", "A", "2", 6.0),
            ("ts-3", "tv-1", "Balcony", "B", "1", 25.0),
            ("ts-4", "tv-2", "Floor", "A", "1", 8.0),
        ]
        conn.execute(
            text("INSERT OR IGNORE INTO Seats (id, venue_id, section, row, seat_number, distance_to_stage) "
                 "VALUES (:id, :venue_id, :section, :row, :seat_number, :distance_to_stage)"),
            [{"id": s[0], "venue_id": s[1], "section": s[2], "row": s[3],
              "seat_number": s[4], "distance_to_stage": s[5]} for s in test_seats],
        )

        test_aggs = [
            ("ts-1", 4.5, 4.0, 3.5, 4.2, 80.0, 10),
            ("ts-2", 3.0, 3.5, 4.0, 3.4, 60.0, 5),
            ("ts-3", 2.0, 2.5, 3.0, 2.5, 40.0, 3),
        ]
        conn.execute(
            text("INSERT OR IGNORE INTO SeatAggregates "
                 "(seat_id, avg_visual, avg_sound, avg_value, avg_overall, avg_price_paid, review_count) "
                 "VALUES (:seat_id, :avg_visual, :avg_sound, :avg_value, :avg_overall, :avg_price_paid, :review_count)"),
            [{"seat_id": a[0], "avg_visual": a[1], "avg_sound": a[2], "avg_value": a[3],
              "avg_overall": a[4], "avg_price_paid": a[5], "review_count": a[6]} for a in test_aggs],
        )

    yield

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM SeatAggregates WHERE seat_id LIKE 'ts-%'"))
        conn.execute(text("DELETE FROM Seats WHERE id LIKE 'ts-%'"))


@pytest.fixture(scope="module")
def seed_reviews(seed_events, seed_seats):
    """Insert test reviews linked to test events and seats."""
    from api.database import engine
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Reviews WHERE id LIKE 'tr-%'"))

        test_reviews = [
            ("tr-1", "te-1", "ts-1", 5, 4, 3, 4, 75.0),
            ("tr-2", "te-1", "ts-2", 3, 3, 4, 3, 55.0),
            ("tr-3", "te-2", "ts-1", 4, 5, 4, 5, 90.0),
            ("tr-4", "te-3", "ts-4", 2, 2, 3, 2, 45.0),
        ]
        conn.execute(
            text("INSERT OR IGNORE INTO Reviews "
                 "(id, event_id, seat_id, rating_visual, rating_sound, rating_value, overall_rating, price_paid, created_at) "
                 "VALUES (:id, :event_id, :seat_id, :rating_visual, :rating_sound, :rating_value, :overall_rating, :price_paid, :created_at)"),
            [{"id": r[0], "event_id": r[1], "seat_id": r[2], "rating_visual": r[3],
              "rating_sound": r[4], "rating_value": r[5], "overall_rating": r[6],
              "price_paid": r[7], "created_at": "2025-01-01"} for r in test_reviews],
        )

    yield

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Reviews WHERE id LIKE 'tr-%'"))


# ---------------------------------------------------------------------------
# /search/venues
# ---------------------------------------------------------------------------

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


def test_pagination_limit():
    """Limit should control the number of returned results."""
    response = client.get("/search/venues", params={"q": "TestVenue", "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 2
    assert data["total"] >= 4


def test_pagination_offset():
    """Offset should skip the specified number of results."""
    resp_all = client.get("/search/venues", params={"q": "TestVenue", "sort_by": "name", "order": "asc"})
    resp_offset = client.get("/search/venues", params={"q": "TestVenue", "sort_by": "name", "order": "asc", "offset": 2})

    all_venues = resp_all.json()["results"]
    offset_venues = resp_offset.json()["results"]

    assert offset_venues[0]["name"] == all_venues[2]["name"]


def test_list_all_venues():
    """No filters should return all venues."""
    response = client.get("/search/venues")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 4


# ---------------------------------------------------------------------------
# /search/events
# ---------------------------------------------------------------------------

def test_search_events_by_name(seed_events):
    """Search should match event names case-insensitively."""
    response = client.get("/search/events", params={"q": "alpha"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("Alpha" in e["name"] for e in data["results"])


def test_search_events_by_artist(seed_events):
    """Search should match artist names via the q parameter."""
    response = client.get("/search/events", params={"q": "artist two"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("Two" in e["artist"] for e in data["results"])


def test_filter_events_by_venue(seed_events):
    """Filter events by venue_id should only return events for that venue."""
    response = client.get("/search/events", params={"venue_id": "tv-1"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert all(e["venue_id"] == "tv-1" for e in data["results"])


def test_filter_events_by_genre(seed_events):
    """Filter events by exact genre."""
    response = client.get("/search/events", params={"genre": "jazz"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(e["genre"] == "jazz" for e in data["results"])


def test_filter_events_by_date_range(seed_events):
    """Filter events within a date range."""
    response = client.get("/search/events", params={"date_from": "2025-07-01", "date_to": "2025-08-31"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    for e in data["results"]:
        assert "2025-07-01" <= e["event_date"] <= "2025-08-31"


def test_filter_events_date_from_only(seed_events):
    """date_from alone should filter out earlier events."""
    response = client.get("/search/events", params={"date_from": "2025-09-01"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(e["event_date"] >= "2025-09-01" for e in data["results"])


def test_sort_events_by_date_asc(seed_events):
    """Events should be sortable by event_date ascending."""
    response = client.get("/search/events", params={"q": "TestEvent", "sort_by": "event_date", "order": "asc"})
    assert response.status_code == 200
    dates = [e["event_date"] for e in response.json()["results"]]
    assert dates == sorted(dates)


def test_sort_events_by_artist_desc(seed_events):
    """Events should be sortable by artist descending."""
    response = client.get("/search/events", params={"q": "TestEvent", "sort_by": "artist", "order": "desc"})
    assert response.status_code == 200
    artists = [e["artist"] for e in response.json()["results"]]
    assert artists == sorted(artists, reverse=True)


def test_sort_events_invalid_field(seed_events):
    """Invalid sort field should return 400."""
    response = client.get("/search/events", params={"sort_by": "venue_name"})
    assert response.status_code == 400


def test_events_no_results(seed_events):
    """Search for a non-existent term should return empty results."""
    response = client.get("/search/events", params={"q": "zzz_nonexistent_zzz"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []


def test_events_pagination(seed_events):
    """Pagination should limit and offset event results correctly."""
    resp_all = client.get("/search/events", params={"q": "TestEvent", "sort_by": "name", "order": "asc"})
    resp_page = client.get("/search/events", params={"q": "TestEvent", "sort_by": "name", "order": "asc", "limit": 2, "offset": 2})

    all_events = resp_all.json()["results"]
    page_events = resp_page.json()["results"]

    assert len(page_events) <= 2
    assert page_events[0]["name"] == all_events[2]["name"]


# ---------------------------------------------------------------------------
# /search/seats
# ---------------------------------------------------------------------------

def test_seats_requires_venue_id():
    """Omitting venue_id should return 422 (missing required param)."""
    response = client.get("/search/seats")
    assert response.status_code == 422


def test_seats_by_venue(seed_seats):
    """Should return only seats belonging to the specified venue."""
    response = client.get("/search/seats", params={"venue_id": "tv-1"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert all(s["venue_id"] == "tv-1" for s in data["results"])


def test_filter_seats_by_section(seed_seats):
    """Filter by section name (case-insensitive)."""
    response = client.get("/search/seats", params={"venue_id": "tv-1", "section": "floor"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert all(s["section"] == "Floor" for s in data["results"])


def test_filter_seats_by_max_distance(seed_seats):
    """Filter seats by maximum distance to stage."""
    response = client.get("/search/seats", params={"venue_id": "tv-1", "max_distance": 10.0})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert all(s["distance_to_stage"] <= 10.0 for s in data["results"])


def test_filter_seats_by_min_rating(seed_seats):
    """Filter seats by minimum average overall rating (from SeatAggregates)."""
    response = client.get("/search/seats", params={"venue_id": "tv-1", "min_rating": 4.0})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all((s["avg_overall"] or 0) >= 4.0 for s in data["results"])


def test_sort_seats_by_distance_asc(seed_seats):
    """Sort seats by distance_to_stage ascending."""
    response = client.get("/search/seats", params={"venue_id": "tv-1", "sort_by": "distance_to_stage", "order": "asc"})
    assert response.status_code == 200
    distances = [s["distance_to_stage"] for s in response.json()["results"]]
    assert distances == sorted(distances)


def test_sort_seats_by_avg_overall_desc(seed_seats):
    """Sort seats by avg_overall descending (NULL seats last)."""
    response = client.get("/search/seats", params={"venue_id": "tv-1", "sort_by": "avg_overall", "order": "desc"})
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_sort_seats_invalid_field(seed_seats):
    """Invalid sort field should return 400."""
    response = client.get("/search/seats", params={"venue_id": "tv-1", "sort_by": "row"})
    assert response.status_code == 400


def test_seats_pagination(seed_seats):
    """Pagination should limit and offset seat results correctly."""
    resp_all = client.get("/search/seats", params={"venue_id": "tv-1", "sort_by": "distance_to_stage", "order": "asc"})
    resp_page = client.get("/search/seats", params={"venue_id": "tv-1", "sort_by": "distance_to_stage", "order": "asc", "limit": 1, "offset": 1})

    all_seats = resp_all.json()["results"]
    page_seats = resp_page.json()["results"]

    assert len(page_seats) <= 1
    assert page_seats[0]["id"] == all_seats[1]["id"]


# ---------------------------------------------------------------------------
# /search/reviews
# ---------------------------------------------------------------------------

def test_list_all_reviews(seed_reviews):
    """No filters should return reviews (at least the seeded ones)."""
    response = client.get("/search/reviews")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 4


def test_filter_reviews_by_seat(seed_reviews):
    """Filter reviews by seat_id."""
    response = client.get("/search/reviews", params={"seat_id": "ts-1"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert all(r["seat_id"] == "ts-1" for r in data["results"])


def test_filter_reviews_by_event(seed_reviews):
    """Filter reviews by event_id."""
    response = client.get("/search/reviews", params={"event_id": "te-1"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert all(r["event_id"] == "te-1" for r in data["results"])


def test_filter_reviews_by_min_rating(seed_reviews):
    """Filter reviews with overall_rating >= threshold."""
    response = client.get("/search/reviews", params={"min_rating": 4})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert all(r["overall_rating"] >= 4 for r in data["results"])


def test_sort_reviews_by_rating_asc(seed_reviews):
    """Sort reviews by overall_rating ascending."""
    response = client.get("/search/reviews", params={"sort_by": "overall_rating", "order": "asc"})
    assert response.status_code == 200
    ratings = [r["overall_rating"] for r in response.json()["results"]]
    assert ratings == sorted(ratings)


def test_sort_reviews_by_price_desc(seed_reviews):
    """Sort reviews by price_paid descending."""
    response = client.get("/search/reviews", params={"sort_by": "price_paid", "order": "desc"})
    assert response.status_code == 200
    prices = [r["price_paid"] for r in response.json()["results"]]
    assert prices == sorted(prices, reverse=True)


def test_sort_reviews_invalid_field(seed_reviews):
    """Invalid sort field should return 400."""
    response = client.get("/search/reviews", params={"sort_by": "user_id"})
    assert response.status_code == 400


def test_reviews_no_results(seed_reviews):
    """Filter with impossible min_rating should return empty results."""
    response = client.get("/search/reviews", params={"min_rating": 5, "seat_id": "ts-2"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []


def test_reviews_pagination(seed_reviews):
    """Pagination should limit and offset review results correctly."""
    resp_all = client.get("/search/reviews", params={"sort_by": "overall_rating", "order": "asc"})
    resp_page = client.get("/search/reviews", params={"sort_by": "overall_rating", "order": "asc", "limit": 2, "offset": 2})

    all_reviews = resp_all.json()["results"]
    page_reviews = resp_page.json()["results"]

    assert len(page_reviews) <= 2
    assert page_reviews[0]["overall_rating"] == all_reviews[2]["overall_rating"]
