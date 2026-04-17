# Backend Wizards — Stage 1 API

A Django REST API that generates and stores user profiles using external APIs (Genderize, Agify, Nationalize).

---

## Base URL
``` https://url.com ```

---

## Features
- Create profile from name
- External API integration (gender, age, nationality)
- Idempotent requests (no duplicates)
- Age grouping (child, teenager, adult, senior)
- Filtering (gender, country_id, age_group)
- CRUD operations

---

## Endpoints

### Create Profile
`POST /api/profiles/`

```json
{ "name": "ella" }
```
Success Response 201

```json
{
  "status": "success",
  "data": {
    "id": "uuid-v7",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "US",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```
### Get All Profiles

`GET /api/profiles/?gender=male&country_id=NG&age_group=adult`

Success Response 200

```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": "uuid",
      "name": "emmanuel",
      "gender": "male",
      "age": 25,
      "age_group": "adult",
      "country_id": "NG"
    }
  ]
}
```

### Get Single Profile
`GET /api/profiles/{id}/`

### Delete Profile

`DELETE /api/profiles/{id}/`

### Setup Instructions
1. Clone repo
```
git clone https://github.com/yourusername/repo-name.git
cd repo-name
```
2. Create virtual environment
```
python -m venv myenv
source myenv/bin/activate  # mac/linux
myenv\Scripts\activate     # windows
```
3. Install dependencies
```
pip install -r requirements.txt
```
4. Run migrations
```
python manage.py migrate
```
5. Start server
```
python manage.py runserver
```