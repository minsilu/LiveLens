import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def test_upsert():
    engine = create_engine("sqlite:///./dev.db")
    with engine.begin() as conn:
        try:
            # Try to run the query
            upsert_seat_query = text("""
                INSERT INTO Seats (id, venue_id, section, row, seat_number)
                VALUES (:id, :v_id, :sec, :row, :num)
                ON CONFLICT (venue_id, section, row, seat_number) 
                DO UPDATE SET section = EXCLUDED.section 
                RETURNING id;
            """)
            
            res = conn.execute(upsert_seat_query, {
                "id": "test-id",
                "v_id": "test-venue", 
                "sec": "101",
                "row": "A",
                "num": "1"
            }).scalar()
            print("Success:", res)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    test_upsert()
