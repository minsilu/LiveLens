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
    Saves a new ongoing review draft or updates an existing one for the authenticated user.

    ### Functionality:
    - This endpoint acts as an **Upsert** (Update or Insert) mechanism.
    - If `draft.id` is provided and exists in the database, it updates the stored content.
    - If `draft.id` is null or does not exist, it generates a new UUID and creates a record.
    - Ensures security by verifying that only the owner of a draft can update it via the `user_id` check.

    ### Input (Request Body):
    - **draft**: `ReviewDraft` (Pydantic Model)
        - `id`: Optional[str] - The UUID of the draft. Pass `null` for new drafts.
        - `draft_data`: dict - A JSON object containing partial review info (e.g., event_id, text, ratings).
    - **user_id**: `str` - Extracted automatically from the **JWT Bearer Token** in the header.

    ### Output (Response):
    - **Success (200 OK)**:
        ```json
        {
            "message": "Draft saved successfully",
            "draft_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        ```
    - **Failure (500/401)**:
        - `500`: Database connection issues or SQL execution errors.
        - `401`: Missing or invalid authentication token.

    ---
    :param draft: The draft object containing the ID and the data payload.
    :param user_id: The unique identifier of the user (from token dependency).
    :return: A dictionary containing a confirmation message and the draft UUID.
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
    Fetches all review drafts associated with the currently authenticated user.
    This endpoint is used to populate a 'Drafts' or 'Continue Writing' list in the frontend.

    ### 1. Mandatory Header (Authentication)
    - **Authorization**: `Bearer <JWT_TOKEN>`
    - The `user_id` is automatically extracted from the token's 'sub' claim via the `get_current_user` dependency.
    
    ### 2. Response Format (Returns a List of Objects)
    Returns a `List[Dict]` where each object represents a draft:
    ```json
    [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "draft_data": {
          "event_id": "...",
          "text": "The view was...",
          "rating_visual": 5
        },
        "created_at": "2026-03-24T14:30:00",
        "updated_at": "2026-03-24T15:45:00"
      }
    ]
    ```

    ### 3. Exceptions
    - **500 Internal Server Error**: Raised if the database engine is not initialized or if a SQL execution error occurs.
    - **401 Unauthorized**: Raised if the JWT is missing, invalid, or expired (via `get_current_user`).

    ---
    :param user_id: (Injected) The unique identifier of the user requesting their data.
    :return: A list of sanitized draft objects sorted by the latest update.
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
    Deletes a user's review draft.

    - **Args**: 
        - `draft_id` (Query Param, UUID string): The unique ID of the draft to delete.
        - `user_id` (Injected): Extracted from JWT for ownership verification.
    
    - **Action**: Removes the record from `ReviewDrafts` only if it belongs to the requester.
    
    - **Returns**: A success message or 404 if the draft is missing/unauthorized.
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
