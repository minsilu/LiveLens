import os
import jwt
import uuid
import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import text

from ..database import engine
from ..auth_utils import SECRET_KEY, ALGORITHM

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Decodes the JWT to extract user_id.
    Implemented locally in reviews.py to avoid altering legacy auth_utils.py module.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token scope: no user ID found")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

class ReviewCreate(BaseModel):
    event_id: str
    seat_id: str
    rating_visual: int
    rating_sound: int
    rating_value: int
    price_paid: float
    text: str
    images: List[str] = [] # The URLs we generated earlier via /upload/presigned-url or local

@router.post("/")
def create_review(review: ReviewCreate, user_id: str = Depends(get_current_user)):
    """
    Submit a final review containing ratings, text, and S3 image URLs.
    Validates JWT token to attach the review to the calling user.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    overall_rating = int(round((review.rating_visual + review.rating_sound + review.rating_value) / 3.0))
    review_id = str(uuid.uuid4())
    images_json = json.dumps(review.images)
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO Reviews (
                    id, user_id, event_id, seat_id,
                    rating_visual, rating_sound, rating_value, overall_rating,
                    price_paid, text, images, created_at
                ) VALUES (
                    :id, :user_id, :event_id, :seat_id,
                    :r_vis, :r_snd, :r_val, :r_over,
                    :price, :text, :images, :created_at
                )
            """), {
                "id": review_id,
                "user_id": user_id,
                "event_id": review.event_id,
                "seat_id": review.seat_id,
                "r_vis": review.rating_visual,
                "r_snd": review.rating_sound,
                "r_val": review.rating_value,
                "r_over": overall_rating,
                "price": review.price_paid,
                "text": review.text,
                "images": images_json,
                "created_at": datetime.utcnow()
            })
            
            return {"message": "Review submitted successfully", "review_id": review_id, "overall_rating": overall_rating}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {str(e)}")
