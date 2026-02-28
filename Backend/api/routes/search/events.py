from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from ...database import engine
from typing import Optional

router = APIRouter()


@router.get("/events")
def search_events(
    q: Optional[str] = Query(None, description="Search by event name or artist"),
    venue_id: Optional[str] = Query(None, description="Filter by venue ID"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    date_from: Optional[str] = Query(None, description="Filter events on or after this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter events on or before this date (YYYY-MM-DD)"),
    sort_by: Optional[str] = Query("event_date", description="Sort field: name, event_date, artist"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):
    """
    Search, filter, and sort events.

    - **q**: Free-text search across event name and artist
    - **venue_id**: Filter by venue
    - **genre**: Exact genre filter
    - **date_from / date_to**: Date range filter (YYYY-MM-DD)
    - **sort_by**: Field to sort results by (name, event_date, artist)
    - **order**: Sort direction (asc or desc)
    - **limit / offset**: Pagination controls
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")

    allowed_sort_fields = {"name", "event_date", "artist"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by field. Allowed: {', '.join(allowed_sort_fields)}"
        )

    if order not in ("asc", "desc"):
        raise HTTPException(
            status_code=400,
            detail="Invalid order. Allowed: asc, desc"
        )

    try:
        with engine.connect() as conn:
            conditions = []
            params = {"limit": limit, "offset": offset}

            if q:
                conditions.append("(LOWER(name) LIKE :q OR LOWER(artist) LIKE :q)")
                params["q"] = f"%{q.lower()}%"

            if venue_id:
                conditions.append("venue_id = :venue_id")
                params["venue_id"] = venue_id

            if genre:
                conditions.append("LOWER(genre) = :genre")
                params["genre"] = genre.lower()

            if date_from:
                conditions.append("event_date >= :date_from")
                params["date_from"] = date_from

            if date_to:
                conditions.append("event_date <= :date_to")
                params["date_to"] = date_to

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            count_query = text(f"SELECT COUNT(*) FROM Events {where_clause}")
            total = conn.execute(count_query, params).scalar()

            query = text(f"""
                SELECT id, venue_id, name, artist, genre, event_date, ticket_url
                FROM Events
                {where_clause}
                ORDER BY {sort_by} {order}
                LIMIT :limit OFFSET :offset
            """)
            result = conn.execute(query, params)

            events = [
                {
                    "id": row[0],
                    "venue_id": row[1],
                    "name": row[2],
                    "artist": row[3],
                    "genre": row[4],
                    "event_date": row[5],
                    "ticket_url": row[6],
                }
                for row in result
            ]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "results": events,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
