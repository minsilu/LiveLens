from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from ...database import engine
from typing import Optional

router = APIRouter()


@router.get("/reviews")
def search_reviews(
    seat_id: Optional[str] = Query(None, description="Filter by seat ID"),
    event_id: Optional[str] = Query(None, description="Filter by event ID"),
    venue_id: Optional[str] = Query(None, description="Filter by venue ID"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Minimum overall rating (1-5)"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: overall_rating, created_at, price_paid"),
    order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):
    """
    Search, filter, and sort reviews.

    - **seat_id**: Filter reviews for a specific seat
    - **event_id**: Filter reviews for a specific event
    - **venue_id**: Filter reviews for a specific venue (joins with Events)
    - **min_rating**: Only reviews with overall_rating >= this value
    - **sort_by**: Field to sort results by (overall_rating, created_at, price_paid)
    - **order**: Sort direction (asc or desc)
    - **limit / offset**: Pagination controls
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")

    allowed_sort_fields = {"overall_rating", "created_at", "price_paid"}
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

            if seat_id:
                conditions.append("r.seat_id = :seat_id")
                params["seat_id"] = seat_id

            if event_id:
                conditions.append("r.event_id = :event_id")
                params["event_id"] = event_id

            if venue_id:
                conditions.append("e.venue_id = :venue_id")
                params["venue_id"] = venue_id

            if min_rating is not None:
                conditions.append("r.overall_rating >= :min_rating")
                params["min_rating"] = min_rating

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            count_query = text(f"""
                SELECT COUNT(*)
                FROM Reviews r
                LEFT JOIN Events e ON r.event_id = e.id
                LEFT JOIN Seats s ON r.seat_id = s.id
                {where_clause}
            """)
            total = conn.execute(count_query, params).scalar()

            query = text(f"""
                SELECT r.id, r.user_id, r.event_id, r.seat_id,
                       r.rating_visual, r.rating_sound, r.rating_value, r.overall_rating,
                       r.price_paid, r.text, r.created_at,
                       s.section, s.row
                FROM Reviews r
                LEFT JOIN Events e ON r.event_id = e.id
                LEFT JOIN Seats s ON r.seat_id = s.id
                {where_clause}
                ORDER BY r.{sort_by} {order}
                LIMIT :limit OFFSET :offset
            """)
            result = conn.execute(query, params)

            reviews = [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "event_id": row[2],
                    "seat_id": row[3],
                    "rating_visual": row[4],
                    "rating_sound": row[5],
                    "rating_value": row[6],
                    "overall_rating": row[7],
                    "price_paid": row[8],
                    "text": row[9],
                    "created_at": row[10],
                    "section": row[11],
                    "row": row[12],
                }
                for row in result
            ]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "results": reviews,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
