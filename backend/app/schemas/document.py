"""Document request/response schemas for API validation."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DocumentPageSchema(BaseModel):
    """Schema for document page information."""
    page_number: int = Field(..., ge=1, description="Page number (1-indexed)")
    width: float = Field(..., gt=0, description="Page width in pixels")
    height: float = Field(..., gt=0, description="Page height in pixels")
    thumbnail_url: Optional[str] = Field(None, description="URL to page thumbnail")

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""
    document_id: UUID = Field(..., description="Unique document identifier")
    name: str = Field(..., description="Document name")
    original_filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Number of pages")
    status: str = Field(..., description="Processing status: processing, ready, failed")
    thumbnail_url: Optional[str] = Field(None, description="URL to document thumbnail")
    checksum: str = Field(..., description="SHA-256 checksum")
    uploaded_at: datetime = Field(..., description="Upload timestamp")

    model_config = {"from_attributes": True}


class UserInfoSchema(BaseModel):
    """Minimal user information for document metadata."""
    user_id: UUID
    name: str
    email: str

    model_config = {"from_attributes": True}


class DocumentMetadataResponse(BaseModel):
    """Response schema for detailed document metadata."""
    document_id: UUID
    name: str
    original_filename: str
    file_type: str
    file_size: int
    page_count: int
    status: str
    thumbnail_url: Optional[str] = None
    checksum: str
    uploaded_at: datetime
    uploaded_by: UserInfoSchema
    pages: list[DocumentPageSchema] = []

    model_config = {"from_attributes": True}


class DocumentListItemSchema(BaseModel):
    """Schema for document list item (lightweight)."""
    document_id: UUID
    name: str
    file_size: int
    page_count: int
    uploaded_at: datetime
    thumbnail_url: Optional[str] = None

    model_config = {"from_attributes": True}


class PaginationSchema(BaseModel):
    """Pagination metadata."""
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)
    total_pages: int = Field(..., ge=0)
    total_items: int = Field(..., ge=0)


class DocumentListResponse(BaseModel):
    """Response schema for document list."""
    documents: list[DocumentListItemSchema]
    pagination: PaginationSchema


class PreviewUrlResponse(BaseModel):
    """Response schema for document preview URL."""
    preview_url: str = Field(..., description="Presigned URL for document preview")
    expires_at: datetime = Field(..., description="URL expiration timestamp")


class DocumentDeleteResponse(BaseModel):
    """Response schema for successful document deletion."""
    success: bool = True
    message: str = "Document deleted successfully"


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")


class DocumentValidationError(BaseModel):
    """Document validation error details."""
    detail: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    max_allowed_size: Optional[int] = None
    supported_types: Optional[list[str]] = None
