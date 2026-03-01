from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

app = FastAPI(
    title="LiveLens API",
    description="Backend API for LiveLens, servicing the mobile and web application. Uses PostgreSQL via SQLAlchemy.",
    version="1.0.0"
)

# Mount local static files for development (Images, Maps)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # TODO: change to specific origins
    allow_credentials=True,
    allow_methods=["*"], # TODO: change to specific methods
    allow_headers=["*"], # TODO: change to specific headers
)

@app.get("/")
def read_root():
    return {"message": "Welcome to LiveLens API!"}

@app.get("/health")
def health_check():
    from .database import engine
    db_status = "Connected" if engine else "Not Configured"
    return {
        "status": "healthy",
        "database": db_status
    }

from .routes import mock, auth, uploads, reviews
# TODO: Add more routers here
app.include_router(mock.router, prefix="/dev", tags=["dev"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(uploads.router, prefix="/upload", tags=["upload"])
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
