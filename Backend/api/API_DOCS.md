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

### Running Tests

```bash
cd Backend
source venv/bin/activate
PYTHONPATH=. pytest tests/test_search.py -v
```
