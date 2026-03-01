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

from .routes import mock, auth, search

app.include_router(mock.router, prefix="/dev", tags=["dev"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(search.router, prefix="/search", tags=["search"])
