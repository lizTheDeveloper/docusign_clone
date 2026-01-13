"""Token repository for managing authentication tokens."""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import (
    EmailVerificationModel,
    PasswordResetModel,
    RefreshTokenModel,
)


class TokenRepository:
    """Repository for managing authentication tokens."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async database session
        """
        self.session = session

    # Email Verification Tokens

    async def create_verification_token(
        self, user_id: UUID, expires_hours: int = 24
    ) -> str:
        """
        Create email verification token.
        
        Args:
            user_id: User ID
            expires_hours: Token expiration in hours
            
        Returns:
            str: Verification token
        """
        token = secrets.token_urlsafe(48)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        db_token = EmailVerificationModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        
        self.session.add(db_token)
        await self.session.flush()
        
        return token

    async def verify_email_token(self, token: str) -> Optional[UUID]:
        """
        Verify email token and mark as used.
        
        Args:
            token: Verification token
            
        Returns:
            Optional[UUID]: User ID if token is valid, None otherwise
        """
        stmt = select(EmailVerificationModel).where(
            EmailVerificationModel.token == token,
            EmailVerificationModel.verified_at.is_(None),
            EmailVerificationModel.expires_at > datetime.utcnow(),
        )
        result = await self.session.execute(stmt)
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            return None
        
        # Mark as verified
        db_token.verified_at = datetime.utcnow()
        await self.session.flush()
        
        return db_token.user_id

    async def delete_verification_tokens(self, user_id: UUID) -> None:
        """
        Delete all verification tokens for a user.
        
        Args:
            user_id: User ID
        """
        stmt = delete(EmailVerificationModel).where(
            EmailVerificationModel.user_id == user_id
        )
        await self.session.execute(stmt)
        await self.session.flush()

    # Password Reset Tokens

    async def create_reset_token(
        self, user_id: UUID, expires_hours: int = 1
    ) -> str:
        """
        Create password reset token.
        
        Args:
            user_id: User ID
            expires_hours: Token expiration in hours
            
        Returns:
            str: Reset token
        """
        token = secrets.token_urlsafe(48)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        db_token = PasswordResetModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        
        self.session.add(db_token)
        await self.session.flush()
        
        return token

    async def validate_reset_token(self, token: str) -> Optional[UUID]:
        """
        Validate password reset token and mark as used.
        
        Args:
            token: Reset token
            
        Returns:
            Optional[UUID]: User ID if token is valid, None otherwise
        """
        stmt = select(PasswordResetModel).where(
            PasswordResetModel.token == token,
            PasswordResetModel.used_at.is_(None),
            PasswordResetModel.expires_at > datetime.utcnow(),
        )
        result = await self.session.execute(stmt)
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            return None
        
        # Mark as used
        db_token.used_at = datetime.utcnow()
        await self.session.flush()
        
        return db_token.user_id

    async def delete_reset_tokens(self, user_id: UUID) -> None:
        """
        Delete all reset tokens for a user.
        
        Args:
            user_id: User ID
        """
        stmt = delete(PasswordResetModel).where(
            PasswordResetModel.user_id == user_id
        )
        await self.session.execute(stmt)
        await self.session.flush()

    # Refresh Tokens

    async def create_refresh_token(
        self, user_id: UUID, token: str, expires_days: int = 30
    ) -> None:
        """
        Store refresh token.
        
        Args:
            user_id: User ID
            token: Refresh token (will be hashed)
            expires_days: Token expiration in days
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        db_token = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        
        self.session.add(db_token)
        await self.session.flush()

    async def validate_refresh_token(self, token: str) -> Optional[UUID]:
        """
        Validate refresh token.
        
        Args:
            token: Refresh token
            
        Returns:
            Optional[UUID]: User ID if token is valid, None otherwise
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.revoked_at.is_(None),
            RefreshTokenModel.expires_at > datetime.utcnow(),
        )
        result = await self.session.execute(stmt)
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            return None
        
        # Update last used timestamp
        db_token.last_used_at = datetime.utcnow()
        await self.session.flush()
        
        return db_token.user_id

    async def revoke_refresh_token(self, token: str) -> None:
        """
        Revoke a refresh token.
        
        Args:
            token: Refresh token to revoke
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .values(revoked_at=datetime.utcnow())
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            user_id: User ID
        """
        stmt = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.utcnow())
        )
        await self.session.execute(stmt)
        await self.session.flush()
