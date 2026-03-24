from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import text
from typing import Optional, Any
import uuid
import json
from datetime import datetime
import jwt

from ..database import engine
from ..auth_utils import SECRET_KEY, ALGORITHM

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
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

class ReviewDraft(BaseModel):
    id: Optional[str] = None
    draft_data: Any # Can be a JSON object containing the draft parts

@router.post("/")
def save_draft(draft: ReviewDraft, user_id: str = Depends(get_current_user)):
    """
    Saves or updates a review draft for the logged-in user.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    draft_id = draft.id if draft.id else str(uuid.uuid4())
    draft_json = json.dumps(draft.draft_data) if draft.draft_data is not None else "{}"
    now = datetime.utcnow()
    
    try:
        with engine.begin() as conn:
            # Check if this draft already exists and belongs to the user
            existing = conn.execute(
                text("SELECT id FROM ReviewDrafts WHERE id = :id"), 
                {"id": draft_id}
            ).fetchone()

            if existing: # Update
                conn.execute(text("""
                    UPDATE ReviewDrafts
                    SET draft_data = :data, updated_at = :now
                    WHERE id = :id AND user_id = :user_id
                """), {
                    "data": draft_json,
                    "now": now,
                    "id": draft_id,
                    "user_id": user_id
                })
            else: # Insert
                conn.execute(text("""
                    INSERT INTO ReviewDrafts (id, user_id, draft_data, created_at, updated_at)
                    VALUES (:id, :user_id, :data, :now, :now)
                """), {
                    "id": draft_id,
                    "user_id": user_id,
                    "data": draft_json,
                    "now": now
                })
            return {"message": "Draft saved successfully", "draft_id": draft_id}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save draft: {str(e)}")

@router.get("/")
def get_drafts(user_id: str = Depends(get_current_user)):
    """
    Retrieves all drafts for the logged-in user.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.begin() as conn:
            rows = conn.execute(text("""
                SELECT id, draft_data, created_at, updated_at
                FROM ReviewDrafts
                WHERE user_id = :user_id
                ORDER BY updated_at DESC
            """), {"user_id": user_id}).fetchall()
            
            drafts = []
            for r in rows:
                raw_data = r[1]
                if isinstance(raw_data, str):
                    parsed_data = json.loads(raw_data)
                elif raw_data is None:
                    parsed_data = {}
                else:
                    parsed_data = raw_data
                    
                drafts.append({
                    "id": str(r[0]),
                    "draft_data": parsed_data,
                    "created_at": r[2],
                    "updated_at": r[3]
                })
            return drafts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve drafts: {str(e)}")

@router.delete("/delete")
def delete_draft(draft_id: str, user_id: str = Depends(get_current_user)):
    """
    Discards a specific draft for the user.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                DELETE FROM ReviewDrafts
                WHERE id = :id AND user_id = :user_id
            """), {"id": draft_id, "user_id": user_id})
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Draft not found or unauthorized")
            
            return {"message": "Draft deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete draft: {str(e)}")
