"""User repository for data access."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User
from app.infrastructure.models import UserModel


class UserRepository:
    """
    Repository for user data access.
    
    Provides abstraction layer between domain models and database models.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async database session
        """
        self.session = session

    async def create(self, user: User) -> User:
        """
        Create a new user in the database.
        
        Args:
            user: User domain model
            
        Returns:
            User: Created user with generated ID
        """
        db_user = UserModel(
            user_id=user.user_id,
            email=user.email,
            password_hash=user.password_hash,
            first_name=user.first_name,
            last_name=user.last_name,
            company=user.company,
            phone=user.phone,
            role=user.role,
            email_verified=user.email_verified,
        )
        
        self.session.add(db_user)
        await self.session.flush()
        await self.session.refresh(db_user)
        
        return self._to_domain(db_user)

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        stmt = select(UserModel).where(
            UserModel.user_id == user_id,
            UserModel.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        return self._to_domain(db_user) if db_user else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: Email address
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        stmt = select(UserModel).where(
            UserModel.email == email.lower(),
            UserModel.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        return self._to_domain(db_user) if db_user else None

    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.
        
        Args:
            email: Email address
            
        Returns:
            bool: True if email exists
        """
        user = await self.get_by_email(email)
        return user is not None

    async def update(self, user: User) -> User:
        """
        Update user in the database.
        
        Args:
            user: User domain model with updated data
            
        Returns:
            User: Updated user
        """
        stmt = (
            update(UserModel)
            .where(UserModel.user_id == user.user_id)
            .values(
                email=user.email,
                password_hash=user.password_hash,
                first_name=user.first_name,
                last_name=user.last_name,
                company=user.company,
                phone=user.phone,
                role=user.role,
                email_verified=user.email_verified,
                account_locked=user.account_locked,
                locked_until=user.locked_until,
                failed_login_attempts=user.failed_login_attempts,
                last_failed_login=user.last_failed_login,
                last_login_at=user.last_login_at,
                updated_at=datetime.utcnow(),
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()
        
        # Get updated user
        updated_user = await self.get_by_id(user.user_id)
        if not updated_user:
            raise ValueError(f"User {user.user_id} not found after update")
        return updated_user

    async def delete(self, user_id: UUID) -> None:
        """
        Soft delete user by setting deleted_at timestamp.
        
        Args:
            user_id: User ID to delete
        """
        stmt = (
            update(UserModel)
            .where(UserModel.user_id == user_id)
            .values(deleted_at=datetime.utcnow())
        )
        await self.session.execute(stmt)
        await self.session.flush()

    def _to_domain(self, db_user: UserModel) -> User:
        """
        Convert database model to domain model.
        
        Args:
            db_user: Database user model
            
        Returns:
            User: Domain user model
        """
        return User(
            user_id=db_user.user_id,
            email=db_user.email,
            password_hash=db_user.password_hash,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            company=db_user.company,
            phone=db_user.phone,
            role=db_user.role,
            email_verified=db_user.email_verified,
            account_locked=db_user.account_locked,
            locked_until=db_user.locked_until,
            failed_login_attempts=db_user.failed_login_attempts,
            last_failed_login=db_user.last_failed_login,
            last_login_at=db_user.last_login_at,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            deleted_at=db_user.deleted_at,
        )
