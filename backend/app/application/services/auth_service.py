"""Authentication service with JWT and business logic."""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID, uuid4

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.domain.models.user import User
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.token_repository import TokenRepository
from app.infrastructure.services.email_service import EmailService
from app.schemas.auth import UserProfile

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Exception for invalid login credentials."""

    pass


class EmailAlreadyExistsError(AuthenticationError):
    """Exception for duplicate email registration."""

    pass


class EmailNotVerifiedError(AuthenticationError):
    """Exception for unverified email login attempt."""

    pass


class AccountLockedError(AuthenticationError):
    """Exception for locked account login attempt."""

    pass


class InvalidTokenError(AuthenticationError):
    """Exception for invalid or expired tokens."""

    pass


class AuthService:
    """
    Authentication service handling registration, login, and token management.
    
    Provides business logic for user authentication with proper security measures.
    """

    def __init__(
        self,
        session: AsyncSession,
        user_repo: Optional[UserRepository] = None,
        token_repo: Optional[TokenRepository] = None,
        email_service: Optional[EmailService] = None,
    ):
        """
        Initialize authentication service.
        
        Args:
            session: Database session
            user_repo: User repository (injected for testing)
            token_repo: Token repository (injected for testing)
            email_service: Email service (injected for testing)
        """
        self.session = session
        self.user_repo = user_repo or UserRepository(session)
        self.token_repo = token_repo or TokenRepository(session)
        self.email_service = email_service or EmailService()

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        company: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> User:
        """
        Register a new user.
        
        Args:
            email: User email address
            password: Plain text password
            first_name: User's first name
            last_name: User's last name
            company: Optional company name
            phone: Optional phone number
            
        Returns:
            User: Created user
            
        Raises:
            EmailAlreadyExistsError: If email already registered
            ValueError: If validation fails
        """
        try:
            # Normalize email
            email = email.lower().strip()

            # Check if email already exists
            if await self.user_repo.email_exists(email):
                logger.warning(f"Registration attempt with existing email: {email}")
                raise EmailAlreadyExistsError("Email already registered")

            # Validate email format
            if not User.validate_email(email):
                raise ValueError("Invalid email format")

            # Validate password strength
            is_valid, error = User.validate_password_strength(
                password, settings.password_min_length
            )
            if not is_valid:
                raise ValueError(error)

            # Create user domain model
            user = User(
                user_id=uuid4(),
                email=email,
                password_hash=User.hash_password(password),
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                company=company.strip() if company else None,
                phone=phone.strip() if phone else None,
                role="user",
                email_verified=False,
            )

            # Persist user
            created_user = await self.user_repo.create(user)

            # Create verification token and send email
            try:
                verification_token = await self.token_repo.create_verification_token(
                    created_user.user_id, settings.verification_token_expire_hours
                )
                await self.email_service.send_verification_email(
                    to_email=created_user.email,
                    token=verification_token,
                    user_name=created_user.full_name,
                )
                logger.info(f"User registered successfully: {created_user.user_id}")
            except Exception as e:
                logger.error(f"Failed to send verification email: {str(e)}", exc_info=True)
                # Don't fail registration if email fails

            return created_user

        except (EmailAlreadyExistsError, ValueError):
            raise
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}", exc_info=True)
            raise

    async def login(self, email: str, password: str) -> Tuple[str, str, User]:
        """
        Authenticate user and generate tokens.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            Tuple[str, str, User]: Access token, refresh token, and user
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            EmailNotVerifiedError: If email not verified
            AccountLockedError: If account is locked
        """
        try:
            # Normalize email
            email = email.lower().strip()

            # Get user
            user = await self.user_repo.get_by_email(email)
            
            if not user:
                logger.warning(f"Login attempt with non-existent email: {email}")
                raise InvalidCredentialsError("Invalid credentials")

            # Check if account is locked
            if user.is_locked():
                logger.warning(f"Login attempt on locked account: {user.user_id}")
                raise AccountLockedError("Account locked due to too many failed attempts")

            # Verify password
            if not user.verify_password(password):
                logger.warning(f"Failed login attempt for user: {user.user_id}")
                
                # Record failed attempt
                user.record_failed_login(
                    max_attempts=settings.max_login_attempts,
                    lockout_minutes=settings.account_lockout_minutes,
                )
                await self.user_repo.update(user)

                # Send lockout email if just locked
                if user.is_locked():
                    try:
                        await self.email_service.send_account_lockout_email(
                            to_email=user.email,
                            user_name=user.full_name,
                            unlock_minutes=settings.account_lockout_minutes,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send lockout email: {str(e)}")

                raise InvalidCredentialsError("Invalid credentials")

            # Check if email is verified
            if not user.email_verified:
                logger.warning(f"Login attempt with unverified email: {user.user_id}")
                raise EmailNotVerifiedError("Please verify your email before logging in")

            # Record successful login
            user.record_successful_login()
            await self.user_repo.update(user)

            # Generate tokens
            access_token = self._create_access_token(user)
            refresh_token = self._create_refresh_token(user)

            # Store refresh token
            await self.token_repo.create_refresh_token(
                user_id=user.user_id,
                token=refresh_token,
                expires_days=settings.refresh_token_expire_days,
            )

            logger.info(f"User logged in successfully: {user.user_id}")
            return access_token, refresh_token, user

        except (InvalidCredentialsError, EmailNotVerifiedError, AccountLockedError):
            raise
        except Exception as e:
            logger.error(f"Login failed: {str(e)}", exc_info=True)
            raise

    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            str: New access token
            
        Raises:
            InvalidTokenError: If refresh token is invalid
        """
        try:
            # Validate refresh token
            user_id = await self.token_repo.validate_refresh_token(refresh_token)
            
            if not user_id:
                raise InvalidTokenError("Invalid or expired refresh token")

            # Get user
            user = await self.user_repo.get_by_id(user_id)
            
            if not user:
                raise InvalidTokenError("User not found")

            # Generate new access token
            access_token = self._create_access_token(user)
            
            logger.info(f"Access token refreshed for user: {user.user_id}")
            return access_token

        except InvalidTokenError:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}", exc_info=True)
            raise InvalidTokenError("Token refresh failed")

    async def verify_email(self, token: str) -> User:
        """
        Verify user email with token.
        
        Args:
            token: Email verification token
            
        Returns:
            User: Verified user
            
        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        try:
            # Validate token
            user_id = await self.token_repo.verify_email_token(token)
            
            if not user_id:
                raise InvalidTokenError("Invalid or expired verification token")

            # Get and update user
            user = await self.user_repo.get_by_id(user_id)
            
            if not user:
                raise InvalidTokenError("User not found")

            user.verify_email_address()
            await self.user_repo.update(user)

            # Clean up used tokens
            await self.token_repo.delete_verification_tokens(user_id)

            logger.info(f"Email verified for user: {user.user_id}")
            return user

        except InvalidTokenError:
            raise
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}", exc_info=True)
            raise

    async def resend_verification_email(self, email: str) -> None:
        """
        Resend email verification.
        
        Args:
            email: User email address
            
        Raises:
            ValueError: If email already verified or not found
        """
        try:
            email = email.lower().strip()
            user = await self.user_repo.get_by_email(email)
            
            if not user:
                # Don't reveal if email exists
                logger.warning(f"Verification resend for non-existent email: {email}")
                return

            if user.email_verified:
                raise ValueError("Email already verified")

            # Create new token
            token = await self.token_repo.create_verification_token(
                user.user_id, settings.verification_token_expire_hours
            )

            # Send email
            await self.email_service.send_verification_email(
                to_email=user.email,
                token=token,
                user_name=user.full_name,
            )

            logger.info(f"Verification email resent to: {user.user_id}")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to resend verification: {str(e)}", exc_info=True)
            raise

    async def request_password_reset(self, email: str) -> None:
        """
        Request password reset email.
        
        Args:
            email: User email address
            
        Note:
            Always returns success to prevent email enumeration
        """
        try:
            email = email.lower().strip()
            user = await self.user_repo.get_by_email(email)
            
            if not user:
                # Don't reveal if email exists
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return

            # Create reset token
            token = await self.token_repo.create_reset_token(
                user.user_id, settings.reset_token_expire_hours
            )

            # Send email
            await self.email_service.send_password_reset_email(
                to_email=user.email,
                token=token,
                user_name=user.full_name,
            )

            logger.info(f"Password reset email sent to: {user.user_id}")

        except Exception as e:
            logger.error(f"Failed to send password reset: {str(e)}", exc_info=True)
            # Don't raise - always appear successful

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset user password with token.
        
        Args:
            token: Password reset token
            new_password: New plain text password
            
        Raises:
            InvalidTokenError: If token is invalid or expired
            ValueError: If password validation fails
        """
        try:
            # Validate token
            user_id = await self.token_repo.validate_reset_token(token)
            
            if not user_id:
                raise InvalidTokenError("Invalid or expired reset token")

            # Validate new password
            is_valid, error = User.validate_password_strength(
                new_password, settings.password_min_length
            )
            if not is_valid:
                raise ValueError(error)

            # Get and update user
            user = await self.user_repo.get_by_id(user_id)
            
            if not user:
                raise InvalidTokenError("User not found")

            user.change_password(new_password)
            await self.user_repo.update(user)

            # Revoke all refresh tokens
            await self.token_repo.revoke_all_user_tokens(user_id)

            # Clean up used reset tokens
            await self.token_repo.delete_reset_tokens(user_id)

            logger.info(f"Password reset successful for user: {user.user_id}")

        except (InvalidTokenError, ValueError):
            raise
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}", exc_info=True)
            raise

    async def logout(self, refresh_token: str) -> None:
        """
        Logout user by revoking refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
        """
        try:
            await self.token_repo.revoke_refresh_token(refresh_token)
            logger.info("User logged out successfully")
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}", exc_info=True)

    def _create_access_token(self, user: User) -> str:
        """
        Create JWT access token.
        
        Args:
            user: User domain model
            
        Returns:
            str: JWT access token
        """
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": str(user.user_id),
            "email": user.email,
            "role": user.role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }
        
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def _create_refresh_token(self, user: User) -> str:
        """
        Create JWT refresh token.
        
        Args:
            user: User domain model
            
        Returns:
            str: JWT refresh token
        """
        expires_delta = timedelta(days=settings.refresh_token_expire_days)
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": str(user.user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        }
        
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            dict: Token payload
            
        Raises:
            InvalidTokenError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except JWTError as e:
            logger.warning(f"Token decode failed: {str(e)}")
            raise InvalidTokenError("Invalid token")
