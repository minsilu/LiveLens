# LiveLens API Documentation

Base URL: `http://127.0.0.1:8000` (local) | App Runner URL (production)

> **Tip:** You can also explore all endpoints interactively via Swagger UI at `/docs`

---

## Auth (`/auth`)

### `POST /auth/register`
Register a new user account and receive a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "is_incognito": false
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

### `POST /auth/login`
Authenticate and receive a fresh JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "message": "Login successful"
}
```

---

## Search (`/search`)

### `GET /search/venues`
Search, filter, and sort venues.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | — | Free-text search across venue name and city |
| `city` | string | — | Filter by exact city name |
| `min_capacity` | int | — | Only venues with capacity >= this value |
| `sort_by` | string | `name` | Sort field: `name`, `capacity`, `city` |
| `order` | string | `asc` | Sort direction: `asc` or `desc` |
| `limit` | int | `20` | Results per page (1–100) |
| `offset` | int | `0` | Number of results to skip |

**Example Requests:**
```
GET /search/venues?q=scotiabank
GET /search/venues?city=Toronto&sort_by=capacity&order=desc
GET /search/venues?min_capacity=20000&limit=10&offset=0
```

**Response:**
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

## Dev Tools (`/dev`)

> These endpoints are for development and testing only.

### `POST /dev/generate`
Injects ~1000 mock records (users, venues, events, seats, reviews) into the database.

### `GET /dev/reviews`
Fetch mocked reviews with venue/event/seat details.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | `20` | Number of reviews to return |
| `venue_name` | string | `Scotiabank Arena` | Filter by venue name |

### `GET /dev/tables`
List all database tables (PostgreSQL only).

---

## Running Tests

```bash
cd Backend
source venv/bin/activate
PYTHONPATH=. pytest tests/test_auth.py tests/test_search.py -v
```
