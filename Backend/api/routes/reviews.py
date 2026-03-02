import os
import jwt
import uuid
import json
import boto3
from datetime import datetime
from typing import List, Optional
from botocore.exceptions import NoCredentialsError, ClientError
from botocore.config import Config

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import text

from ..database import engine
from ..auth_utils import SECRET_KEY, ALGORITHM

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "livelens-images")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

s3_client = boto3.client(
    's3', 
    region_name=AWS_REGION,
    config=Config(
        s3={'addressing_style': 'virtual'},
        signature_version='s3v4'
    )
)

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
    venue_id: str
    section: str
    row: str
    seat_number: str
    rating_visual: int
    rating_sound: int
    rating_value: int
    price_paid: float
    text: str
    images: Optional[List[str]] = None # Can be omitted during initial POST

class ReviewImagesUpdate(BaseModel):
    images: List[str]

@router.post("/")
def create_review(review: ReviewCreate, user_id: str = Depends(get_current_user)):
    """
    :param review: ReviewCreate object containing event details, seat info, and image URLs.
    Submits a comprehensive event review, links it to a seat, and calculates ratings.
    value needed from frontend:
    auth_token: pls include 'Authorization': `Bearer ${storedToken}`in the header, this is mandatory
    {
        "event_id": "594671b6-da30-41f3-ab14-447e1268a49e", #pls use the event id from the event page
        "venue_id": "36a7f0e4-7d37-46d9-89bd-55dae360a871", #pls use the venue id from the event page
        "section": "General Admission",
        "row": "Front",
        "seat_number": "101",
        "rating_visual": 3,
        "rating_sound": 5,
        "rating_value": 4,
        "price_paid": 299.99,
        "text": "The atmosphere was electric! Postman test is working!",
        "images": ["https://test.com/img_1.jpg", "https://test.com/img_2.jpg"] # (optional) if there are images, pls run presigned url first
    }

    ### Frontend Workflow Instructions:
    - **IF THE REVIEW HAS IMAGES**:
        1. The frontend must FIRST call the `/presigned url` API for each image.
        2. Upload the files directly to S3 using the provided instructions.
        3. Collect the resulting `future_url` strings into a list.
        4. Pass this list into the `images` field of THIS API.
    - **IF NO IMAGES**: Simply leave the `images` field empty or null.
    
    :param user_id: Automatically injected from JWT token.
    :return: A success message, the new review_id, and the calculated overall_rating.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    overall_rating = int(round((review.rating_visual + review.rating_sound + review.rating_value) / 3.0))
    review_id = str(uuid.uuid4())
    images_json = json.dumps(review.images) if review.images else None
    
    try:
        with engine.begin() as conn:
            # 1. Validate User
            user_exists = conn.execute(text("SELECT 1 FROM Users WHERE id = :user_id"), {"user_id": user_id}).scalar()
            if not user_exists:
                raise HTTPException(status_code=400, detail="Invalid user_id: User does not exist.")
                
            # 2. Validate Venue & Event
            venue_exists = conn.execute(text("SELECT 1 FROM Venues WHERE id = :venue_id"), {"venue_id": review.venue_id}).scalar()
            if not venue_exists:
                raise HTTPException(status_code=400, detail="Invalid venue_id: Venue does not exist.")
                
            # We want to make sure the event actually exists and belongs to the specified venue
            event_row = conn.execute(
                text("SELECT venue_id FROM Events WHERE id = :event_id"), 
                {"event_id": review.event_id}
            ).fetchone()
            
            if not event_row:
                raise HTTPException(status_code=400, detail="Invalid event_id: Event does not exist.")
            if event_row[0] != review.venue_id:
                raise HTTPException(status_code=400, detail="Invalid venue_id: Event does not belong to this venue.")
                
            # 3. Handle Seat (Find or Create)
            upsert_seat_query = text("""
                INSERT INTO Seats (id, venue_id, section, row, seat_number)
                VALUES (:id, :v_id, :sec, :row, :num)
                ON CONFLICT (venue_id, section, row, seat_number) 
                DO UPDATE SET section = EXCLUDED.section 
                RETURNING id;
            """)

            final_seat_id = conn.execute(upsert_seat_query, {
                "id": str(uuid.uuid4()),
                "v_id": review.venue_id, 
                "sec": review.section,
                "row": review.row,
                "num": review.seat_number
            }).scalar()

            conn.execute(text("""
                INSERT INTO Reviews (
                    id, user_id, event_id, venue_id, seat_id,
                    rating_visual, rating_sound, rating_value, overall_rating,
                    price_paid, text, images, created_at
                ) VALUES (
                    :id, :user_id, :event_id, :venue_id, :seat_id,
                    :r_vis, :r_snd, :r_val, :r_over,
                    :price, :text, :images, :created_at
                )
            """), {
                "id": review_id,
                "user_id": user_id,
                "event_id": review.event_id,
                "venue_id": review.venue_id,
                "seat_id": final_seat_id,
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {str(e)}")

# @router.patch("/{review_id}/images")
# def update_review_images(review_id: str, payload: ReviewImagesUpdate, user_id: str = Depends(get_current_user)):
#     """
#     Called by the frontend AFTER successfully uploading images to S3.
#     This links the final S3 URLs back to the review.
#     """
#     if not engine:
#         raise HTTPException(status_code=500, detail="Database not configured")
        
#     try:
#         with engine.begin() as conn:
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Failed to update images: {str(e)}")

@router.get("/presigned-url")
def generate_s3_presigned_url(review_id: str, pic_num: int, filename: str, content_type: str, user_id: str = Depends(get_current_user)):
    """
    Generate a pre-signed URL for the frontend to upload an image directly to S3.
    This should be called for each image AFTER creating the base review.
    
    - review_id: The UUID of the review this image belongs to.
    - pic_num: Sequence number for multiple uploads (e.g., 1, 2, 3).
    - filename: Original name (e.g., "my_photo.jpg"). We only extract the extension.
    - content_type: The MIME type of the file (e.g., `image/jpeg`).
    """

    file_extension = filename.split(".")[-1]
    unique_filename = f"{review_id}_{pic_num}.{file_extension}"
    
    try:
        presigned_post = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET_NAME,
            Key=f"reviews/{unique_filename}",
            Fields={"acl": "public-read", "Content-Type": content_type},
            Conditions=[
                {"acl": "public-read"},
                {"Content-Type": content_type},
                ["content-length-range", 1, 10485760] # Max 10MB
            ],
            ExpiresIn=3600
        )
        
        final_image_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/reviews/{unique_filename}"
        
        return {
            "upload_instructions": presigned_post,
            "future_url": final_image_url,
            "method": "s3_presigned"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate S3 presigned URL: {str(e)}")
