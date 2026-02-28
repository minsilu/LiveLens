import os
from sqlalchemy import create_engine

# AWS App Runner injects DATABASE_URL from our backend_stack deployment
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = None
