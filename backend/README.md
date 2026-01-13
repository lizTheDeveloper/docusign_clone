# DocuSign Clone - Backend

Python backend for the DocuSign Clone electronic signature platform.

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL with SQLAlchemy (async)
- **Authentication:** JWT with passlib/argon2
- **Testing:** pytest
- **Migrations:** Alembic

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Setup Database

```bash
# Create PostgreSQL database
createdb docusign_clone

# Run migrations
alembic upgrade head
```

### 5. Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at http://localhost:8000
API documentation at http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── domain/              # Domain models and business logic
│   │   ├── __init__.py
│   │   └── models/
│   │       └── user.py
│   ├── infrastructure/      # Data access and external services
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   │   └── user_repository.py
│   │   └── services/
│   │       └── email_service.py
│   ├── application/         # Application services and use cases
│   │   ├── __init__.py
│   │   └── services/
│   │       └── auth_service.py
│   ├── api/                 # HTTP layer
│   │   ├── __init__.py
│   │   ├── deps.py         # Dependencies
│   │   ├── middleware.py   # Middleware
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           └── auth.py
│   └── schemas/            # Pydantic schemas
│       ├── __init__.py
│       └── auth.py
├── alembic/                # Database migrations
├── tests/                  # Test suite
└── requirements.txt
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/verify-email` - Verify email
- `POST /api/v1/auth/resend-verification` - Resend verification email
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update user profile

Full API documentation available at `/docs` when server is running.
