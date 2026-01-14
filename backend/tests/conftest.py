"""Pytest configuration and fixtures."""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base
from app.config import get_settings
from app.infrastructure.services.email_service import EmailService

settings = get_settings()

# Use test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/docusign_clone_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.
    
    Creates all tables before test and drops them after.
    """
    # Create test engine
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Provide session
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for tests."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
        "company": "Test Company",
        "phone": "+1234567890",
    }


@pytest.fixture
def mock_email_service() -> EmailService:
    """Mock email service for tests."""
    mock_service = MagicMock(spec=EmailService)
    mock_service.send_verification_email = AsyncMock(return_value=True)
    mock_service.send_password_reset_email = AsyncMock(return_value=True)
    mock_service.send_account_lockout_email = AsyncMock(return_value=True)
    return mock_service
