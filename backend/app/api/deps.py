"""FastAPI dependencies for dependency injection."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.auth_service import AuthService, InvalidTokenError
from app.application.services.document_service import DocumentService
from app.config import get_settings
from app.database import get_db
from app.domain.models.user import User
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.services.pdf_service import PdfService
from app.infrastructure.services.storage_service import StorageService

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """
    Dependency to get AuthService instance.
    
    Args:
        session: Database session
        
    Returns:
        AuthService: Authentication service instance
    """
    return AuthService(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        session: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Decode token
        token = credentials.credentials
        payload = AuthService.decode_token(token)
        
        # Verify token type
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
        
        # Get user ID from token
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenError("Token missing user ID")
        
        user_id = UUID(user_id_str)
        
        # Get user from database
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if account is locked
        if user.is_locked():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked",
            )
        
        return user
        
    except InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError as e:
        logger.warning(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current authenticated admin user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    session: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Dependency to optionally get current user (for endpoints that work with or without auth).
    
    Args:
        credentials: Optional HTTP authorization credentials
        session: Database session
        
    Returns:
        Optional[User]: Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        # Use the regular get_current_user logic
        token = credentials.credentials
        payload = AuthService.decode_token(token)
        
        if payload.get("type") != "access":
            return None
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        
        user_id = UUID(user_id_str)
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        
        return user if user and not user.is_locked() else None
        
    except Exception:
        return None


def get_storage_service() -> StorageService:
    """
    Dependency to get StorageService instance.
    
    Returns:
        StorageService: Storage service instance
    """
    settings = get_settings()
    return StorageService(
        bucket_name=settings.s3_bucket_name,
        region=settings.s3_region,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        endpoint_url=settings.s3_endpoint_url,
    )


def get_pdf_service() -> PdfService:
    """
    Dependency to get PdfService instance.
    
    Returns:
        PdfService: PDF service instance
    """
    return PdfService()


async def get_document_service(
    session: AsyncSession = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
    pdf_service: PdfService = Depends(get_pdf_service),
) -> DocumentService:
    """
    Dependency to get DocumentService instance.
    
    Args:
        session: Database session
        storage_service: Storage service
        pdf_service: PDF service
        
    Returns:
        DocumentService: Document service instance
    """
    document_repository = DocumentRepository(session)
    return DocumentService(
        document_repository=document_repository,
        storage_service=storage_service,
        pdf_service=pdf_service,
    )
