# Test Troubleshooting Guide

## Common Test Issues and Solutions

### Issue 1: Database Connection Failed

**Error:** `OperationalError: could not connect to server`

**Solutions:**
```bash
# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql # Linux

# Verify it's running
pg_isready

# Create test database if needed
createdb -U postgres docusign_clone_test
```

### Issue 2: Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solutions:**
```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make sure pytest is installed
pip install pytest pytest-asyncio pytest-cov
```

### Issue 3: Async Test Issues

**Error:** `RuntimeError: Event loop is closed`

**Solution:** The `conftest.py` already handles this with the `event_loop` fixture, but if issues persist:
```bash
# Make sure pytest-asyncio is installed
pip install pytest-asyncio

# Check pytest.ini has: asyncio_mode = auto
```

### Issue 4: Email Service Errors

**Error:** Tests fail due to SMTP connection

**Solution:** Tests now use `mock_email_service` fixture, so this shouldn't happen. But if you see SMTP errors:
- Check that tests use the `mock_email_service` fixture
- Verify the mock is properly configured in `conftest.py`

### Issue 5: Database Tables Don't Exist

**Error:** `ProgrammingError: relation "users" does not exist`

**Solutions:**
```bash
# The test fixture should create tables automatically, but if not:
# 1. Drop and recreate test database
dropdb -U postgres docusign_clone_test
createdb -U postgres docusign_clone_test

# 2. Make sure the Base.metadata includes all models
# Check that models are imported in conftest.py
```

### Issue 6: Token/JWT Errors

**Error:** `JWTError` or token validation failures

**Solution:**
- Make sure `.env` file exists with valid JWT_SECRET_KEY
- Check that settings are loading correctly

## Running Specific Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test class
pytest tests/test_auth.py::TestUserRegistration

# Run specific test method
pytest tests/test_auth.py::TestUserRegistration::test_register_user_success

# Run with print statements visible
pytest -v -s

# Run with coverage
pytest --cov=app --cov-report=html

# Run and stop on first failure
pytest -x

# Run only failed tests from last run
pytest --lf
```

## Debugging Tests

### Add breakpoints in tests:
```python
@pytest.mark.asyncio
async def test_something(test_db):
    import pdb; pdb.set_trace()  # Debugger will stop here
    # ... test code
```

### Check test output:
```bash
# Run with maximum verbosity
pytest -vv

# Show print statements
pytest -s

# Show local variables on failure
pytest -l
```

### Check database state during tests:
```python
# In your test, add:
result = await session.execute(select(UserModel))
users = result.scalars().all()
print(f"Users in DB: {len(users)}")
for user in users:
    print(f"  - {user.email}: verified={user.email_verified}")
```

## Expected Test Results

When all tests pass, you should see:
```
tests/test_auth.py::TestUserRegistration::test_register_user_success PASSED
tests/test_auth.py::TestUserRegistration::test_register_duplicate_email PASSED
tests/test_auth.py::TestUserRegistration::test_register_weak_password PASSED
tests/test_auth.py::TestUserRegistration::test_register_invalid_email PASSED
tests/test_auth.py::TestUserLogin::test_login_success PASSED
tests/test_auth.py::TestUserLogin::test_login_invalid_credentials PASSED
tests/test_auth.py::TestUserLogin::test_login_unverified_email PASSED
tests/test_auth.py::TestUserLogin::test_login_account_lockout PASSED
tests/test_auth.py::TestEmailVerification::test_verify_email_success PASSED
tests/test_auth.py::TestEmailVerification::test_verify_email_invalid_token PASSED
tests/test_auth.py::TestPasswordReset::test_password_reset_success PASSED
tests/test_auth.py::TestPasswordReset::test_password_reset_invalid_token PASSED
tests/test_auth.py::TestTokenRefresh::test_refresh_token_success PASSED
tests/test_auth.py::TestTokenRefresh::test_refresh_token_invalid PASSED
tests/test_auth.py::TestUserDomain::test_password_hashing PASSED
tests/test_auth.py::TestUserDomain::test_password_validation PASSED
tests/test_auth.py::TestUserDomain::test_email_validation PASSED
tests/test_auth.py::TestUserDomain::test_account_lockout PASSED
tests/test_auth.py::TestUserDomain::test_successful_login_resets_attempts PASSED

=================== 19 passed in X.XXs ===================
```

## Quick Test Checklist

Before running tests, verify:
- [ ] Virtual environment activated
- [ ] In `backend/` directory
- [ ] PostgreSQL running (`pg_isready`)
- [ ] Test database exists
- [ ] Dependencies installed (`pip list | grep pytest`)
- [ ] `.env` file exists with required settings

## Still Having Issues?

1. Check the full error traceback
2. Verify all imports are correct
3. Make sure database migrations are up to date
4. Try running tests one at a time to isolate the issue
5. Check that the test database is clean (recreate it)

## Contact/Debug

If tests still fail, provide:
1. Full error message and traceback
2. Output of `pytest --version`
3. Output of `python --version`
4. Contents of your `.env` file (redact secrets)
