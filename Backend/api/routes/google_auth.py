import os
import secrets
import string
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text
from google.oauth2 import id_token
from google.auth.transport import requests

from ..database import engine
from ..auth_utils import get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

class GoogleAuthRequest(BaseModel):
    token: str

@router.post("/google")
def google_auth(request: GoogleAuthRequest):
    """Authenticates a user via Google ID Token, returning a JWT token."""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        # Verify the Google token
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        if not client_id:
            raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured in server environment")
        try:
            idinfo = id_token.verify_oauth2_token(request.token, requests.Request(), client_id, clock_skew_in_seconds=10)
        except ValueError as e:
            # Invalid token
            raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
            
        email = idinfo.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google token")
            
        with engine.begin() as conn:
            # Check if user exists
            row = conn.execute(text("SELECT id FROM Users WHERE email = :email"), {"email": email}).fetchone()
            
            if row:
                user_id = row[0]
                # Update last_login
                conn.execute(text("UPDATE Users SET last_login = :now WHERE id = :id"), {"now": datetime.utcnow(), "id": user_id})
                message = "Login successful"
            else:
                # Create new user
                user_id = str(uuid.uuid4())
                # Generate strong random password
                alphabet = string.ascii_letters + string.digits + string.punctuation
                random_password = ''.join(secrets.choice(alphabet) for i in range(32))
                hashed_pwd = get_password_hash(random_password)
                
                conn.execute(text("""
                    INSERT INTO Users (id, email, password_hash, is_incognito, created_at, last_login)
                    VALUES (:id, :email, :password_hash, :is_incognito, :created_at, :last_login)
                """), {
                    "id": user_id,
                    "email": email,
                    "password_hash": hashed_pwd,
                    "is_incognito": False,
                    "created_at": datetime.utcnow(),
                    "last_login": datetime.utcnow()
                })
                message = "User registered successfully via Google"
                
            # Create token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user_id)}, expires_delta=access_token_expires
            )
            
            return {
                "access_token": access_token, 
                "token_type": "bearer",
                "message": message
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
