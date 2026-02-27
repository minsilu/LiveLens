from fastapi import FastAPI
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

app = FastAPI(
    title="LiveLens API",
    description="The backend API for the LiveLens application.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to LiveLens API!"}

@app.get("/health")
def health_check():
    # Attempt to read database URL just to verify env var presence (optional)
    db_url = os.getenv("DATABASE_URL")
    db_status = "Connected (simulated)" if db_url else "No DATABASE_URL configured"
    
    return {
        "status": "healthy",
        "database": db_status
    }

# --- Database Connection Setup for Runtime ---
from sqlalchemy import create_engine, text
from fastapi import HTTPException
import uuid

# AWS App Runner injects DATABASE_URL from our backend_stack deployment
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = None

@app.get("/dev/tables")
def list_tables():
    """Verify that the database tables were created successfully by listing them."""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]
            return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dev/mock-venues")
def mock_venues():
    """Inject 3 mock venues into the database for testing purposes."""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.connect() as conn:
            # Generate UUIDs for 3 venues
            v1_id = str(uuid.uuid4())
            v2_id = str(uuid.uuid4())
            v3_id = str(uuid.uuid4())
            
            # Simple SQL execution to insert mock venues
            insert_query = text("""
                INSERT INTO Venues (id, name, city, capacity, tags)
                VALUES 
                (:v1, 'Madison Square Garden', 'New York', 19500, '["sports", "concerts"]'),
                (:v2, 'Staples Center', 'Los Angeles', 20000, '["basketball", "music"]'),
                (:v3, 'The O2', 'London', 20000, '["arena", "historic"]')
                ON CONFLICT (id) DO NOTHING;
            """)
            
            conn.execute(insert_query, {"v1": v1_id, "v2": v2_id, "v3": v3_id})
            conn.commit()
            
            return {
                "message": "Successfully mocked 3 venues!",
                "venues_inserted": [
                    {"id": v1_id, "name": "Madison Square Garden"},
                    {"id": v2_id, "name": "Staples Center"},
                    {"id": v3_id, "name": "The O2"}
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

