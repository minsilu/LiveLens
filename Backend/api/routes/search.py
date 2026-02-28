from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from ..database import engine
from typing import Optional

router = APIRouter()


@router.get("/venues")
def search_venues(
    q: Optional[str] = Query(None, description="Search by venue name or city"),
    city: Optional[str] = Query(None, description="Filter by city"),
    min_capacity: Optional[int] = Query(None, description="Minimum venue capacity"),
    sort_by: Optional[str] = Query("name", description="Sort field: name, capacity, city"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):
    """
    Search, filter, and sort venues.

    - **q**: Free-text search across venue name and city
    - **city**: Exact city filter
    - **min_capacity**: Only return venues with capacity >= this value
    - **sort_by**: Field to sort results by (name, capacity, city)
    - **order**: Sort direction (asc or desc)
    - **limit / offset**: Pagination controls
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Validate sort parameters
    allowed_sort_fields = {"name", "capacity", "city"}
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
            # Build dynamic WHERE clauses
            conditions = []
            params = {"limit": limit, "offset": offset}

            if q:
                conditions.append("(LOWER(name) LIKE :q OR LOWER(city) LIKE :q)")
                params["q"] = f"%{q.lower()}%"

            if city:
                conditions.append("LOWER(city) = :city")
                params["city"] = city.lower()

            if min_capacity is not None:
                conditions.append("capacity >= :min_capacity")
                params["min_capacity"] = min_capacity

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            # Count total matching results (for pagination metadata)
            count_query = text(f"SELECT COUNT(*) FROM Venues {where_clause}")
            total = conn.execute(count_query, params).scalar()

            # Fetch paginated results with sorting
            query = text(f"""
                SELECT id, name, city, capacity, tags
                FROM Venues
                {where_clause}
                ORDER BY {sort_by} {order}
                LIMIT :limit OFFSET :offset
            """)
            result = conn.execute(query, params)

            venues = [
                {
                    "id": row[0],
                    "name": row[1],
                    "city": row[2],
                    "capacity": row[3],
                    "tags": row[4],
                }
                for row in result
            ]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "results": venues,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
