"""User domain model with business logic."""
import re
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class User:
    """
    User domain model representing a user account.
    
    Encapsulates user data and business logic for authentication and profile management.
    """

    def __init__(
        self,
        user_id: UUID,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        role: str = "user",
        company: Optional[str] = None,
        phone: Optional[str] = None,
        email_verified: bool = False,
        account_locked: bool = False,
        locked_until: Optional[datetime] = None,
        failed_login_attempts: int = 0,
        last_failed_login: Optional[datetime] = None,
        last_login_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        deleted_at: Optional[datetime] = None,
    ):
        """Initialize User domain model."""
        self.user_id = user_id
        self.email = email
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.company = company
        self.phone = phone
        self.email_verified = email_verified
        self.account_locked = account_locked
        self.locked_until = locked_until
        self.failed_login_attempts = failed_login_attempts
        self.last_failed_login = last_failed_login
        self.last_login_at = last_login_at
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.deleted_at = deleted_at

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email is valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_password_strength(password: str, min_length: int = 12) -> tuple[bool, Optional[str]]:
        """
        Validate password meets security requirements.
        
        Args:
            password: Password to validate
            min_length: Minimum password length
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        # Check against common passwords (simplified)
        common_passwords = [
            "password", "123456", "qwerty", "admin", "letmein",
            "welcome", "monkey", "dragon", "master", "sunshine"
        ]
        if password.lower() in common_passwords:
            return False, "Password is too common"
        
        return True, None

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using Argon2.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches
        """
        return pwd_context.verify(password, self.password_hash)

    def is_locked(self) -> bool:
        """
        Check if account is currently locked.
        
        Returns:
            bool: True if account is locked
        """
        if not self.account_locked:
            return False
        
        if self.locked_until and datetime.utcnow() >= self.locked_until:
            # Lock has expired
            return False
        
        return True

    def record_failed_login(self, max_attempts: int = 5, lockout_minutes: int = 30) -> None:
        """
        Record a failed login attempt and lock account if threshold exceeded.
        
        Args:
            max_attempts: Maximum failed attempts before lockout
            lockout_minutes: Duration of lockout in minutes
        """
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
        
        if self.failed_login_attempts >= max_attempts:
            self.account_locked = True
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)

    def record_successful_login(self) -> None:
        """Record a successful login and reset failed attempts."""
        self.last_login_at = datetime.utcnow()
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked = False
        self.locked_until = None

    def unlock_account(self) -> None:
        """Unlock the account and reset failed login attempts."""
        self.account_locked = False
        self.locked_until = None
        self.failed_login_attempts = 0
        self.last_failed_login = None

    def verify_email_address(self) -> None:
        """Mark email as verified."""
        self.email_verified = True

    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> None:
        """
        Update user profile information.
        
        Args:
            first_name: New first name
            last_name: New last name
            company: New company
            phone: New phone number
        """
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if company is not None:
            self.company = company
        if phone is not None:
            self.phone = phone
        
        self.updated_at = datetime.utcnow()

    def change_password(self, new_password: str) -> None:
        """
        Change user password.
        
        Args:
            new_password: New plain text password
        """
        self.password_hash = User.hash_password(new_password)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "company": self.company,
            "phone": self.phone,
            "role": self.role,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
