import bcrypt
import jwt
import os
from datetime import datetime, timedelta

# Secret key for JWT signing. In production, this should be a secure environment variable.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-change-in-prod-1234")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days valid access token

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the hashed version in DB."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Hashes a password using bcrypt before storing it."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a JWT token containing the user's data (like user_id)."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
