"""Pydantic schemas for authentication API."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr
    password: str = Field(..., min_length=12)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        from app.domain.models.user import User
        
        is_valid, error = User.validate_password_strength(v)
        if not is_valid:
            raise ValueError(error)
        return v


class RegisterResponse(BaseModel):
    """User registration response schema."""

    user_id: UUID
    email: str
    first_name: str
    last_name: str
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr
    password: str


class UserProfile(BaseModel):
    """User profile schema."""

    user_id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    company: Optional[str]
    phone: Optional[str]
    role: str
    email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """User login response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserProfile


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema."""

    access_token: str
    token_type: str = "bearer"


class VerifyEmailRequest(BaseModel):
    """Email verification request schema."""

    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request schema."""

    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request schema."""

    token: str
    new_password: str = Field(..., min_length=12)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        from app.domain.models.user import User
        
        is_valid, error = User.validate_password_strength(v)
        if not is_valid:
            raise ValueError(error)
        return v


class UpdateProfileRequest(BaseModel):
    """Update user profile request schema."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)


class SuccessResponse(BaseModel):
    """Generic success response schema."""

    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    error_code: Optional[str] = None
