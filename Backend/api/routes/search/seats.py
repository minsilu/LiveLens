from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from ...database import engine
from typing import Optional

router = APIRouter()


@router.get("/seats")
def search_seats(
    venue_id: str = Query(..., description="Venue ID (required)"),
    section: Optional[str] = Query(None, description="Filter by section name"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum average overall rating"),
    max_distance: Optional[float] = Query(None, ge=0, description="Maximum distance to stage"),
    sort_by: Optional[str] = Query(
        "distance_to_stage",
        description="Sort field: distance_to_stage, avg_overall, avg_price_paid, section"
    ),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):
    """
    Search, filter, and sort seats within a venue.

    - **venue_id**: Required. Restricts results to a specific venue.
    - **section**: Exact section name filter
    - **min_rating**: Only seats with avg_overall >= this value (from SeatAggregates)
    - **max_distance**: Only seats within this distance from the stage
    - **sort_by**: Field to sort results by (distance_to_stage, avg_overall, avg_price_paid, section)
    - **order**: Sort direction (asc or desc)
    - **limit / offset**: Pagination controls
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")

    allowed_sort_fields = {"distance_to_stage", "avg_overall", "avg_price_paid", "section"}
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

    # Qualify aggregates columns with table alias to avoid ambiguity
    sort_col = f"sa.{sort_by}" if sort_by in {"avg_overall", "avg_price_paid"} else f"s.{sort_by}"

    try:
        with engine.connect() as conn:
            conditions = ["s.venue_id = :venue_id"]
            params = {"venue_id": venue_id, "limit": limit, "offset": offset}

            if section:
                conditions.append("LOWER(s.section) = :section")
                params["section"] = section.lower()

            if max_distance is not None:
                conditions.append("s.distance_to_stage <= :max_distance")
                params["max_distance"] = max_distance

            if min_rating is not None:
                conditions.append("COALESCE(sa.avg_overall, 0) >= :min_rating")
                params["min_rating"] = min_rating

            where_clause = f"WHERE {' AND '.join(conditions)}"

            count_query = text(f"""
                SELECT COUNT(*)
                FROM Seats s
                LEFT JOIN SeatAggregates sa ON s.id = sa.seat_id
                {where_clause}
            """)
            total = conn.execute(count_query, params).scalar()

            query = text(f"""
                SELECT s.id, s.venue_id, s.section, s.row, s.seat_number,
                       s.distance_to_stage,
                       sa.avg_overall, sa.avg_price_paid, sa.review_count
                FROM Seats s
                LEFT JOIN SeatAggregates sa ON s.id = sa.seat_id
                {where_clause}
                ORDER BY {sort_col} {order}
                LIMIT :limit OFFSET :offset
            """)
            result = conn.execute(query, params)

            seats = [
                {
                    "id": row[0],
                    "venue_id": row[1],
                    "section": row[2],
                    "row": row[3],
                    "seat_number": row[4],
                    "distance_to_stage": row[5],
                    "avg_overall": row[6],
                    "avg_price_paid": row[7],
                    "review_count": row[8],
                }
                for row in result
            ]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "results": seats,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
