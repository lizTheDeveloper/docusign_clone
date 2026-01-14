"""Envelope domain models with business logic."""
import secrets
import hashlib
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from uuid import UUID


class EnvelopeStatus(str, Enum):
    """Envelope workflow status."""
    DRAFT = "draft"
    SENT = "sent"
    DELIVERED = "delivered"
    SIGNED = "signed"
    COMPLETED = "completed"
    DECLINED = "declined"
    VOIDED = "voided"
    EXPIRED = "expired"


class SigningOrder(str, Enum):
    """Signing workflow order type."""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


class RecipientRole(str, Enum):
    """Recipient role in envelope."""
    SIGNER = "signer"
    CC = "cc"
    APPROVER = "approver"


class RecipientStatus(str, Enum):
    """Recipient status in workflow."""
    PENDING = "pending"
    SENT = "sent"
    VIEWED = "viewed"
    SIGNED = "signed"
    DECLINED = "declined"


class Envelope:
    """
    Envelope domain model representing a signing workflow container.
    
    Encapsulates envelope data and business logic for workflow orchestration,
    status management, and recipient coordination.
    """

    # Constants
    MIN_SUBJECT_LENGTH = 1
    MAX_SUBJECT_LENGTH = 200
    MAX_MESSAGE_LENGTH = 5000
    MIN_EXPIRATION_DAYS = 1
    MAX_EXPIRATION_DAYS = 365
    DEFAULT_EXPIRATION_DAYS = 30
    MAX_DOCUMENTS = 50
    MAX_RECIPIENTS = 100

    def __init__(
        self,
        envelope_id: UUID,
        sender_id: UUID,
        subject: str,
        message: Optional[str] = None,
        status: EnvelopeStatus = EnvelopeStatus.DRAFT,
        signing_order: SigningOrder = SigningOrder.PARALLEL,
        expiration_days: int = DEFAULT_EXPIRATION_DAYS,
        expires_at: Optional[datetime] = None,
        void_reason: Optional[str] = None,
        created_at: Optional[datetime] = None,
        sent_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        voided_at: Optional[datetime] = None,
        expired_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize Envelope domain model."""
        self.envelope_id = envelope_id
        self.sender_id = sender_id
        self.subject = subject
        self.message = message
        self.status = status
        self.signing_order = signing_order
        self.expiration_days = expiration_days
        self.expires_at = expires_at
        self.void_reason = void_reason
        self.created_at = created_at or datetime.utcnow()
        self.sent_at = sent_at
        self.completed_at = completed_at
        self.voided_at = voided_at
        self.expired_at = expired_at
        self.updated_at = updated_at or datetime.utcnow()

    @staticmethod
    def validate_subject(subject: str) -> tuple[bool, Optional[str]]:
        """
        Validate envelope subject.
        
        Args:
            subject: Envelope subject line
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not subject or not subject.strip():
            return False, "Subject is required"
        
        if len(subject) < Envelope.MIN_SUBJECT_LENGTH:
            return False, f"Subject must be at least {Envelope.MIN_SUBJECT_LENGTH} characters"
        
        if len(subject) > Envelope.MAX_SUBJECT_LENGTH:
            return False, f"Subject cannot exceed {Envelope.MAX_SUBJECT_LENGTH} characters"
        
        return True, None

    @staticmethod
    def validate_message(message: Optional[str]) -> tuple[bool, Optional[str]]:
        """
        Validate envelope message.
        
        Args:
            message: Optional envelope message
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if message and len(message) > Envelope.MAX_MESSAGE_LENGTH:
            return False, f"Message cannot exceed {Envelope.MAX_MESSAGE_LENGTH} characters"
        
        return True, None

    @staticmethod
    def validate_expiration_days(days: int) -> tuple[bool, Optional[str]]:
        """
        Validate expiration days.
        
        Args:
            days: Number of days until expiration
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if days < Envelope.MIN_EXPIRATION_DAYS:
            return False, f"Expiration must be at least {Envelope.MIN_EXPIRATION_DAYS} day"
        
        if days > Envelope.MAX_EXPIRATION_DAYS:
            return False, f"Expiration cannot exceed {Envelope.MAX_EXPIRATION_DAYS} days"
        
        return True, None

    def can_send(self) -> tuple[bool, Optional[str]]:
        """
        Check if envelope can be sent.
        
        Returns:
            tuple: (can_send, error_message)
        """
        if self.status != EnvelopeStatus.DRAFT:
            return False, f"Cannot send envelope with status '{self.status}'"
        
        return True, None

    def can_void(self) -> tuple[bool, Optional[str]]:
        """
        Check if envelope can be voided.
        
        Returns:
            tuple: (can_void, error_message)
        """
        if self.status in [EnvelopeStatus.COMPLETED, EnvelopeStatus.VOIDED, EnvelopeStatus.EXPIRED]:
            return False, f"Cannot void envelope with status '{self.status}'"
        
        if self.status == EnvelopeStatus.DRAFT:
            return False, "Cannot void draft envelope (delete it instead)"
        
        return True, None

    def can_update(self) -> tuple[bool, Optional[str]]:
        """
        Check if envelope can be updated.
        
        Returns:
            tuple: (can_update, error_message)
        """
        if self.status != EnvelopeStatus.DRAFT:
            return False, f"Cannot update envelope with status '{self.status}'"
        
        return True, None

    def send(self, sent_at: Optional[datetime] = None) -> None:
        """
        Mark envelope as sent.
        
        Args:
            sent_at: Optional timestamp (defaults to now)
            
        Raises:
            ValueError: If envelope cannot be sent
        """
        can_send, error = self.can_send()
        if not can_send:
            raise ValueError(error)
        
        self.status = EnvelopeStatus.SENT
        self.sent_at = sent_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Set expiration if not already set
        if not self.expires_at:
            self.expires_at = self.sent_at + timedelta(days=self.expiration_days)

    def void(self, reason: str, voided_at: Optional[datetime] = None) -> None:
        """
        Void the envelope.
        
        Args:
            reason: Reason for voiding
            voided_at: Optional timestamp (defaults to now)
            
        Raises:
            ValueError: If envelope cannot be voided
        """
        can_void, error = self.can_void()
        if not can_void:
            raise ValueError(error)
        
        if not reason or not reason.strip():
            raise ValueError("Void reason is required")
        
        self.status = EnvelopeStatus.VOIDED
        self.void_reason = reason
        self.voided_at = voided_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, completed_at: Optional[datetime] = None) -> None:
        """
        Mark envelope as completed.
        
        Args:
            completed_at: Optional timestamp (defaults to now)
        """
        self.status = EnvelopeStatus.COMPLETED
        self.completed_at = completed_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def decline(self) -> None:
        """Mark envelope as declined."""
        self.status = EnvelopeStatus.DECLINED
        self.updated_at = datetime.utcnow()

    def expire(self, expired_at: Optional[datetime] = None) -> None:
        """
        Mark envelope as expired.
        
        Args:
            expired_at: Optional timestamp (defaults to now)
        """
        self.status = EnvelopeStatus.EXPIRED
        self.expired_at = expired_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """
        Check if envelope has expired.
        
        Returns:
            bool: True if envelope has expired
        """
        if self.status == EnvelopeStatus.EXPIRED:
            return True
        
        if self.expires_at and datetime.utcnow() >= self.expires_at:
            return True
        
        return False


class Recipient:
    """
    Recipient domain model representing a participant in signing workflow.
    
    Encapsulates recipient data and business logic for authentication,
    status tracking, and workflow progression.
    """

    # Constants
    MAX_NAME_LENGTH = 200
    ACCESS_CODE_LENGTH = 6
    MIN_SIGNING_ORDER = 1

    def __init__(
        self,
        recipient_id: UUID,
        envelope_id: UUID,
        name: str,
        email: str,
        role: RecipientRole,
        signing_order: int = 1,
        status: RecipientStatus = RecipientStatus.PENDING,
        user_id: Optional[UUID] = None,
        phone: Optional[str] = None,
        access_code: Optional[str] = None,
        access_code_hash: Optional[str] = None,
        decline_reason: Optional[str] = None,
        sent_at: Optional[datetime] = None,
        viewed_at: Optional[datetime] = None,
        signed_at: Optional[datetime] = None,
        declined_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize Recipient domain model."""
        self.recipient_id = recipient_id
        self.envelope_id = envelope_id
        self.name = name
        self.email = email
        self.role = role
        self.signing_order = signing_order
        self.status = status
        self.user_id = user_id
        self.phone = phone
        self.access_code = access_code
        self.access_code_hash = access_code_hash
        self.decline_reason = decline_reason
        self.sent_at = sent_at
        self.viewed_at = viewed_at
        self.signed_at = signed_at
        self.declined_at = declined_at
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    @staticmethod
    def generate_access_code() -> str:
        """
        Generate a random 6-digit access code.
        
        Returns:
            str: 6-digit access code
        """
        return ''.join([str(secrets.randbelow(10)) for _ in range(Recipient.ACCESS_CODE_LENGTH)])

    @staticmethod
    def hash_access_code(code: str) -> str:
        """
        Hash an access code for secure storage.
        
        Args:
            code: Plain text access code
            
        Returns:
            str: SHA-256 hash of access code
        """
        return hashlib.sha256(code.encode()).hexdigest()

    @staticmethod
    def validate_name(name: str) -> tuple[bool, Optional[str]]:
        """
        Validate recipient name.
        
        Args:
            name: Recipient name
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Recipient name is required"
        
        if len(name) > Recipient.MAX_NAME_LENGTH:
            return False, f"Recipient name cannot exceed {Recipient.MAX_NAME_LENGTH} characters"
        
        return True, None

    @staticmethod
    def validate_email(email: str) -> tuple[bool, Optional[str]]:
        """
        Validate recipient email.
        
        Args:
            email: Email address
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not email or not email.strip():
            return False, "Recipient email is required"
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            return False, "Invalid email format"
        
        return True, None

    @staticmethod
    def validate_signing_order(order: int) -> tuple[bool, Optional[str]]:
        """
        Validate signing order.
        
        Args:
            order: Signing order number
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if order < Recipient.MIN_SIGNING_ORDER:
            return False, f"Signing order must be at least {Recipient.MIN_SIGNING_ORDER}"
        
        return True, None

    def verify_access_code(self, provided_code: str) -> bool:
        """
        Verify if provided access code matches.
        
        Args:
            provided_code: Access code to verify
            
        Returns:
            bool: True if code matches
        """
        if not self.access_code_hash:
            return False
        
        provided_hash = self.hash_access_code(provided_code)
        return provided_hash == self.access_code_hash

    def can_sign(self) -> tuple[bool, Optional[str]]:
        """
        Check if recipient can sign.
        
        Returns:
            tuple: (can_sign, error_message)
        """
        if self.role != RecipientRole.SIGNER:
            return False, f"Recipient role '{self.role}' cannot sign"
        
        if self.status == RecipientStatus.SIGNED:
            return False, "Recipient has already signed"
        
        if self.status == RecipientStatus.DECLINED:
            return False, "Recipient has declined"
        
        return True, None

    def mark_sent(self, sent_at: Optional[datetime] = None) -> None:
        """
        Mark recipient as sent (notification sent).
        
        Args:
            sent_at: Optional timestamp (defaults to now)
        """
        self.status = RecipientStatus.SENT
        self.sent_at = sent_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_viewed(self, viewed_at: Optional[datetime] = None) -> None:
        """
        Mark recipient as viewed (opened envelope).
        
        Args:
            viewed_at: Optional timestamp (defaults to now)
        """
        if self.status == RecipientStatus.PENDING or self.status == RecipientStatus.SENT:
            self.status = RecipientStatus.VIEWED
        
        if not self.viewed_at:
            self.viewed_at = viewed_at or datetime.utcnow()
        
        self.updated_at = datetime.utcnow()

    def mark_signed(self, signed_at: Optional[datetime] = None) -> None:
        """
        Mark recipient as signed.
        
        Args:
            signed_at: Optional timestamp (defaults to now)
            
        Raises:
            ValueError: If recipient cannot sign
        """
        can_sign, error = self.can_sign()
        if not can_sign:
            raise ValueError(error)
        
        self.status = RecipientStatus.SIGNED
        self.signed_at = signed_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_declined(self, reason: str, declined_at: Optional[datetime] = None) -> None:
        """
        Mark recipient as declined.
        
        Args:
            reason: Reason for declining
            declined_at: Optional timestamp (defaults to now)
        """
        if not reason or not reason.strip():
            raise ValueError("Decline reason is required")
        
        self.status = RecipientStatus.DECLINED
        self.decline_reason = reason
        self.declined_at = declined_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()


class EnvelopeDocument:
    """
    EnvelopeDocument domain model representing document-envelope association.
    
    Manages the relationship between envelopes and their documents with display ordering.
    """

    def __init__(
        self,
        envelope_document_id: UUID,
        envelope_id: UUID,
        document_id: UUID,
        display_order: int = 0,
        created_at: Optional[datetime] = None,
    ):
        """Initialize EnvelopeDocument domain model."""
        self.envelope_document_id = envelope_document_id
        self.envelope_id = envelope_id
        self.document_id = document_id
        self.display_order = display_order
        self.created_at = created_at or datetime.utcnow()

    @staticmethod
    def validate_display_order(order: int) -> tuple[bool, Optional[str]]:
        """
        Validate display order.
        
        Args:
            order: Display order number
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if order < 0:
            return False, "Display order must be non-negative"
        
        return True, None
