from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from ..database import engine
from ..auth_utils import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
import jwt
import json
import uuid
from datetime import datetime, timedelta

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Decodes the JWT to extract user_id."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

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

@router.get("/me")
def get_profile(user_id: str = Depends(get_current_user)):
    """Returns the authenticated user's profile, stats, and reviews."""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        with engine.begin() as conn:
            # 1. Fetch user info
            user_row = conn.execute(text(
                "SELECT email, is_incognito, created_at, last_login FROM Users WHERE id = :id"
            ), {"id": user_id}).fetchone()
            
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            email, is_incognito, created_at, last_login = user_row
            
            # 2. Fetch user's reviews with venue names
            reviews_rows = conn.execute(text("""
                SELECT r.id, r.venue_id, v.name as venue_name, r.event_id,
                       r.rating_visual, r.rating_sound, r.rating_value, r.overall_rating,
                       r.price_paid, r.text, r.images, r.tags, r.created_at,
                       s.section, s.row, s.seat_number
                FROM Reviews r
                LEFT JOIN Venues v ON r.venue_id = v.id
                LEFT JOIN Seats s ON r.seat_id = s.id
                WHERE r.user_id = :user_id
                ORDER BY r.created_at DESC
            """), {"user_id": user_id}).fetchall()
            
            reviews = []
            venue_count = {}
            total_rating = 0
            
            def _parse_json(val):
                if val is None:
                    return []
                if isinstance(val, (list, dict)):
                    return val
                try:
                    return json.loads(val)
                except Exception:
                    return []
            
            for row in reviews_rows:
                rid, venue_id, venue_name, event_id, rv, rs, rval, ro, pp, txt, imgs, tags, cat, sec, rw, sn = row
                reviews.append({
                    "id": rid,
                    "venue_id": venue_id,
                    "venue_name": venue_name or "Unknown Venue",
                    "event_id": event_id,
                    "rating_visual": rv,
                    "rating_sound": rs,
                    "rating_value": rval,
                    "overall_rating": ro,
                    "price_paid": pp,
                    "text": txt,
                    "images": _parse_json(imgs),
                    "tags": _parse_json(tags),
                    "created_at": str(cat) if cat else None,
                    "section": sec,
                    "row": rw,
                    "seat_number": sn,
                })
                total_rating += (ro or 0)
                vn = venue_name or "Unknown"
                venue_count[vn] = venue_count.get(vn, 0) + 1
            
            total_reviews = len(reviews)
            avg_rating = round(total_rating / total_reviews, 1) if total_reviews > 0 else 0
            top_venue = max(venue_count, key=venue_count.get) if venue_count else None
            
            return {
                "user": {
                    "id": user_id,
                    "email": email,
                    "is_incognito": bool(is_incognito),
                    "created_at": str(created_at) if created_at else None,
                    "last_login": str(last_login) if last_login else None,
                },
                "stats": {
                    "total_reviews": total_reviews,
                    "avg_rating": avg_rating,
                    "top_venue": top_venue,
                },
                "reviews": reviews,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
