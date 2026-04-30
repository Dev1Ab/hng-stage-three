# Insighta Labs+ Backend

A secure backend system for **Insighta Labs+**, supporting:

* GitHub OAuth (PKCE)
* JWT authentication (access + refresh tokens)
* Role-based access control (Admin / Analyst)
* Multi-interface access (CLI + Web)
* Profile intelligence APIs
* CSV export
* Rate limiting and request protection

---

## Tech Stack

* Django + Django REST Framework
* SimpleJWT (JWT auth)
* PostgreSQL
* GitHub OAuth (PKCE)
* CORS + Cookie-based auth

---

## Authentication System

### Overview

This system supports **two authentication flows**:

| Interface | Auth Method                      |
| --------- | -------------------------------- |
| CLI       | OAuth + PKCE + Bearer tokens     |
| Web       | OAuth + PKCE + HTTP-only cookies |

---

### OAuth Flow (GitHub + PKCE)

#### Step 1 — Initiate Login

```http
GET /auth/github
```

* Redirects user to GitHub OAuth
* Supports PKCE (`code_challenge`)
* Automatically generates PKCE if not provided

---

#### Callback

```http
GET /auth/github/callback
```

Handles:

* CLI flow → redirects to CLI callback
* Web flow → exchanges code + sets cookies

---

## Token System

### Access Token

* Short-lived
* Used for API authentication

### Refresh Token

* Long-lived
* Used to generate new access tokens

---

### Refresh Endpoint

```http
POST /auth/refresh
```

Request:

```json
{
  "refresh_token": "..."
}
```

Response:

```json
{
  "status": "success",
  "access_token": "...",
  "refresh_token": "..."
}
```

---

## Web Authentication (Cookies)

* Tokens stored in **HTTP-only cookies**
* Not accessible via JavaScript
* Secure production settings:

```python
httponly=True
secure=True
samesite="None"
```

---

## CLI Authentication

* Stores credentials at:

```bash
~/.insighta/credentials.json
```

* Uses:

```http
Authorization: Bearer <access_token>
```

* Auto-refreshes tokens when expired

---

## Role-Based Access Control

### Roles

| Role    | Permissions                          |
| ------- | ------------------------------------ |
| Admin   | Full access (create, delete, export) |
| Analyst | Read-only access                     |

---

### Enforcement

* Applied at view level:

```python
IsAuthenticated + IsAdmin
```

---

## API Endpoints

### Auth

| Endpoint                | Method | Description        |
| ----------------------- | ------ | ------------------ |
| `/auth/github`          | GET    | Start OAuth        |
| `/auth/github/callback` | GET    | Handle callback    |
| `/auth/exchange`        | POST   | CLI token exchange |
| `/auth/refresh`         | POST   | Refresh tokens     |
| `/auth/logout`          | POST   | Logout             |
| `/auth/me`              | GET    | Current user       |

---

### Profiles

| Endpoint               | Method | Description                 |
| ---------------------- | ------ | --------------------------- |
| `/api/profiles`        | GET    | List profiles               |
| `/api/profiles`        | POST   | Create profile (Admin only) |
| `/api/profiles/<id>`   | GET    | Retrieve profile            |
| `/api/profiles/<id>`   | DELETE | Delete (Admin only)         |
| `/api/profiles/search` | GET    | Natural search              |
| `/api/profiles/export` | GET    | Export CSV                  |

---

## Features

### Filtering & Sorting

Supports:

* gender
* age range
* country
* probability thresholds
* sorting (age, created_at, etc.)

---

### Natural Language Search

```http
GET /api/profiles/search?q=female adults in nigeria above 30
```

---

### CSV Export

```http
GET /api/profiles/export?format=csv
```

* Downloads CSV file
* Saves data for CLI and browser

---

## Rate Limiting

* Custom throttle classes:

  * `AuthRateThrottle`
  * `UserRateThrottle`

Protects:

* Auth endpoints
* Profile endpoints

---

## Security

* PKCE enforced for OAuth
* HTTP-only cookies for web
* Token blacklisting (logout)
* Role-based access
* Input validation on queries

---

## API Versioning

Headers:

```http
X-API-Version: 1
```

---

## Running Locally

```bash
git clone https://github.com/Dev1Ab/hng-stage-three.git
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---