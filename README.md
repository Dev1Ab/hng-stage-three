# HNG-Internship Stage 2
# Intelligence Query Engine API

A backend system built for **Insighta Labs** that provides advanced filtering, sorting, pagination, and natural language querying over demographic profile data.

---

# Features

- Advanced filtering (gender, age, country, probability ranges)
- Sorting (age, created_at, gender_probability)
- Pagination (page & limit support, max 50)
- Natural language query parsing (rule-based, no AI/LLMs)
- External API-based profile generation (Genderize, Agify, Nationalize)
- Standardized API response format

---

# Tech Stack

- Python (Django + Django REST Framework)
- PostgreSQL

---

# API ENDPOINTS

---

## 1. Create / Get Profile

### `POST /api/profiles`

Creates a new profile using external APIs or returns existing profile if name exists.

### Request Body:
```json
{
  "name": "emmanuel"
}
```

Response (Success):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-v7",
    "name": "emmanuel",
    "gender": "male",
    "gender_probability": 0.99,
    "age": 34,
    "age_group": "adult",
    "country_id": "NG",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```


## 2. Get All Profiles (Advanced Query Engine)

### `GET /api/profiles`

Supports filtering, sorting, and pagination.

---

### Filters Supported

| Parameter | Description |
|----------|-------------|
| gender | male / female |
| age_group | child / teenager / adult / senior |
| country_id | ISO country code |
| min_age | minimum age |
| max_age | maximum age |
| min_gender_probability | float filter |
| min_country_probability | float filter |

---

### Sorting

| Parameter | Values |
|----------|--------|
| sort_by | age, created_at, gender_probability |
| order | asc, desc |

---

### Pagination

| Parameter | Default | Max |
|----------|--------|-----|
| page | 1 | - |
| limit | 10 | 50 |

---

### Example Request

```http
GET /api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10
```
Response

```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 2026,
  "data": [
    {
      "id": "uuid-v7",
      "name": "emmanuel",
      "gender": "male",
      "gender_probability": 0.99,
      "age": 34,
      "age_group": "adult",
      "country_id": "NG",
      "country_probability": 0.85,
      "created_at": "2026-04-01T12:00:00Z"
    }
  ]
}
```
## 3. Natural Language Search

`GET /api/profiles/search?q=`

Converts plain English into structured filters using a rule-based parsing system (**NO AI / LLM used**).

---

## Example Requests

**Young males from Nigeria**  
`/api/profiles/search?q=young males from nigeria`

**Females above 30**  
`/api/profiles/search?q=females above 30`

**Adult males from Kenya**  
`/api/profiles/search?q=adult males from kenya`

---

## Parsing Rules

| Phrase        | Mapping              |
|--------------|----------------------|
| young        | age 16–24           |
| above X      | age >= X            |
| below X      | age <= X            |
| male         | gender = male       |
| female       | gender = female     |
| teenager     | age_group = teenager |
| adult        | age_group = adult   |
| child        | age_group = child   |
| senior       | age_group = senior  |
| country name | mapped to ISO code  |

---

## Response Format

```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 120,
  "data": []
}
```

Error Response
```json
{
  "status": "error",
  "message": "Unable to interpret query"
}
```

---

## Natural Language Parsing Approach

The system uses a rule-based keyword parser (no AI/ML models).

### How it works:
- Convert query to lowercase
- Match keywords using:
- Regex (for age rules: above / below)
- Direct keyword mapping (male, female, country names)
- Apply filters incrementally to Django QuerySet
- If no rules match → return error

Example

Input:

``"young males from nigeria"``

Parsed into:

gender = male
age = 16–24
country_id = NG

### Limitations

This system does NOT support:

- Complex grammar queries (e.g. "not older than 40")
- Range expressions (e.g. "between 20 and 30")
- Synonyms not defined in keyword map
- Spelling mistakes or fuzzy matching
- Multi-country queries (e.g. "Nigeria and Kenya")
- Advanced natural language understanding (no LLM used by design)
### Country Mapping Limitation

Country recognition is based on a predefined static dictionary:
```json
COUNTRY_MAP = {
    "nigeria": "NG",
    "kenya": "KE",
    "angola": "AO",
}
```
      
- Only countries included in the `COUNTRY_MAP` are supported
- Queries outside this list cannot be interpreted