import os
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from ...database import engine
from typing import Optional

router = APIRouter()

@router.get("/venues/stats")
def get_venue_stats():
    """Get aggregated platform stats for all venues."""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    COUNT(DISTINCT v.id) as total_venues,
                    COUNT(r.id) as total_reviews,
                    COALESCE(ROUND(AVG(r.overall_rating), 1), 0) as avg_rating
                FROM Venues v
                LEFT JOIN Seats s ON s.venue_id = v.id
                LEFT JOIN Reviews r ON r.seat_id = s.id
            """)
            row = conn.execute(query).fetchone()
            
            # Simple assumption for satisfaction (e.g. % of reviews > 3)
            # Just mimicking the frontend static for now or calculate:
            # For simplicity, returning static 98 if missing, or based on avg_rating
            satisfaction = min(100, max(0, int((float(row[2]) / 5.0) * 100))) if row[2] else 0
            if row[1] == 0:
                satisfaction = 100 # default
                
            return {
                "total_venues": row[0],
                "total_reviews": row[1],
                "avg_rating": row[2],
                "satisfaction": satisfaction
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



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

    allowed_sort_fields = {"name", "capacity", "city", "rating"}
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
                conditions.append("(LOWER(v.name) LIKE :q OR LOWER(v.city) LIKE :q)")
                params["q"] = f"%{q.lower()}%"

            if city:
                conditions.append("LOWER(v.city) = :city")
                params["city"] = city.lower()

            if min_capacity is not None:
                conditions.append("v.capacity >= :min_capacity")
                params["min_capacity"] = min_capacity

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            count_query = text(f"SELECT COUNT(*) FROM Venues v {where_clause}")
            total = conn.execute(count_query, params).scalar()

            query = text(f"""
                SELECT v.id, v.name, v.city, v.capacity, v.tags,
                       ROUND(AVG(r.overall_rating), 1) as avg_rating,
                       COUNT(r.id) as review_count,
                       v.seat_map_2d_url, v.seat_map_meta,
                       (SELECT COUNT(*) FROM Events e2
                        WHERE e2.venue_id = v.id
                          AND e2.event_date >= DATE('now')) as upcoming_events
                FROM Venues v
                LEFT JOIN Seats s ON s.venue_id = v.id
                LEFT JOIN Reviews r ON r.seat_id = s.id
                {where_clause}
                GROUP BY v.id, v.name, v.city, v.capacity, v.tags, v.seat_map_2d_url, v.seat_map_meta
                ORDER BY {"avg_rating" if sort_by == "rating" else f"v.{sort_by}"} {order}
                LIMIT :limit OFFSET :offset
            """)
            result = conn.execute(query, params)

            import re
            S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "livelens-images")
            AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
            venues = []
            for row in result:
                slug = re.sub(r'[^a-z0-9]+', '_', row[1].lower()).strip('_')
                base_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/venues/{slug}"
                
                # Default to just the facade
                image_urls = [f"{base_url}/facade.png"]
                
                # If it's scotiabank_arena, provide multiple demo images (assuming these exist)
                # The frontend will use these for a slideshow
                if slug == "scotiabank_arena":
                    image_urls = [
                        f"{base_url}/facade.png",
                        f"{base_url}/interior.jpg",
                        f"{base_url}/stage.jpg"
                    ]
                    
                venues.append({
                    "id": row[0],
                    "name": row[1],
                    "city": row[2],
                    "capacity": row[3],
                    "tags": row[4],
                    "rating": row[5],
                    "review_count": row[6],
                    "seat_map_2d_url": row[7],
                    "seat_map_meta": row[8],
                    "upcoming_events": row[9] if len(row) > 9 else 0,
                    "image_url": f"{base_url}/facade.png",
                    "image_urls": image_urls
                })

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
