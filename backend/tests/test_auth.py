"""Tests for authentication service and endpoints."""
import pytest
from uuid import uuid4

from app.application.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    EmailNotVerifiedError,
    AccountLockedError,
    InvalidTokenError,
)
from app.domain.models.user import User
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.token_repository import TokenRepository


class TestUserRegistration:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, test_db, sample_user_data, mock_email_service):
        """Test successful user registration."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        user = await auth_service.register_user(**sample_user_data)
        
        assert user.user_id is not None
        assert user.email == sample_user_data["email"].lower()
        assert user.first_name == sample_user_data["first_name"]
        assert user.last_name == sample_user_data["last_name"]
        assert user.email_verified is False
        assert user.verify_password(sample_user_data["password"]) is True

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, test_db, sample_user_data, mock_email_service):
        """Test registration with duplicate email fails."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        # Register first user
        await auth_service.register_user(**sample_user_data)
        
        # Try to register again with same email
        with pytest.raises(EmailAlreadyExistsError):
            await auth_service.register_user(**sample_user_data)

    @pytest.mark.asyncio
    async def test_register_weak_password(self, test_db, sample_user_data, mock_email_service):
        """Test registration with weak password fails."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        sample_user_data["password"] = "weak"
        
        with pytest.raises(ValueError, match="at least 12 characters"):
            await auth_service.register_user(**sample_user_data)

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, test_db, sample_user_data, mock_email_service):
        """Test registration with invalid email fails."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        sample_user_data["email"] = "not-an-email"
        
        with pytest.raises(ValueError, match="Invalid email format"):
            await auth_service.register_user(**sample_user_data)


class TestUserLogin:
    """Tests for user login."""

    @pytest.mark.asyncio
    async def test_login_success(self, test_db, sample_user_data, mock_email_service):
        """Test successful login."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        # Register and verify user
        user = await auth_service.register_user(**sample_user_data)
        user.verify_email_address()
        user_repo = UserRepository(test_db)
        await user_repo.update(user)
        
        # Login
        access_token, refresh_token, logged_in_user = await auth_service.login(
            email=sample_user_data["email"],
            password=sample_user_data["password"],
        )
        
        assert access_token is not None
        assert refresh_token is not None
        assert logged_in_user.user_id == user.user_id
        assert logged_in_user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, test_db, sample_user_data, mock_email_service):
        """Test login with wrong password fails."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        # Register and verify user
        user = await auth_service.register_user(**sample_user_data)
        user.verify_email_address()
        user_repo = UserRepository(test_db)
        await user_repo.update(user)
        
        # Try login with wrong password
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(
                email=sample_user_data["email"],
                password="WrongPassword123!",
            )

    @pytest.mark.asyncio
    async def test_login_unverified_email(self, test_db, sample_user_data, mock_email_service):
        """Test login with unverified email fails."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        # Register user (not verified)
        await auth_service.register_user(**sample_user_data)
        
        # Try to login
        with pytest.raises(EmailNotVerifiedError):
            await auth_service.login(
                email=sample_user_data["email"],
                password=sample_user_data["password"],
            )

    @pytest.mark.asyncio
    async def test_login_account_lockout(self, test_db, sample_user_data, mock_email_service):
        """Test account locks after failed login attempts."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        # Register and verify user
        user = await auth_service.register_user(**sample_user_data)
        user.verify_email_address()
        user_repo = UserRepository(test_db)
        await user_repo.update(user)
        
        # Attempt multiple failed logins
        for _ in range(5):
            try:
                await auth_service.login(
                    email=sample_user_data["email"],
                    password="WrongPassword123!",
                )
            except InvalidCredentialsError:
                pass
        
        # Next attempt should trigger account lock
        with pytest.raises(AccountLockedError):
            await auth_service.login(
                email=sample_user_data["email"],
                password=sample_user_data["password"],
            )


class TestEmailVerification:
    """Tests for email verification."""

    @pytest.mark.asyncio
    async def test_verify_email_success(self, test_db, sample_user_data, mock_email_service):
        """Test successful email verification."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        # Register user
        user = await auth_service.register_user(**sample_user_data)
        
        # Get verification token
        token_repo = TokenRepository(test_db)
        token = await token_repo.create_verification_token(user.user_id)
        
        # Verify email
        verified_user = await auth_service.verify_email(token)
        
        assert verified_user.email_verified is True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, test_db, mock_email_service):
        """Test email verification with invalid token fails."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        with pytest.raises(InvalidTokenError):
            await auth_service.verify_email("invalid-token")


class TestPasswordReset:
    """Tests for password reset."""

    @pytest.mark.asyncio
    async def test_password_reset_success(self, test_db, sample_user_data, mock_email_service):
        """Test successful password reset."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        # Register user
        user = await auth_service.register_user(**sample_user_data)
        
        # Request password reset
        await auth_service.request_password_reset(user.email)
        
        # Get reset token
        token_repo = TokenRepository(test_db)
        token = await token_repo.create_reset_token(user.user_id)
        
        # Reset password
        new_password = "NewSecurePassword123!"
        await auth_service.reset_password(token, new_password)
        
        # Verify new password works
        user_repo = UserRepository(test_db)
        updated_user = await user_repo.get_by_id(user.user_id)
        assert updated_user.verify_password(new_password) is True

    @pytest.mark.asyncio
    async def test_password_reset_invalid_token(self, test_db, mock_email_service):
        """Test password reset with invalid token fails."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        with pytest.raises(InvalidTokenError):
            await auth_service.reset_password("invalid-token", "NewPassword123!")


class TestTokenRefresh:
    """Tests for token refresh."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, test_db, sample_user_data, mock_email_service):
        """Test successful token refresh."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        # Register and verify user
        user = await auth_service.register_user(**sample_user_data)
        user.verify_email_address()
        user_repo = UserRepository(test_db)
        await user_repo.update(user)
        
        # Login to get tokens
        _, refresh_token, _ = await auth_service.login(
            email=sample_user_data["email"],
            password=sample_user_data["password"],
        )
        
        # Refresh access token
        new_access_token = await auth_service.refresh_access_token(refresh_token)
        
        assert new_access_token is not None
        assert new_access_token != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, test_db, mock_email_service):
        """Test token refresh with invalid token fails."""
        auth_service = AuthService(test_db, email_service=mock_email_service)
        
        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_access_token("invalid-token")


class TestUserDomain:
    """Tests for User domain model."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        hashed = User.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0

    def test_password_validation(self):
        """Test password strength validation."""
        # Valid password
        is_valid, error = User.validate_password_strength("SecurePassword123!")
        assert is_valid is True
        assert error is None
        
        # Too short
        is_valid, error = User.validate_password_strength("Short1!")
        assert is_valid is False
        assert "at least 12 characters" in error
        
        # No uppercase
        is_valid, error = User.validate_password_strength("securepassword123!")
        assert is_valid is False
        assert "uppercase" in error
        
        # No lowercase
        is_valid, error = User.validate_password_strength("SECUREPASSWORD123!")
        assert is_valid is False
        assert "lowercase" in error
        
        # No number
        is_valid, error = User.validate_password_strength("SecurePassword!")
        assert is_valid is False
        assert "number" in error

    def test_email_validation(self):
        """Test email format validation."""
        assert User.validate_email("test@example.com") is True
        assert User.validate_email("user.name+tag@example.co.uk") is True
        assert User.validate_email("invalid-email") is False
        assert User.validate_email("@example.com") is False
        assert User.validate_email("user@") is False

    def test_account_lockout(self):
        """Test account lockout logic."""
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash=User.hash_password("Password123!"),
            first_name="Test",
            last_name="User",
        )
        
        assert user.is_locked() is False
        
        # Record failed attempts
        for _ in range(5):
            user.record_failed_login(max_attempts=5, lockout_minutes=30)
        
        assert user.is_locked() is True
        assert user.account_locked is True
        assert user.locked_until is not None
        
        # Unlock account
        user.unlock_account()
        assert user.is_locked() is False
        assert user.failed_login_attempts == 0

    def test_successful_login_resets_attempts(self):
        """Test successful login resets failed attempts."""
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash=User.hash_password("Password123!"),
            first_name="Test",
            last_name="User",
        )
        
        # Record some failed attempts
        user.record_failed_login()
        user.record_failed_login()
        assert user.failed_login_attempts == 2
        
        # Successful login
        user.record_successful_login()
        assert user.failed_login_attempts == 0
        assert user.last_login_at is not None
