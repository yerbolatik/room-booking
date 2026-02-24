# Hotel Room Booking API

Production-ready REST API for hotel room reservation management built with Django + Django REST Framework.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 5.0 + DRF 3.15 |
| Database | PostgreSQL 16 |
| Auth | SimpleJWT (Bearer tokens) |
| Filtering | django-filter |
| API Docs | drf-spectacular (Swagger / ReDoc) |
| Tests | pytest + pytest-django |
| Server | Gunicorn |
| Container | Docker + docker-compose |

---

## Project Structure

```
room_booking/
├── config/
│   ├── settings/
│   │   ├── base.py          # Shared settings
│   │   ├── development.py   # Dev overrides
│   │   └── production.py    # Production hardening
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/
│   │   ├── exceptions.py    # Custom exception handler
│   │   └── models.py        # TimestampedModel abstract base
│   ├── users/               # Auth & user profiles
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── tests/
│   ├── rooms/               # Room catalogue & availability
│   │   ├── models.py
│   │   ├── filters.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── tests/
│   └── bookings/            # Booking lifecycle
│       ├── models.py
│       ├── filters.py
│       ├── serializers.py
│       ├── services.py      # Conflict-safe booking logic
│       ├── views.py
│       ├── urls.py
│       ├── permissions.py
│       ├── exceptions.py
│       ├── admin.py
│       └── tests/
├── Makefile
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── .env.example
```

---

## Setup

### 1. Clone and configure environment

```bash
git clone https://github.com/yerbolatik/room-booking
cd room-booking
cp .env.example .env
# Edit .env — set SECRET_KEY and POSTGRES_PASSWORD
```

### 2. Docker (recommended)

```bash
make build      # Build images
make up         # Start db + api
make migrate    # Apply migrations
make superuser  # Create admin user
```

API is available at `http://localhost:8000`

### 3. Local development (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # set POSTGRES_HOST=localhost
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Make Commands

```
make help            - Show all available commands
make build           - Build Docker images
make up              - Start all services
make down            - Stop all services
make restart         - Restart all services
make logs            - Tail logs from all containers
make shell           - Open bash shell in api container
make migrate         - Run database migrations
make superuser       - Create a Django superuser
make test            - Run test suite
make clean           - Remove containers, images, and volumes
make db-shell        - Open psql in the db container
make db-reset        - Drop DB, re-migrate, create superuser
make dev-up          - Start development stack with live reload
make prod-up         - Start production stack
make backup          - Dump database to SQL file
make restore FILE=.. - Restore database from SQL file
```

---

## API Documentation

| URL | Description |
|---|---|
| `/api/v1/docs/` | Swagger UI |
| `/api/v1/redoc/` | ReDoc |
| `/admin/` | Django Admin |

---

## API Endpoints

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register/` | Public | Register new user |
| POST | `/api/v1/auth/login/` | Public | Login, get JWT tokens |
| POST | `/api/v1/auth/token/refresh/` | Public | Refresh access token |
| GET/PATCH | `/api/v1/auth/me/` | Required | Own profile |

### Rooms — publicly accessible, no login required

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/rooms/` | Public | List rooms |
| GET | `/api/v1/rooms/{id}/` | Public | Room detail |
| GET | `/api/v1/rooms/available/` | Public | Available rooms for a date range |

**Filters** (`/api/v1/rooms/`):

| Param | Example | Description |
|---|---|---|
| `price_min` | `50` | Min price per night |
| `price_max` | `200` | Max price per night |
| `capacity_min` | `2` | Min number of beds |
| `capacity_max` | `4` | Max number of beds |
| `ordering` | `-price_per_night` | Sort field (prefix `-` for desc) |

**Availability search**:
```
GET /api/v1/rooms/available/?check_in=2025-08-01&check_out=2025-08-05
```

### Bookings — authentication required

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/bookings/` | Required | My bookings |
| POST | `/api/v1/bookings/` | Required | Create booking |
| GET | `/api/v1/bookings/{id}/` | Owner/Admin | Booking detail |
| POST | `/api/v1/bookings/{id}/cancel/` | Owner/Admin | Cancel booking |

---

## Usage Examples

### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Smith",
    "phone": "+1-555-0100",
    "password": "StrongP@ss123",
    "password_confirm": "StrongP@ss123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "StrongP@ss123"}'
```

```json
{
  "access": "<token>",
  "refresh": "<token>",
  "user": {"id": 1, "email": "alice@example.com", "full_name": "Alice Smith"}
}
```

### List available rooms

```bash
curl "http://localhost:8000/api/v1/rooms/available/?check_in=2025-08-01&check_out=2025-08-05"
```

### Book a room

```bash
curl -X POST http://localhost:8000/api/v1/bookings/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "check_in": "2025-08-01",
    "check_out": "2025-08-05",
    "notes": "Late check-in requested"
  }'
```

### Cancel a booking

```bash
curl -X POST http://localhost:8000/api/v1/bookings/1/cancel/ \
  -H "Authorization: Bearer <access_token>"
```

---

## Running Tests

```bash
# All tests with coverage report
make test

# Or directly
pytest

# Specific app
pytest apps/bookings/tests/ -v

# Without coverage (faster)
pytest --no-cov
```

---

## Code Quality

```bash
# Lint + auto-fix with Ruff (configured in setup.cfg)
ruff check .
ruff check . --fix

# Static type checking with mypy (strict mode, configured in setup.cfg)
mypy .
```

---

## Architecture

### Service Layer

Business logic lives in `services.py` — views only validate and delegate.

```
Request -> View -> Serializer (validate) -> Service (logic) -> Model (persist)
```

### Booking Overlap Prevention (defence-in-depth)

1. **Application layer** — `BookingService.create_booking` wraps the conflict check and INSERT in a `SELECT FOR UPDATE` transaction:
   ```
   existing.check_in < requested.check_out AND existing.check_out > requested.check_in
   ```
2. **Database layer** — `CheckConstraint` enforces `check_out > check_in` at the storage level.

### Permissions Summary

| Role | Rooms | Own Bookings | Other Bookings |
|---|---|---|---|
| Anonymous | Read | — | — |
| Authenticated | Read | Full access | No access |
| Staff/Admin | Read | Full access | Full access |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | Django secret key (required) |
| `DEBUG` | `False` | Enable debug mode |
| `ALLOWED_HOSTS` | `""` | Comma-separated allowed hosts |
| `POSTGRES_DB` | `room_booking` | Database name |
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_HOST` | `db` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `ACCESS_TOKEN_LIFETIME_DAYS` | `1` | JWT access token lifetime (days) |
| `REFRESH_TOKEN_LIFETIME_DAYS` | `7` | JWT refresh token lifetime (days) |
