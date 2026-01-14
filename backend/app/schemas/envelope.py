"""Envelope request/response schemas for API validation."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, field_validator


# ============================================================================
# Recipient Schemas
# ============================================================================

class RecipientCreate(BaseModel):
    """Schema for creating a recipient."""
    name: str = Field(..., min_length=1, max_length=200, description="Recipient name")
    email: EmailStr = Field(..., description="Recipient email address")
    phone: Optional[str] = Field(None, max_length=20, description="Recipient phone number")
    role: str = Field(..., description="Recipient role: signer, cc, approver")
    signing_order: int = Field(1, ge=1, description="Signing order (for sequential workflows)")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        allowed_roles = {'signer', 'cc', 'approver'}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class RecipientUpdate(BaseModel):
    """Schema for updating a recipient."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    signing_order: Optional[int] = Field(None, ge=1)


class RecipientResponse(BaseModel):
    """Schema for recipient in API responses."""
    recipient_id: UUID
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    signing_order: int
    status: str
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecipientWithAccessCode(RecipientResponse):
    """Schema for recipient with access code (only for sender)."""
    access_code: str = Field(..., description="6-digit access code")


# ============================================================================
# Envelope Document Schemas
# ============================================================================

class EnvelopeDocumentCreate(BaseModel):
    """Schema for adding documents to envelope."""
    document_id: UUID = Field(..., description="Document to add to envelope")
    display_order: int = Field(0, ge=0, description="Display order in envelope")


class EnvelopeDocumentResponse(BaseModel):
    """Schema for document in envelope response."""
    document_id: UUID
    name: str
    page_count: int
    display_order: int

    model_config = {"from_attributes": True}


# ============================================================================
# Envelope Schemas
# ============================================================================

class EnvelopeCreate(BaseModel):
    """Schema for creating an envelope."""
    subject: str = Field(..., min_length=1, max_length=200, description="Envelope subject")
    message: Optional[str] = Field(None, max_length=5000, description="Optional message to recipients")
    document_ids: List[UUID] = Field(..., min_items=1, max_items=50, description="Documents to include")
    signing_order: str = Field("parallel", description="Signing order: parallel or sequential")
    expiration_days: int = Field(30, ge=1, le=365, description="Days until envelope expires")
    recipients: Optional[List[RecipientCreate]] = Field(None, description="Recipients (can be added later)")

    @field_validator('signing_order')
    @classmethod
    def validate_signing_order(cls, v):
        allowed_orders = {'parallel', 'sequential'}
        if v not in allowed_orders:
            raise ValueError(f"Signing order must be one of: {', '.join(allowed_orders)}")
        return v

    @field_validator('document_ids')
    @classmethod
    def validate_document_ids_unique(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Document IDs must be unique")
        return v


class EnvelopeUpdate(BaseModel):
    """Schema for updating an envelope (only in draft status)."""
    subject: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, max_length=5000)
    signing_order: Optional[str] = None
    expiration_days: Optional[int] = Field(None, ge=1, le=365)

    @field_validator('signing_order')
    @classmethod
    def validate_signing_order(cls, v):
        if v is not None:
            allowed_orders = {'parallel', 'sequential'}
            if v not in allowed_orders:
                raise ValueError(f"Signing order must be one of: {', '.join(allowed_orders)}")
        return v


class EnvelopeSend(BaseModel):
    """Schema for sending an envelope."""
    pass  # No additional data needed; action is implicit


class EnvelopeVoid(BaseModel):
    """Schema for voiding an envelope."""
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for voiding")


class EnvelopeReminder(BaseModel):
    """Schema for sending reminders."""
    recipient_ids: Optional[List[UUID]] = Field(None, description="Specific recipients (None = all pending)")
    custom_message: Optional[str] = Field(None, max_length=1000, description="Custom reminder message")


class EnvelopeSender(BaseModel):
    """Schema for envelope sender information."""
    user_id: UUID
    name: str
    email: str

    model_config = {"from_attributes": True}


class EnvelopeResponse(BaseModel):
    """Schema for envelope in API responses."""
    envelope_id: UUID
    subject: str
    message: Optional[str] = None
    status: str
    signing_order: str
    expiration_days: int
    expires_at: Optional[datetime] = None
    void_reason: Optional[str] = None
    sender: EnvelopeSender
    documents: List[EnvelopeDocumentResponse]
    recipients: List[RecipientResponse]
    created_at: datetime
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    voided_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnvelopeResponseWithAccessCodes(BaseModel):
    """Schema for envelope with access codes (only for sender)."""
    envelope_id: UUID
    subject: str
    message: Optional[str] = None
    status: str
    signing_order: str
    expiration_days: int
    expires_at: Optional[datetime] = None
    void_reason: Optional[str] = None
    sender: EnvelopeSender
    documents: List[EnvelopeDocumentResponse]
    recipients: List[RecipientWithAccessCode]
    created_at: datetime
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    voided_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnvelopeSummary(BaseModel):
    """Schema for envelope summary in list views."""
    envelope_id: UUID
    subject: str
    status: str
    signing_order: str
    sender: EnvelopeSender
    document_count: int
    recipient_count: int
    completed_recipient_count: int
    created_at: datetime
    sent_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EnvelopeListResponse(BaseModel):
    """Schema for paginated envelope list."""
    envelopes: List[EnvelopeSummary]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# Signing Order Management
# ============================================================================

class SigningOrderUpdate(BaseModel):
    """Schema for updating signing order."""
    recipient_orders: List[dict] = Field(
        ...,
        description="List of {recipient_id, signing_order} mappings"
    )

    @field_validator('recipient_orders')
    @classmethod
    def validate_recipient_orders(cls, v):
        if not v:
            raise ValueError("At least one recipient order must be provided")
        
        # Check for required fields
        for item in v:
            if 'recipient_id' not in item or 'signing_order' not in item:
                raise ValueError("Each item must have 'recipient_id' and 'signing_order'")
            
            # Validate signing order is positive
            if item['signing_order'] < 1:
                raise ValueError("Signing order must be at least 1")
        
        return v


# ============================================================================
# Recipient Access Schemas (for signing interface)
# ============================================================================

class RecipientAccessRequest(BaseModel):
    """Schema for recipient to access envelope."""
    access_code: str = Field(..., min_length=6, max_length=6, description="6-digit access code")


class RecipientDecline(BaseModel):
    """Schema for recipient declining to sign."""
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for declining")
