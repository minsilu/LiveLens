from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from ..database import engine
from ..auth_utils import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
import uuid
from datetime import datetime, timedelta

router = APIRouter()

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    is_incognito: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(user: UserRegister):
    """Registers a new user and returns a JWT token."""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.begin() as conn: # Engine.begin() guarantees an atomic transaction
            # Check if user exists
            existing_user = conn.execute(text("SELECT id FROM Users WHERE email = :email"), {"email": user.email}).fetchone()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Hash password and insert
            user_id = str(uuid.uuid4())
            hashed_pwd = get_password_hash(user.password)
            
            conn.execute(text("""
                INSERT INTO Users (id, email, password_hash, is_incognito, created_at)
                VALUES (:id, :email, :password_hash, :is_incognito, :created_at)
            """), {
                "id": user_id,
                "email": user.email,
                "password_hash": hashed_pwd,
                "is_incognito": user.is_incognito,
                "created_at": datetime.utcnow()
            })
            
            # Create a token for immediate login upon successful registration
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user_id}, expires_delta=access_token_expires
            )
            
            return {
                "message": "User registered successfully", 
                "access_token": access_token, 
                "token_type": "bearer"
            }
    except HTTPException:
        raise # Rethrow FastAPI HTTPExceptions normally
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(user: UserLogin):
    """Authenticates a user and returns a fresh JWT token."""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.begin() as conn:
            # Find user
            row = conn.execute(text("SELECT id, password_hash FROM Users WHERE email = :email"), {"email": user.email}).fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
            user_id, hashed_pwd = row
            
            # Verify password mathematically using bcrypt
            if not verify_password(user.password, hashed_pwd):
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
            # Update last_login timestamp
            conn.execute(text("UPDATE Users SET last_login = :now WHERE id = :id"), {"now": datetime.utcnow(), "id": user_id})
            
            # Create token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user_id)}, expires_delta=access_token_expires
            )
            
            return {
                "access_token": access_token, 
                "token_type": "bearer",
                "message": "Login successful"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
