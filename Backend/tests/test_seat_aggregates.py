import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from datetime import timedelta
from api.main import app
from api.auth_utils import get_password_hash, create_access_token
from api.database import engine

client = TestClient(app)

@pytest.fixture
def test_user():
    user_id = "00000000-0000-0000-0000-000000000001"
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Users WHERE id = :id"), {"id": user_id})
        conn.execute(
            text("INSERT INTO Users (id, email, password_hash) VALUES (:id, :e, :p)"),
            {"id": user_id, "e": "aggtest@test.com", "p": get_password_hash("password")},
        )
    token = create_access_token({"sub": user_id}, expires_delta=timedelta(hours=1))
    yield {"user_id": user_id, "token": token}
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Users WHERE id = :id"), {"id": user_id})

@pytest.fixture
def test_venue_event():
    v_id = "00000000-0000-0000-0000-000000000002"
    e_id = "00000000-0000-0000-0000-000000000003"
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM Events WHERE id = :id"), {"id": e_id})
        conn.execute(text("DELETE FROM Venues WHERE id = :id"), {"id": v_id})
        conn.execute(
            text("INSERT INTO Venues (id, name, city) VALUES (:id, :n, :c)"),
            {"id": v_id, "n": "AggTestVenue", "c": "TestCity"},
        )
        conn.execute(
            text("INSERT INTO Events (id, venue_id, name) VALUES (:id, :v, :n)"),
            {"id": e_id, "v": v_id, "n": "AggTestEvent"},
        )
    yield {"venue_id": v_id, "event_id": e_id}
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM SeatAggregates WHERE seat_id IN (SELECT id FROM Seats WHERE venue_id = :id)"), {"id": v_id})
        conn.execute(text("DELETE FROM Reviews WHERE venue_id = :id"), {"id": v_id})
        conn.execute(text("DELETE FROM Seats WHERE venue_id = :id"), {"id": v_id})
        conn.execute(text("DELETE FROM Events WHERE id = :id"), {"id": e_id})
        conn.execute(text("DELETE FROM Venues WHERE id = :id"), {"id": v_id})

def test_seat_aggregates_update(test_user, test_venue_event):
    # 1. First review
    resp1 = client.post(
        "/reviews/",
        json={
            "event_id": test_venue_event["event_id"],
            "venue_id": test_venue_event["venue_id"],
            "section": "AggSec",
            "row": "1",
            "seat_number": "1",
            "rating_visual": 5,
            "rating_sound": 3,
            "rating_value": 4,
            "price_paid": 100.0,
            "text": "Review 1",
        },
        headers={"Authorization": f"Bearer {test_user['token']}"},
    )
    assert resp1.status_code == 200
    
    # Check SeatAggregates
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT sa.avg_visual, sa.avg_sound, sa.avg_value, sa.avg_overall, sa.avg_price_paid, sa.review_count
            FROM SeatAggregates sa
            JOIN Seats s ON s.id = sa.seat_id
            WHERE s.venue_id = :v_id AND s.section = 'AggSec' AND s.row = '1' AND s.seat_number = '1'
        """), {"v_id": test_venue_event["venue_id"]}).fetchone()
        
        assert row is not None
        assert row.review_count == 1
        assert float(row.avg_visual) == 5.0
        assert float(row.avg_sound) == 3.0
        assert float(row.avg_value) == 4.0
        # overall = round((5+3+4)/3) = 4
        assert float(row.avg_overall) == 4.0
        assert float(row.avg_price_paid) == 100.0

    # 2. Second review
    resp2 = client.post(
        "/reviews/",
        json={
            "event_id": test_venue_event["event_id"],
            "venue_id": test_venue_event["venue_id"],
            "section": "AggSec",
            "row": "1",
            "seat_number": "1",
            "rating_visual": 1,
            "rating_sound": 1,
            "rating_value": 1,
            "price_paid": 50.0,
            "text": "Review 2",
        },
        headers={"Authorization": f"Bearer {test_user['token']}"},
    )
    assert resp2.status_code == 200
    
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT sa.avg_visual, sa.avg_sound, sa.avg_value, sa.avg_overall, sa.avg_price_paid, sa.review_count
            FROM SeatAggregates sa
            JOIN Seats s ON s.id = sa.seat_id
            WHERE s.venue_id = :v_id AND s.section = 'AggSec' AND s.row = '1' AND s.seat_number = '1'
        """), {"v_id": test_venue_event["venue_id"]}).fetchone()
        
        assert row.review_count == 2
        # (5 + 1) / 2 = 3.0
        assert float(row.avg_visual) == 3.0
        # (3 + 1) / 2 = 2.0
        assert float(row.avg_sound) == 2.0
        # (4 + 1) / 2 = 2.5
        assert float(row.avg_value) == 2.5
        # overall1 = 4. overall2 = round((1+1+1)/3) = 1. (4 + 1) / 2 = 2.5
        assert float(row.avg_overall) == 2.5
        # (100 + 50) / 2 = 75.0
        assert float(row.avg_price_paid) == 75.0
