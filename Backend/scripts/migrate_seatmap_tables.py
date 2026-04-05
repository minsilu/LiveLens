"""
One-time migration: create SeatmapCache and SeatmapPinCache tables in production PostgreSQL.
Run once:
    cd Backend
    python -m scripts.migrate_seatmap_tables
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS SeatmapCache (
        id              TEXT PRIMARY KEY,
        tm_venue_id     TEXT,
        png_url         TEXT,
        section_coords  TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
print("SeatmapCache: OK")

cur.execute("""
    CREATE TABLE IF NOT EXISTS SeatmapPinCache (
        id          TEXT PRIMARY KEY,
        venue_key   TEXT,
        section     TEXT,
        s3_url      TEXT NOT NULL,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
print("SeatmapPinCache: OK")

cur.close()
conn.close()
print("Migration complete.")
