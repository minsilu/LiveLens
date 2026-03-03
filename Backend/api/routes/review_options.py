from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
import logging

from ..database import engine

router = APIRouter()
logger = logging.getLogger(__name__)

# Response Models for Swagger UI
class EventDictionaryItem(BaseModel):
    event_id: str
    display_name: str
    venue_id: str

class VenueMetadata(BaseModel):
    venue_id: str
    name: str
    seat_map_2d_url: Optional[str]
    available_sections: List[str]

@router.get("/events", response_model=List[EventDictionaryItem])
def get_events_dictionary(venue_id: Optional[str] = None):
    """
    Fetch a lightweight list of events for UI selection components (dropdowns/autocomplete).

    ### Purpose:
    Provides a simplified event list to help users select a specific event to get the `event_id` and `venue_id` for the review insertion.
    It automatically formats a `display_name` combining the event name and date.

    ### Input:
    - **venue_id** (Optional): A UUID string. If provided, the list filters events held only at that specific venue.

    ### Output:
    Returns a list of objects containing:
    - **event_id**: The unique UUID of the event.
    - **display_name**: A formatted string, e.g., "Taylor Swift: The Eras Tour (2024-11-15)".
    - **venue_id**: The UUID of the associated venue.

    ### Behavior:
    - Results are sorted by `event_date` in descending order (newest first).
    - Limited to the top 100 results for performance.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.begin() as conn:
            query_str = """
                SELECT e.id as event_id, 
                       e.name,
                       e.event_date,
                       e.venue_id
                FROM Events e
            """
            params = {}
            if venue_id:
                query_str += " WHERE e.venue_id = :venue_id"
                params["venue_id"] = venue_id
                
            query_str += " ORDER BY e.event_date DESC LIMIT 100"
            
            result = conn.execute(text(query_str), params).fetchall()
            
            # Format the display_name in Python to be DB-agnostic (SQLite vs Postgres)
            formatted_results = []
            for row in result:
                # row[2] could be a string (SQLite) or a datetime.date object (Postgres)
                date_str = str(row[2]).split(" ")[0] if row[2] else "Unknown Date"
                display_name = f"{row[1]} ({date_str})"
                formatted_results.append({
                    "event_id": str(row[0]),
                    "display_name": display_name,
                    "venue_id": str(row[3])
                })
                
            return formatted_results
    except Exception as e:
        logger.error(f"Error fetching event dictionary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch event dictionary")

@router.get("/venues", response_model=VenueMetadata)
def get_venue_metadata(venue_id: str):
    """
    Retrieve foundational metadata required to initialize the Seat Selection UI.

    ### Purpose:
    When a user selects an event/venue, the frontend needs to know:
    1. The visual map (2D URL) to display.
    2. Which "Sections" (e.g., Floor, 100 Level) actually have seats available in the database.

    ### Input:
    - **venue_id** (Query Param, Mandatory): The UUID of the venue to look up.

    ### Output:
    Returns a single object containing:
    - **venue_id**: The UUID of the venue.
    - **name**: The official name of the venue (e.g., "Scotiabank Arena").
    - **seat_map_2d_url**: URL to the 2D layout image/asset.
    - **available_sections**: A list of strings representing unique sections found in the `Seats` table for this venue.

    ### Errors:
    - **404 Not Found**: If the provided `venue_id` does not exist in the Venues table.
    - **500 Internal Error**: Database connection or query failure.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        with engine.begin() as conn:
            # 1. Fetch Venue Basic Info
            venue_row = conn.execute(
                text("SELECT id, name, seat_map_2d_url FROM Venues WHERE id = :venue_id"),
                {"venue_id": venue_id}
            ).fetchone()
            
            if not venue_row:
                raise HTTPException(status_code=404, detail="Venue not found")
                
            # 2. Fetch distinct sections dynamically from the Seats table
            # This ensures the frontend dropdown only shows sections we actually have data (or mock data) for.
            sections_result = conn.execute(
                text("""
                    SELECT DISTINCT section 
                    FROM Seats 
                    WHERE venue_id = :venue_id 
                    ORDER BY section
                """),
                {"venue_id": venue_id}
            ).fetchall()
            
            available_sections = [row[0] for row in sections_result]
            
            return {
                "venue_id": str(venue_row[0]),
                "name": venue_row[1],
                "seat_map_2d_url": venue_row[2],
                "available_sections": available_sections
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching venue metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch venue data")
