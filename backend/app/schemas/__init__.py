"""Schema package for request/response validation."""
from .auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenRefreshRequest,
    UserProfileResponse,
)
from .document import (
    DocumentUploadResponse,
    DocumentMetadataResponse,
    DocumentListResponse,
    DocumentPageSchema,
)
from .envelope import (
    EnvelopeCreate,
    EnvelopeUpdate,
    EnvelopeSend,
    EnvelopeVoid,
    EnvelopeReminder,
    EnvelopeResponse,
    EnvelopeResponseWithAccessCodes,
    EnvelopeSummary,
    EnvelopeListResponse,
    RecipientCreate,
    RecipientUpdate,
    RecipientResponse,
    RecipientWithAccessCode,
    RecipientAccessRequest,
    RecipientDecline,
    EnvelopeDocumentCreate,
    EnvelopeDocumentResponse,
    SigningOrderUpdate,
)

__all__ = [
    # Auth
    "LoginRequest",
    "LoginResponse",
    "RegisterRequest",
    "TokenRefreshRequest",
    "UserProfileResponse",
    # Document
    "DocumentUploadResponse",
    "DocumentMetadataResponse",
    "DocumentListResponse",
    "DocumentPageSchema",
    # Envelope
    "EnvelopeCreate",
    "EnvelopeUpdate",
    "EnvelopeSend",
    "EnvelopeVoid",
    "EnvelopeReminder",
    "EnvelopeResponse",
    "EnvelopeResponseWithAccessCodes",
    "EnvelopeSummary",
    "EnvelopeListResponse",
    "RecipientCreate",
    "RecipientUpdate",
    "RecipientResponse",
    "RecipientWithAccessCode",
    "RecipientAccessRequest",
    "RecipientDecline",
    "EnvelopeDocumentCreate",
    "EnvelopeDocumentResponse",
    "SigningOrderUpdate",
]
