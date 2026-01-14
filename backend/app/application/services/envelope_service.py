"""Envelope business service for orchestrating signing workflows."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from app.domain.models.envelope import (
    Envelope,
    EnvelopeDocument,
    Recipient,
    EnvelopeStatus,
    SigningOrder,
    RecipientRole,
    RecipientStatus,
)
from app.infrastructure.repositories.envelope_repository import EnvelopeRepository
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class EnvelopeServiceError(Exception):
    """Base exception for envelope service errors."""
    pass


class EnvelopeValidationError(EnvelopeServiceError):
    """Exception raised when envelope validation fails."""
    pass


class EnvelopeNotFoundError(EnvelopeServiceError):
    """Exception raised when envelope is not found."""
    pass


class EnvelopePermissionError(EnvelopeServiceError):
    """Exception raised when user lacks permission for envelope operation."""
    pass


class RecipientNotFoundError(EnvelopeServiceError):
    """Exception raised when recipient is not found."""
    pass


class EnvelopeService:
    """
    Envelope business service for handling signing workflow operations.
    
    Orchestrates envelope creation, recipient management, workflow state transitions,
    and coordinates with notification systems for email/SMS alerts.
    """

    def __init__(
        self,
        envelope_repository: EnvelopeRepository,
        document_repository: DocumentRepository,
        user_repository: UserRepository,
    ):
        """
        Initialize envelope service.
        
        Args:
            envelope_repository: Repository for envelope persistence
            document_repository: Repository for document operations
            user_repository: Repository for user operations
        """
        self.envelope_repository = envelope_repository
        self.document_repository = document_repository
        self.user_repository = user_repository

    # ========================================================================
    # Envelope Operations
    # ========================================================================

    async def create_envelope(
        self,
        sender_id: UUID,
        subject: str,
        document_ids: List[UUID],
        message: Optional[str] = None,
        signing_order: SigningOrder = SigningOrder.PARALLEL,
        expiration_days: int = 30,
        recipients: Optional[List[dict]] = None,
    ) -> Tuple[Envelope, List[Recipient]]:
        """
        Create a new envelope in draft status.
        
        Args:
            sender_id: User ID of envelope sender
            subject: Envelope subject line
            document_ids: List of document UUIDs to include
            message: Optional message to recipients
            signing_order: Parallel or sequential signing
            expiration_days: Days until envelope expires
            recipients: Optional list of recipient data
            
        Returns:
            Tuple[Envelope, List[Recipient]]: Created envelope and recipients
            
        Raises:
            EnvelopeValidationError: If validation fails
            EnvelopeServiceError: If creation fails
        """
        try:
            # Validate subject
            is_valid, error = Envelope.validate_subject(subject)
            if not is_valid:
                raise EnvelopeValidationError(error)
            
            # Validate message
            is_valid, error = Envelope.validate_message(message)
            if not is_valid:
                raise EnvelopeValidationError(error)
            
            # Validate expiration days
            is_valid, error = Envelope.validate_expiration_days(expiration_days)
            if not is_valid:
                raise EnvelopeValidationError(error)
            
            # Validate document count
            if not document_ids:
                raise EnvelopeValidationError("At least one document is required")
            
            if len(document_ids) > Envelope.MAX_DOCUMENTS:
                raise EnvelopeValidationError(
                    f"Cannot exceed {Envelope.MAX_DOCUMENTS} documents per envelope"
                )
            
            # Check for duplicate document IDs
            if len(document_ids) != len(set(document_ids)):
                raise EnvelopeValidationError("Duplicate document IDs are not allowed")
            
            # Verify all documents exist and belong to sender
            for doc_id in document_ids:
                doc = await self.document_repository.get_document_by_id(doc_id)
                if doc is None:
                    raise EnvelopeValidationError(f"Document {doc_id} not found")
                if doc.user_id != sender_id:
                    raise EnvelopePermissionError(
                        f"User does not have access to document {doc_id}"
                    )
                if doc.status.value != "ready":
                    raise EnvelopeValidationError(
                        f"Document {doc_id} is not ready (status: {doc.status.value})"
                    )
            
            # Create envelope
            envelope_id = uuid4()
            envelope = Envelope(
                envelope_id=envelope_id,
                sender_id=sender_id,
                subject=subject,
                message=message,
                status=EnvelopeStatus.DRAFT,
                signing_order=signing_order,
                expiration_days=expiration_days,
            )
            
            # Persist envelope
            created_envelope = await self.envelope_repository.create_envelope(envelope)
            
            # Add documents to envelope
            for idx, doc_id in enumerate(document_ids):
                envelope_doc = EnvelopeDocument(
                    envelope_document_id=uuid4(),
                    envelope_id=envelope_id,
                    document_id=doc_id,
                    display_order=idx,
                )
                await self.envelope_repository.add_document_to_envelope(envelope_doc)
            
            # Add recipients if provided
            created_recipients = []
            if recipients:
                for recipient_data in recipients:
                    recipient = await self.add_recipient(
                        envelope_id=envelope_id,
                        sender_id=sender_id,
                        name=recipient_data['name'],
                        email=recipient_data['email'],
                        role=RecipientRole(recipient_data['role']),
                        phone=recipient_data.get('phone'),
                        signing_order=recipient_data.get('signing_order', 1),
                    )
                    created_recipients.append(recipient)
            
            logger.info(f"Created envelope {envelope_id} with {len(document_ids)} documents")
            return created_envelope, created_recipients
            
        except EnvelopeServiceError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error creating envelope: {e}")
            raise EnvelopeServiceError(f"Failed to create envelope: {str(e)}") from e

    async def get_envelope(
        self,
        envelope_id: UUID,
        user_id: UUID,
        include_access_codes: bool = False
    ) -> Tuple[Envelope, List[Recipient], List[dict], dict]:
        """
        Get envelope details with authorization check.
        
        Args:
            envelope_id: Envelope UUID
            user_id: User ID requesting access
            include_access_codes: Whether to include recipient access codes
            
        Returns:
            Tuple: (envelope, recipients, documents, sender_info)
            
        Raises:
            EnvelopeNotFoundError: If envelope not found
            EnvelopePermissionError: If user lacks access
        """
        envelope = await self.envelope_repository.get_envelope_by_id(envelope_id)
        if envelope is None:
            raise EnvelopeNotFoundError(f"Envelope {envelope_id} not found")
        
        # Check authorization - sender or recipient
        is_sender = envelope.sender_id == user_id
        
        if not is_sender:
            # Check if user is a recipient
            recipients = await self.envelope_repository.get_recipients_by_envelope(envelope_id)
            recipient_emails = [r.email for r in recipients]
            
            # Get user email
            user = await self.user_repository.get_user_by_id(user_id)
            if user is None or user.email not in recipient_emails:
                raise EnvelopePermissionError("User does not have access to this envelope")
        
        # Get recipients
        recipients = await self.envelope_repository.get_recipients_by_envelope(envelope_id)
        
        # Remove access codes if not sender
        if not is_sender or not include_access_codes:
            for recipient in recipients:
                recipient.access_code = None
        
        # Get documents
        documents = await self.envelope_repository.get_envelope_documents(envelope_id)
        
        # Get sender info
        sender = await self.user_repository.get_user_by_id(envelope.sender_id)
        sender_info = {
            "user_id": sender.user_id,
            "name": f"{sender.first_name} {sender.last_name}",
            "email": sender.email,
        }
        
        return envelope, recipients, documents, sender_info

    async def update_envelope(
        self,
        envelope_id: UUID,
        user_id: UUID,
        subject: Optional[str] = None,
        message: Optional[str] = None,
        signing_order: Optional[SigningOrder] = None,
        expiration_days: Optional[int] = None,
    ) -> Envelope:
        """
        Update envelope (only in draft status).
        
        Args:
            envelope_id: Envelope UUID
            user_id: User ID making the update
            subject: Optional new subject
            message: Optional new message
            signing_order: Optional new signing order
            expiration_days: Optional new expiration days
            
        Returns:
            Envelope: Updated envelope
            
        Raises:
            EnvelopeNotFoundError: If envelope not found
            EnvelopePermissionError: If user is not sender
            EnvelopeValidationError: If envelope cannot be updated
        """
        envelope = await self.envelope_repository.get_envelope_by_id(envelope_id)
        if envelope is None:
            raise EnvelopeNotFoundError(f"Envelope {envelope_id} not found")
        
        # Check authorization
        if envelope.sender_id != user_id:
            raise EnvelopePermissionError("Only sender can update envelope")
        
        # Check if envelope can be updated
        can_update, error = envelope.can_update()
        if not can_update:
            raise EnvelopeValidationError(error)
        
        # Update fields
        if subject is not None:
            is_valid, error = Envelope.validate_subject(subject)
            if not is_valid:
                raise EnvelopeValidationError(error)
            envelope.subject = subject
        
        if message is not None:
            is_valid, error = Envelope.validate_message(message)
            if not is_valid:
                raise EnvelopeValidationError(error)
            envelope.message = message
        
        if signing_order is not None:
            envelope.signing_order = signing_order
        
        if expiration_days is not None:
            is_valid, error = Envelope.validate_expiration_days(expiration_days)
            if not is_valid:
                raise EnvelopeValidationError(error)
            envelope.expiration_days = expiration_days
        
        envelope.updated_at = datetime.utcnow()
        
        # Persist changes
        updated_envelope = await self.envelope_repository.update_envelope(envelope)
        
        logger.info(f"Updated envelope {envelope_id}")
        return updated_envelope

    async def send_envelope(
        self,
        envelope_id: UUID,
        user_id: UUID
    ) -> Envelope:
        """
        Send envelope to recipients.
        
        Transitions envelope from draft to sent status and triggers notifications.
        
        Args:
            envelope_id: Envelope UUID
            user_id: User ID sending the envelope
            
        Returns:
            Envelope: Updated envelope
            
        Raises:
            EnvelopeNotFoundError: If envelope not found
            EnvelopePermissionError: If user is not sender
            EnvelopeValidationError: If envelope cannot be sent
        """
        envelope = await self.envelope_repository.get_envelope_by_id(envelope_id)
        if envelope is None:
            raise EnvelopeNotFoundError(f"Envelope {envelope_id} not found")
        
        # Check authorization
        if envelope.sender_id != user_id:
            raise EnvelopePermissionError("Only sender can send envelope")
        
        # Check if envelope can be sent
        can_send, error = envelope.can_send()
        if not can_send:
            raise EnvelopeValidationError(error)
        
        # Verify envelope has recipients
        recipients = await self.envelope_repository.get_recipients_by_envelope(envelope_id)
        if not recipients:
            raise EnvelopeValidationError("Envelope must have at least one recipient")
        
        # Verify envelope has at least one signer
        has_signer = any(r.role == RecipientRole.SIGNER for r in recipients)
        if not has_signer:
            raise EnvelopeValidationError("Envelope must have at least one signer")
        
        # Send envelope
        envelope.send()
        updated_envelope = await self.envelope_repository.update_envelope(envelope)
        
        # Mark recipients as sent (for sequential, only first order)
        if envelope.signing_order == SigningOrder.SEQUENTIAL:
            # Send to first signing order only
            min_order = min(r.signing_order for r in recipients if r.role == RecipientRole.SIGNER)
            for recipient in recipients:
                if recipient.signing_order == min_order and recipient.role == RecipientRole.SIGNER:
                    recipient.mark_sent()
                    await self.envelope_repository.update_recipient(recipient)
        else:
            # Parallel - send to all recipients
            for recipient in recipients:
                recipient.mark_sent()
                await self.envelope_repository.update_recipient(recipient)
        
        # TODO: Trigger notification events
        # - envelope.sent event
        # - Send emails/SMS to recipients
        
        logger.info(f"Sent envelope {envelope_id}")
        return updated_envelope

    async def void_envelope(
        self,
        envelope_id: UUID,
        user_id: UUID,
        reason: str
    ) -> Envelope:
        """
        Void an envelope.
        
        Args:
            envelope_id: Envelope UUID
            user_id: User ID voiding the envelope
            reason: Reason for voiding
            
        Returns:
            Envelope: Voided envelope
            
        Raises:
            EnvelopeNotFoundError: If envelope not found
            EnvelopePermissionError: If user is not sender
            EnvelopeValidationError: If envelope cannot be voided
        """
        envelope = await self.envelope_repository.get_envelope_by_id(envelope_id)
        if envelope is None:
            raise EnvelopeNotFoundError(f"Envelope {envelope_id} not found")
        
        # Check authorization
        if envelope.sender_id != user_id:
            raise EnvelopePermissionError("Only sender can void envelope")
        
        # Void envelope
        envelope.void(reason)
        updated_envelope = await self.envelope_repository.update_envelope(envelope)
        
        # TODO: Trigger notification events
        # - envelope.voided event
        # - Notify all recipients
        
        logger.info(f"Voided envelope {envelope_id}")
        return updated_envelope

    async def list_envelopes(
        self,
        user_id: UUID,
        status: Optional[EnvelopeStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Envelope], int, bool]:
        """
        List envelopes for a user.
        
        Args:
            user_id: User ID
            status: Optional status filter
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Tuple: (envelopes, total_count, has_more)
        """
        envelopes, total = await self.envelope_repository.list_envelopes(
            user_id=user_id,
            status=status,
            page=page,
            page_size=page_size,
        )
        
        has_more = (page * page_size) < total
        
        return envelopes, total, has_more

    # ========================================================================
    # Recipient Operations
    # ========================================================================

    async def add_recipient(
        self,
        envelope_id: UUID,
        sender_id: UUID,
        name: str,
        email: str,
        role: RecipientRole,
        phone: Optional[str] = None,
        signing_order: int = 1,
    ) -> Recipient:
        """
        Add a recipient to an envelope.
        
        Args:
            envelope_id: Envelope UUID
            sender_id: Sender user ID
            name: Recipient name
            email: Recipient email
            role: Recipient role
            phone: Optional phone number
            signing_order: Signing order number
            
        Returns:
            Recipient: Created recipient
            
        Raises:
            EnvelopeNotFoundError: If envelope not found
            EnvelopePermissionError: If user is not sender
            EnvelopeValidationError: If envelope is not in draft or validation fails
        """
        envelope = await self.envelope_repository.get_envelope_by_id(envelope_id)
        if envelope is None:
            raise EnvelopeNotFoundError(f"Envelope {envelope_id} not found")
        
        # Check authorization
        if envelope.sender_id != sender_id:
            raise EnvelopePermissionError("Only sender can add recipients")
        
        # Check if envelope is in draft
        if envelope.status != EnvelopeStatus.DRAFT:
            raise EnvelopeValidationError("Cannot add recipients to non-draft envelope")
        
        # Validate recipient data
        is_valid, error = Recipient.validate_name(name)
        if not is_valid:
            raise EnvelopeValidationError(error)
        
        is_valid, error = Recipient.validate_email(email)
        if not is_valid:
            raise EnvelopeValidationError(error)
        
        is_valid, error = Recipient.validate_signing_order(signing_order)
        if not is_valid:
            raise EnvelopeValidationError(error)
        
        # Check recipient limit
        recipients = await self.envelope_repository.get_recipients_by_envelope(envelope_id)
        if len(recipients) >= Envelope.MAX_RECIPIENTS:
            raise EnvelopeValidationError(
                f"Cannot exceed {Envelope.MAX_RECIPIENTS} recipients per envelope"
            )
        
        # Generate access code
        access_code = Recipient.generate_access_code()
        access_code_hash = Recipient.hash_access_code(access_code)
        
        # Create recipient
        recipient = Recipient(
            recipient_id=uuid4(),
            envelope_id=envelope_id,
            name=name,
            email=email,
            phone=phone,
            role=role,
            signing_order=signing_order,
            status=RecipientStatus.PENDING,
            access_code=access_code,
            access_code_hash=access_code_hash,
        )
        
        created_recipient = await self.envelope_repository.create_recipient(recipient)
        
        logger.info(f"Added recipient {created_recipient.recipient_id} to envelope {envelope_id}")
        return created_recipient

    async def update_recipient_signing_order(
        self,
        envelope_id: UUID,
        user_id: UUID,
        recipient_orders: List[dict],
    ) -> List[Recipient]:
        """
        Update signing order for recipients.
        
        Args:
            envelope_id: Envelope UUID
            user_id: User ID making the update
            recipient_orders: List of {recipient_id, signing_order} dicts
            
        Returns:
            List[Recipient]: Updated recipients
            
        Raises:
            EnvelopeNotFoundError: If envelope not found
            EnvelopePermissionError: If user is not sender
            EnvelopeValidationError: If envelope is not in draft
        """
        envelope = await self.envelope_repository.get_envelope_by_id(envelope_id)
        if envelope is None:
            raise EnvelopeNotFoundError(f"Envelope {envelope_id} not found")
        
        # Check authorization
        if envelope.sender_id != user_id:
            raise EnvelopePermissionError("Only sender can update recipient order")
        
        # Check if envelope is in draft
        if envelope.status != EnvelopeStatus.DRAFT:
            raise EnvelopeValidationError("Cannot update recipients in non-draft envelope")
        
        # Update each recipient
        updated_recipients = []
        for order_data in recipient_orders:
            recipient = await self.envelope_repository.get_recipient_by_id(
                order_data['recipient_id']
            )
            if recipient is None:
                raise RecipientNotFoundError(
                    f"Recipient {order_data['recipient_id']} not found"
                )
            
            if recipient.envelope_id != envelope_id:
                raise EnvelopeValidationError(
                    f"Recipient {recipient.recipient_id} does not belong to envelope {envelope_id}"
                )
            
            recipient.signing_order = order_data['signing_order']
            recipient.updated_at = datetime.utcnow()
            
            updated_recipient = await self.envelope_repository.update_recipient(recipient)
            updated_recipients.append(updated_recipient)
        
        logger.info(f"Updated signing order for {len(updated_recipients)} recipients")
        return updated_recipients

    async def mark_recipient_viewed(
        self,
        envelope_id: UUID,
        recipient_id: UUID
    ) -> Recipient:
        """
        Mark recipient as having viewed the envelope.
        
        Args:
            envelope_id: Envelope UUID
            recipient_id: Recipient UUID
            
        Returns:
            Recipient: Updated recipient
        """
        recipient = await self.envelope_repository.get_recipient_by_id(recipient_id)
        if recipient is None:
            raise RecipientNotFoundError(f"Recipient {recipient_id} not found")
        
        if recipient.envelope_id != envelope_id:
            raise EnvelopeValidationError("Recipient does not belong to this envelope")
        
        recipient.mark_viewed()
        updated_recipient = await self.envelope_repository.update_recipient(recipient)
        
        # TODO: Trigger envelope.viewed event
        
        logger.info(f"Recipient {recipient_id} viewed envelope {envelope_id}")
        return updated_recipient

    async def mark_recipient_signed(
        self,
        envelope_id: UUID,
        recipient_id: UUID
    ) -> Tuple[Recipient, bool]:
        """
        Mark recipient as having signed.
        
        Checks if envelope is complete and sends to next recipients in sequential workflow.
        
        Args:
            envelope_id: Envelope UUID
            recipient_id: Recipient UUID
            
        Returns:
            Tuple[Recipient, bool]: (updated_recipient, envelope_completed)
        """
        recipient = await self.envelope_repository.get_recipient_by_id(recipient_id)
        if recipient is None:
            raise RecipientNotFoundError(f"Recipient {recipient_id} not found")
        
        if recipient.envelope_id != envelope_id:
            raise EnvelopeValidationError("Recipient does not belong to this envelope")
        
        recipient.mark_signed()
        updated_recipient = await self.envelope_repository.update_recipient(recipient)
        
        # TODO: Trigger envelope.recipient.signed event
        
        # Check if envelope is complete
        pending_count = await self.envelope_repository.count_pending_recipients(envelope_id)
        envelope_completed = (pending_count == 0)
        
        if envelope_completed:
            # Complete the envelope
            envelope = await self.envelope_repository.get_envelope_by_id(envelope_id)
            envelope.complete()
            await self.envelope_repository.update_envelope(envelope)
            
            # TODO: Trigger envelope.completed event
            logger.info(f"Envelope {envelope_id} completed")
        else:
            # For sequential workflows, notify next recipients
            envelope = await self.envelope_repository.get_envelope_by_id(envelope_id)
            if envelope.signing_order == SigningOrder.SEQUENTIAL:
                recipients = await self.envelope_repository.get_recipients_by_envelope(envelope_id)
                
                # Find next signing order
                current_order = recipient.signing_order
                next_order_recipients = [
                    r for r in recipients
                    if r.signing_order == current_order + 1
                    and r.role == RecipientRole.SIGNER
                    and r.status == RecipientStatus.PENDING
                ]
                
                # Send to next order recipients
                for next_recipient in next_order_recipients:
                    next_recipient.mark_sent()
                    await self.envelope_repository.update_recipient(next_recipient)
                    # TODO: Trigger notification
        
        logger.info(f"Recipient {recipient_id} signed envelope {envelope_id}")
        return updated_recipient, envelope_completed

    async def decline_envelope(
        self,
        envelope_id: UUID,
        recipient_id: UUID,
        reason: str
    ) -> Recipient:
        """
        Recipient declines to sign envelope.
        
        Args:
            envelope_id: Envelope UUID
            recipient_id: Recipient UUID
            reason: Reason for declining
            
        Returns:
            Recipient: Updated recipient
        """
        recipient = await self.envelope_repository.get_recipient_by_id(recipient_id)
        if recipient is None:
            raise RecipientNotFoundError(f"Recipient {recipient_id} not found")
        
        if recipient.envelope_id != envelope_id:
            raise EnvelopeValidationError("Recipient does not belong to this envelope")
        
        recipient.mark_declined(reason)
        updated_recipient = await self.envelope_repository.update_recipient(recipient)
        
        # Mark envelope as declined
        envelope = await self.envelope_repository.get_envelope_by_id(envelope_id)
        envelope.decline()
        await self.envelope_repository.update_envelope(envelope)
        
        # TODO: Trigger envelope.declined event
        
        logger.info(f"Recipient {recipient_id} declined envelope {envelope_id}")
        return updated_recipient

    async def verify_recipient_access(
        self,
        envelope_id: UUID,
        email: str,
        access_code: str
    ) -> Optional[Recipient]:
        """
        Verify recipient access code.
        
        Args:
            envelope_id: Envelope UUID
            email: Recipient email
            access_code: Access code provided
            
        Returns:
            Optional[Recipient]: Recipient if access code is valid, None otherwise
        """
        access_code_hash = Recipient.hash_access_code(access_code)
        recipient = await self.envelope_repository.get_recipient_by_access_code_hash(
            envelope_id, access_code_hash
        )
        
        if recipient is None:
            return None
        
        # Verify email matches
        if recipient.email.lower() != email.lower():
            return None
        
        return recipient
