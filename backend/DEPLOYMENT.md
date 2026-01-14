# Deployment Guide - DocuSign Clone Backend

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis (optional, for production rate limiting)
- SMTP server credentials

## Environment Setup

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb docusign_clone

# Create test database
createdb docusign_clone_test
```

### 2. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Application secret key (generate with `openssl rand -hex 32`)
- `JWT_SECRET_KEY` - JWT signing key (generate with `openssl rand -hex 32`)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` - Email configuration

### 3. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
alembic upgrade head
```

## Running the Application

### Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Using Gunicorn with Uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::TestUserRegistration::test_register_user_success
```

## Docker Deployment

### Build Image

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations and start server
CMD alembic upgrade head && \
    gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: docusign_clone
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/docusign_clone
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - .:/app

volumes:
  postgres_data:
```

## Security Checklist

- [ ] Change default `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Use strong database passwords
- [ ] Enable HTTPS in production
- [ ] Configure CORS with specific origins
- [ ] Set secure cookie flags
- [ ] Enable rate limiting with Redis
- [ ] Configure firewall rules
- [ ] Use environment variables for secrets (never commit .env)
- [ ] Enable database connection encryption (SSL/TLS)
- [ ] Set up monitoring and logging
- [ ] Regular security updates

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Common Issues

### Database Connection Failed

- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL in .env
- Ensure database exists: `psql -l`

### Email Not Sending

- Verify SMTP credentials
- Check firewall/security groups allow SMTP port
- For Gmail, use App Password (not regular password)

### Migration Issues

```bash
# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision>

# Create new migration
alembic revision --autogenerate -m "description"
```

## Performance Tuning

1. **Database Connection Pooling**
   - Adjust `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW`
   - Monitor connection usage

2. **Rate Limiting**
   - Use Redis for distributed rate limiting
   - Adjust limits based on usage patterns

3. **Caching**
   - Implement Redis caching for frequent queries
   - Cache user sessions and tokens

4. **Async Workers**
   - Increase Gunicorn workers based on CPU cores
   - Formula: (2 × CPU cores) + 1

## Backup Strategy

```bash
# Backup database
pg_dump docusign_clone > backup_$(date +%Y%m%d).sql

# Restore database
psql docusign_clone < backup_20260113.sql
```

## Support

For issues and questions:
- Check logs: `tail -f logs/app.log`
- Review error messages in API responses
- Check database logs
- Verify environment configuration
