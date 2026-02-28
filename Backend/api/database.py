import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load local .env file if it exists, otherwise rely on App Runner env vars
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(DATABASE_URL)
else:
    engine = None
