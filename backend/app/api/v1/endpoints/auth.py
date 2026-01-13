"""Authentication endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_service, get_current_user
from app.application.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    EmailNotVerifiedError,
    AccountLockedError,
    InvalidTokenError,
)
from app.database import get_db
from app.domain.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    SuccessResponse,
    UserProfile,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Validation error"},
        409: {"description": "Email already registered"},
    },
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """
    Register a new user account.
    
    - **email**: Valid email address (required)
    - **password**: Strong password (min 12 chars, uppercase, lowercase, number) (required)
    - **first_name**: User's first name (required)
    - **last_name**: User's last name (required)
    - **company**: Company name (optional)
    - **phone**: Phone number (optional)
    
    Returns user information with email_verified=False.
    Sends verification email to the provided address.
    """
    try:
        user = await auth_service.register_user(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            company=request.company,
            phone=request.phone,
        )
        
        return RegisterResponse(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            email_verified=user.email_verified,
            created_at=user.created_at,
        )
        
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        403: {"description": "Email not verified or account locked"},
    },
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """
    Authenticate user and receive JWT tokens.
    
    - **email**: User's email address (required)
    - **password**: User's password (required)
    
    Returns access token (expires in 1 hour) and refresh token (expires in 30 days).
    """
    try:
        access_token, refresh_token, user = await auth_service.login(
            email=request.email,
            password=request.password,
        )
        
        user_profile = UserProfile(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            company=user.company,
            phone=user.phone,
            role=user.role,
            email_verified=user.email_verified,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_profile,
        )
        
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in",
        )
    except AccountLockedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account locked due to too many failed login attempts",
        )
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RefreshTokenResponse:
    """
    Generate new access token using refresh token.
    
    - **refresh_token**: Valid refresh token (required)
    
    Returns new access token.
    """
    try:
        access_token = await auth_service.refresh_access_token(request.refresh_token)
        
        return RefreshTokenResponse(access_token=access_token)
        
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post(
    "/verify-email",
    response_model=SuccessResponse,
    summary="Verify email address",
    responses={
        200: {"description": "Email verified successfully"},
        400: {"description": "Invalid or expired token"},
    },
)
async def verify_email(
    request: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    """
    Verify user email with verification token.
    
    - **token**: Email verification token from email link (required)
    
    Marks the user's email as verified.
    """
    try:
        await auth_service.verify_email(request.token)
        
        return SuccessResponse(message="Email verified successfully")
        
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed",
        )


@router.post(
    "/resend-verification",
    response_model=SuccessResponse,
    summary="Resend verification email",
    responses={
        200: {"description": "Verification email sent"},
        400: {"description": "Email already verified"},
    },
)
async def resend_verification(
    request: ResendVerificationRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    """
    Resend email verification.
    
    - **email**: User's email address (required)
    
    Sends a new verification email with a fresh token.
    """
    try:
        await auth_service.resend_verification_email(request.email)
        
        return SuccessResponse(message="Verification email sent")
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Resend verification failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email",
        )


@router.post(
    "/forgot-password",
    response_model=SuccessResponse,
    summary="Request password reset",
    responses={
        200: {"description": "Password reset email sent if account exists"},
    },
)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    """
    Request password reset email.
    
    - **email**: User's email address (required)
    
    Always returns success to prevent email enumeration.
    If account exists, sends password reset email.
    """
    try:
        await auth_service.request_password_reset(request.email)
        
        # Always return success (security: don't reveal if email exists)
        return SuccessResponse(
            message="If an account exists, a password reset email has been sent"
        )
        
    except Exception as e:
        logger.error(f"Password reset request failed: {str(e)}", exc_info=True)
        # Still return success to prevent email enumeration
        return SuccessResponse(
            message="If an account exists, a password reset email has been sent"
        )


@router.post(
    "/reset-password",
    response_model=SuccessResponse,
    summary="Reset password",
    responses={
        200: {"description": "Password reset successfully"},
        400: {"description": "Invalid token or weak password"},
    },
)
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    """
    Reset password using reset token.
    
    - **token**: Password reset token from email (required)
    - **new_password**: New password (required, same strength requirements as registration)
    
    Resets password and invalidates all existing sessions.
    """
    try:
        await auth_service.reset_password(request.token, request.new_password)
        
        return SuccessResponse(message="Password reset successfully")
        
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed",
        )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="Logout user",
    responses={
        200: {"description": "Logged out successfully"},
    },
)
async def logout(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    """
    Logout user by revoking refresh token.
    
    - **refresh_token**: User's refresh token (required)
    
    Invalidates the refresh token. Access token will expire naturally.
    """
    try:
        await auth_service.logout(request.refresh_token)
        
        return SuccessResponse(message="Logged out successfully")
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}", exc_info=True)
        # Return success anyway - logout should be idempotent
        return SuccessResponse(message="Logged out successfully")


# User profile endpoints

@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user profile",
    responses={
        200: {"description": "User profile retrieved"},
        401: {"description": "Not authenticated"},
    },
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserProfile:
    """
    Get current authenticated user's profile.
    
    Requires valid JWT access token in Authorization header.
    """
    return UserProfile(
        user_id=current_user.user_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        company=current_user.company,
        phone=current_user.phone,
        role=current_user.role,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )


@router.patch(
    "/me",
    response_model=UserProfile,
    summary="Update user profile",
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserProfile:
    """
    Update current user's profile information.
    
    - **first_name**: New first name (optional)
    - **last_name**: New last name (optional)
    - **company**: New company (optional)
    - **phone**: New phone number (optional)
    
    Only provided fields will be updated.
    Requires valid JWT access token in Authorization header.
    """
    try:
        from app.infrastructure.repositories.user_repository import UserRepository
        
        # Update user profile
        current_user.update_profile(
            first_name=request.first_name,
            last_name=request.last_name,
            company=request.company,
            phone=request.phone,
        )
        
        # Save to database
        user_repo = UserRepository(session)
        updated_user = await user_repo.update(current_user)
        
        return UserProfile(
            user_id=updated_user.user_id,
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            full_name=updated_user.full_name,
            company=updated_user.company,
            phone=updated_user.phone,
            role=updated_user.role,
            email_verified=updated_user.email_verified,
            created_at=updated_user.created_at,
            last_login_at=updated_user.last_login_at,
        )
        
    except Exception as e:
        logger.error(f"Profile update failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed",
        )
