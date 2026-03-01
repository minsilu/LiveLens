from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from ..database import engine
import uuid
import random
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/generate")
def generate_mock_data():
    """Inject ~1000 interrelated mock database records (Users, Venues, Events, Seats, Reviews)"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.begin() as conn: # Starts a transaction
            # 1. Venues (4 venues + Scotiabank)
            # You can place real map images in Backend/static/maps/ with these exact filenames
            venues_data = [
                {"id": str(uuid.uuid4()), "name": "Scotiabank Arena", "city": "Toronto", "capacity": 19800, "tags": '["sports", "concerts"]', "seat_map_2d_url": "http://127.0.0.1:8000/static/maps/scotiabank_arena_map.jpg"},
                {"id": str(uuid.uuid4()), "name": "Madison Square Garden", "city": "New York", "capacity": 19500, "tags": '["sports", "concerts"]', "seat_map_2d_url": "http://127.0.0.1:8000/static/maps/msg_map.jpg"},
                {"id": str(uuid.uuid4()), "name": "Staples Center", "city": "Los Angeles", "capacity": 20000, "tags": '["basketball", "music"]', "seat_map_2d_url": "http://127.0.0.1:8000/static/maps/staples_center_map.jpg"},
                {"id": str(uuid.uuid4()), "name": "The O2", "city": "London", "capacity": 20000, "tags": '["arena", "historic"]', "seat_map_2d_url": "http://127.0.0.1:8000/static/maps/the_o2_map.jpg"}
            ]
            conn.execute(text("INSERT INTO Venues (id, name, city, capacity, tags, seat_map_2d_url) VALUES (:id, :name, :city, :capacity, :tags, :seat_map_2d_url) ON CONFLICT DO NOTHING"), venues_data)
            
            res_venues = conn.execute(text("SELECT id, name FROM Venues")).fetchall()
            venue_dict = {row[1]: str(row[0]) for row in res_venues}
            scotia_id = venue_dict.get("Scotiabank Arena")

            # 2. Users (150 users)
            users_data = []
            for i in range(150):
                users_data.append({
                    "id": str(uuid.uuid4()), 
                    "email": f"mockuser{i}_{random.randint(1000,9999)}@example.com", 
                    "password_hash": "mockedhash", 
                    "is_incognito": random.choice([True, False]),
                    "created_at": datetime.now(),
                    "last_login": datetime.now()
                })
            conn.execute(text("INSERT INTO Users (id, email, password_hash, is_incognito, created_at, last_login) VALUES (:id, :email, :password_hash, :is_incognito, :created_at, :last_login) ON CONFLICT DO NOTHING"), users_data)
            res_users = conn.execute(text("SELECT id FROM Users LIMIT 150")).fetchall()
            user_ids = [str(r[0]) for r in res_users]
            
            # 3. Events (5 Events per venue)
            event_names = ["Taylor Swift: The Eras Tour", "Drake: It's All A Blur", "The Weeknd: After Hours", "Hans Zimmer Live", "Coldplay: Spheres"]
            events_data = []
            for v_name, v_id in venue_dict.items():
                for e_name in event_names:
                    events_data.append({
                        "id": str(uuid.uuid4()),
                        "venue_id": v_id,
                        "name": f"{e_name} at {v_name}",
                        "artist": e_name.split(":")[0],
                        "genre": "Pop/Hip-Hop/Classical",
                        "event_date": (datetime.now() + timedelta(days=random.randint(1, 90))).date(),
                        "ticket_url": "https://ticketmaster.com"
                    })
            conn.execute(text("INSERT INTO Events (id, venue_id, name, artist, genre, event_date, ticket_url) VALUES (:id, :venue_id, :name, :artist, :genre, :event_date, :ticket_url) ON CONFLICT DO NOTHING"), events_data)
            res_events = conn.execute(text("SELECT id, venue_id FROM Events")).fetchall()
            events_by_venue = {str(v_id): [] for v_id in venue_dict.values()}
            for e_id, v_id in res_events:
                events_by_venue[str(v_id)].append(str(e_id))

            # 4. Seats (Scotiabank: Sec 1-6, Other: Random)
            seats_data = []
            for sec in range(1, 7): # Section 1 to 6
                for row in range(1, 16): # Rows A-O
                    for seat_num in range(1, 21): # Seat 1-20
                        dist = sec * 15.0 + random.uniform(-2, 2)
                        seats_data.append({
                            "id": str(uuid.uuid4()), "venue_id": scotia_id, "section": str(sec), 
                            "row": chr(64 + row), "seat_number": str(seat_num), "distance_to_stage": dist
                        })
            
            for v_name, v_id in venue_dict.items():
                if v_id == scotia_id: continue
                # 100 generic seats for other arenas
                for i in range(100):
                    seats_data.append({
                        "id": str(uuid.uuid4()), "venue_id": v_id, "section": "100", 
                        "row": "A", "seat_number": str(i), "distance_to_stage": 50.0
                    })
            conn.execute(text("INSERT INTO Seats (id, venue_id, section, row, seat_number, distance_to_stage) VALUES (:id, :venue_id, :section, :row, :seat_number, :distance_to_stage) ON CONFLICT DO NOTHING"), seats_data)
            
            res_seats = conn.execute(text("SELECT id, venue_id, section FROM Seats")).fetchall()
            seats_by_venue = {str(v_id): [] for v_id in venue_dict.values()}
            for s_id, v_id, sec in res_seats:
                seats_by_venue[str(v_id)].append((str(s_id), str(sec)))

            # 5. Reviews (~1000 total, ~350 for scotiabank, rest divided)
            reviews_data = []
            def build_reviews(v_id, count):
                v_events = events_by_venue.get(v_id, [])
                v_seats = seats_by_venue.get(v_id, [])
                if not v_events or not v_seats or not user_ids: return

                for _ in range(count):
                    evt = random.choice(v_events)
                    user = random.choice(user_ids)
                    seat, sec = random.choice(v_seats)
                    
                    sec_int = int(sec) if sec.isdigit() else 3
                    base_rating = max(1, 6 - sec_int) # sec 1 -> 5, sec 6 -> 1
                    
                    v_rating = min(5, max(1, base_rating + random.randint(-1, 1)))
                    s_rating = min(5, max(1, base_rating + random.randint(-1, 1)))
                    val_rating = min(5, max(1, random.randint(3, 5)))
                    overall = int(round((v_rating + s_rating + val_rating) / 3.0))
                    
                    text_content = f"Great view from section {sec}! The sound was amazing." if overall >= 4 else f"Okay view from section {sec}, but could be better."
                    
                    # 15% chance to have a mock image attached
                    mock_images = '[]'
                    if random.random() < 0.15:
                        mock_images = f'["http://127.0.0.1:8000/static/images/mock_concert_{random.randint(1,5)}.jpg"]'
                    
                    reviews_data.append({
                        "id": str(uuid.uuid4()), "user_id": user, "event_id": evt, "seat_id": seat,
                        "rating_visual": v_rating, "rating_sound": s_rating, "rating_value": val_rating, "overall_rating": overall,
                        "price_paid": round(random.uniform(50.0, 500.0), 2), "text": text_content, "images": mock_images,
                        "created_at": datetime.now() - timedelta(days=random.randint(0, 365))
                    })
            
            # Allocate 350 reviews roughly to Scotiabank
            build_reviews(scotia_id, 350)
            other_ids = [v for v in venue_dict.values() if v != scotia_id]
            for ov in other_ids:
                build_reviews(ov, 650 // len(other_ids))
            
            conn.execute(text("""
                INSERT INTO Reviews (id, user_id, event_id, seat_id, rating_visual, rating_sound, rating_value, overall_rating, price_paid, text, images, created_at) 
                VALUES (:id, :user_id, :event_id, :seat_id, :rating_visual, :rating_sound, :rating_value, :overall_rating, :price_paid, :text, :images, :created_at) 
                ON CONFLICT DO NOTHING
            """), reviews_data)
            
        return {"message": f"Successfully injected {len(reviews_data)} reviews across {len(venues_data)} venues!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reviews")
def get_mocked_reviews(limit: int = 20, venue_name: str = "Scotiabank Arena"):
    """Fetch recent mocked reviews joined with Venues, Events, and Seats."""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    r.overall_rating, 
                    r.text,
                    r.images,
                    s.section, 
                    s.row, 
                    s.seat_number, 
                    e.name AS event_name, 
                    v.name AS venue_name
                FROM Reviews r
                JOIN Seats s ON r.seat_id = s.id
                JOIN Events e ON r.event_id = e.id
                JOIN Venues v ON e.venue_id = v.id
                WHERE v.name = :venue
                ORDER BY r.created_at DESC
                LIMIT :limit
            """)
            result = conn.execute(query, {"venue": venue_name, "limit": limit})
            data = [
                {
                    "overall_rating": row[0],
                    "text": row[1],
                    "images": row[2],
                    "section": row[3],
                    "row": row[4],
                    "seat_number": row[5],
                    "event": row[6],
                    "venue": row[7]
                }
                for row in result
            ]
            
            count_res = conn.execute(text("SELECT COUNT(*) FROM Reviews r JOIN Seats s ON r.seat_id = s.id JOIN Venues v ON s.venue_id = v.id WHERE v.name = :venue"), {"venue": venue_name}).scalar()
            
            return {
                "message": f"Showing {len(data)} latest reviews out of {count_res} total in {venue_name}",
                "reviews": data
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tables")
def list_tables():
    """Verify that the database tables were created successfully by listing them."""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        from sqlalchemy import inspect
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SQLRequest(BaseModel):
    query: str

@router.post("/sql")
def execute_raw_sql(request: SQLRequest):
    """
    ⚠️ WARNING: DEVELOPMENT ONLY.
    Executes raw SQL queries against the database and returns the results.
    Useful for checking table counts, debugging, or fixing data directly from Swagger.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.begin() as conn:
            # We use text() to safely wrap the raw sql string
            result = conn.execute(text(request.query))
            
            # If it's a SELECT query, return the rows
            if result.returns_rows:
                data = [dict(row._mapping) for row in result]
                return {
                    "count": len(data),
                    "results": data
                }
            # If it's an UPDATE/INSERT/DELETE, return the affected row count
            else:
                return {
                    "rows_affected": result.rowcount, 
                    "message": "Query executed successfully"
                }
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL Execution Error: {str(e)}")
