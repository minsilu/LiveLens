# LiveLens Search API Documentation

> **Tip:** You can also explore all endpoints interactively via Swagger UI at `/docs`

---

## Venue Search (`GET /search/venues`)

Search, filter, and sort venues.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | — | Free-text search across venue name and city |
| `city` | string | — | Filter by exact city name |
| `min_capacity` | int | — | Only venues with capacity >= this value |
| `sort_by` | string | `name` | Sort field: `name`, `capacity`, `city` |
| `order` | string | `asc` | Sort direction: `asc` or `desc` |
| `limit` | int | `20` | Results per page (1–100) |
| `offset` | int | `0` | Number of results to skip |

### Example Requests

```
GET /search/venues?q=scotiabank
GET /search/venues?city=Toronto&sort_by=capacity&order=desc
GET /search/venues?min_capacity=20000&limit=10&offset=0
```

### Response

```json
{
  "total": 4,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "id": "uuid",
      "name": "Scotiabank Arena",
      "city": "Toronto",
      "capacity": 19800,
      "tags": "[\"sports\", \"concerts\"]"
    }
  ]
}
```

---

## Event Search (`GET /search/events`)

Search, filter, and sort events.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | — | Free-text search across event name and artist |
| `venue_id` | string | — | Filter by venue ID |
| `genre` | string | — | Filter by exact genre |
| `date_from` | string | — | Events on or after this date (`YYYY-MM-DD`) |
| `date_to` | string | — | Events on or before this date (`YYYY-MM-DD`) |
| `sort_by` | string | `event_date` | Sort field: `name`, `event_date`, `artist` |
| `order` | string | `asc` | Sort direction: `asc` or `desc` |
| `limit` | int | `20` | Results per page (1–100) |
| `offset` | int | `0` | Number of results to skip |

### Example Requests

```
GET /search/events?q=coldplay
GET /search/events?venue_id=abc-123&genre=rock
GET /search/events?date_from=2025-06-01&date_to=2025-08-31&sort_by=event_date
```

### Response

```json
{
  "total": 2,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "id": "uuid",
      "venue_id": "uuid",
      "name": "Coldplay World Tour",
      "artist": "Coldplay",
      "genre": "rock",
      "event_date": "2025-07-15",
      "ticket_url": "https://tickets.example.com/1"
    }
  ]
}
```

---

## Seat Search (`GET /search/seats`)

Search, filter, and sort seats within a venue. Includes aggregate ratings from `SeatAggregates`.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `venue_id` | string | **required** | Restrict results to this venue |
| `section` | string | — | Filter by exact section name |
| `min_rating` | float | — | Only seats with avg_overall >= this value |
| `max_distance` | float | — | Only seats within this distance from the stage |
| `sort_by` | string | `distance_to_stage` | Sort field: `distance_to_stage`, `avg_overall`, `avg_price_paid`, `section` |
| `order` | string | `asc` | Sort direction: `asc` or `desc` |
| `limit` | int | `20` | Results per page (1–100) |
| `offset` | int | `0` | Number of results to skip |

### Example Requests

```
GET /search/seats?venue_id=abc-123
GET /search/seats?venue_id=abc-123&section=Floor&sort_by=avg_overall&order=desc
GET /search/seats?venue_id=abc-123&min_rating=4.0&max_distance=20
```

### Response

```json
{
  "total": 10,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "id": "uuid",
      "venue_id": "uuid",
      "section": "Floor",
      "row": "A",
      "seat_number": "1",
      "distance_to_stage": 5.0,
      "avg_overall": 4.2,
      "avg_price_paid": 80.0,
      "review_count": 10
    }
  ]
}
```

---

## Review Search (`GET /search/reviews`)

Search, filter, and sort reviews.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `seat_id` | string | — | Filter reviews for a specific seat |
| `event_id` | string | — | Filter reviews for a specific event |
| `min_rating` | int | — | Only reviews with overall_rating >= this value (1–5) |
| `sort_by` | string | `created_at` | Sort field: `overall_rating`, `created_at`, `price_paid` |
| `order` | string | `desc` | Sort direction: `asc` or `desc` |
| `limit` | int | `20` | Results per page (1–100) |
| `offset` | int | `0` | Number of results to skip |

### Example Requests

```
GET /search/reviews?seat_id=abc-123
GET /search/reviews?event_id=abc-123&min_rating=4&sort_by=overall_rating&order=desc
GET /search/reviews?min_rating=5&limit=10
```

### Response

```json
{
  "total": 3,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "event_id": "uuid",
      "seat_id": "uuid",
      "rating_visual": 5,
      "rating_sound": 4,
      "rating_value": 3,
      "overall_rating": 4,
      "price_paid": 75.0,
      "text": "Great view!",
      "created_at": "2025-01-01T00:00:00"
    }
  ]
}
```

---

## Running Tests

```bash
cd Backend
source venv/bin/activate
PYTHONPATH=. pytest tests/test_search.py -v
```
