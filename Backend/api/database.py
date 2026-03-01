import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load local .env file if it exists, otherwise rely on App Runner env vars
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        
        # Auto-initialize local SQLite database tables so developers don't have to
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS Users (
                  id                TEXT PRIMARY KEY,
                  email             TEXT UNIQUE NOT NULL,
                  password_hash     TEXT NOT NULL,
                  is_incognito      BOOLEAN DEFAULT 0,
                  created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_login        TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS Venues (
                  id                TEXT PRIMARY KEY,
                  name              TEXT NOT NULL,
                  city              TEXT,
                  capacity          INTEGER,
                  tags              TEXT
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS Events (
                  id                TEXT PRIMARY KEY,
                  venue_id          TEXT REFERENCES Venues(id),
                  name              TEXT,
                  artist            TEXT,
                  genre             TEXT,
                  event_date        DATE,
                  ticket_url        TEXT
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS Seats (
                  id                   TEXT PRIMARY KEY,
                  venue_id             TEXT REFERENCES Venues(id),
                  section              TEXT,
                  row                  TEXT,
                  seat_number          TEXT,
                  distance_to_stage    FLOAT
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS Reviews (
                  id                TEXT PRIMARY KEY,
                  user_id           TEXT REFERENCES Users(id),
                  event_id          TEXT REFERENCES Events(id),
                  seat_id           TEXT REFERENCES Seats(id),
                  rating_visual     INTEGER,
                  rating_sound      INTEGER,
                  rating_value      INTEGER,
                  overall_rating    INTEGER,
                  price_paid        FLOAT,
                  text              TEXT,
                  images            TEXT,
                  created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS SeatAggregates (
                  seat_id           TEXT PRIMARY KEY REFERENCES Seats(id),
                  avg_visual        FLOAT,
                  avg_sound         FLOAT,
                  avg_value         FLOAT,
                  avg_overall       FLOAT,
                  avg_price_paid    FLOAT,
                  review_count      INTEGER,
                  last_updated      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS AI_Predictions (
                  seat_id              TEXT PRIMARY KEY REFERENCES Seats(id),
                  predicted_visual     FLOAT,
                  predicted_sound      FLOAT,
                  predicted_value      FLOAT,
                  predicted_overall    FLOAT,
                  predicted_price      FLOAT,
                  confidence           FLOAT,
                  explanation          TEXT
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS SimilarSeats (
                  seat_id             TEXT REFERENCES Seats(id),
                  similar_seat_id     TEXT REFERENCES Seats(id),
                  similarity_score    FLOAT,
                  PRIMARY KEY (seat_id, similar_seat_id)
                );
            """))
            
    else:
        engine = create_engine(DATABASE_URL)
else:
    engine = None
