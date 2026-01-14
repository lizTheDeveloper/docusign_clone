"""Repository for envelope database operations."""
import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.domain.models.envelope import (
    Envelope,
    EnvelopeDocument,
    Recipient,
    EnvelopeStatus,
    SigningOrder,
    RecipientRole,
    RecipientStatus,
)
from app.infrastructure.models import (
    EnvelopeModel,
    EnvelopeDocumentModel,
    RecipientModel,
    DocumentModel,
    UserModel,
)

logger = logging.getLogger(__name__)


class EnvelopeRepository:
    """
    Repository for envelope persistence operations.
    
    Handles all database operations for envelopes, recipients, and
    envelope-document associations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    # ========================================================================
    # Envelope CRUD Operations
    # ========================================================================

    async def create_envelope(self, envelope: Envelope) -> Envelope:
        """
        Create a new envelope in the database.
        
        Args:
            envelope: Envelope domain model
            
        Returns:
            Envelope: Created envelope with DB-generated fields
        """
        db_envelope = EnvelopeModel(
            envelope_id=envelope.envelope_id,
            sender_id=envelope.sender_id,
            subject=envelope.subject,
            message=envelope.message,
            status=envelope.status.value,
            signing_order=envelope.signing_order.value,
            expiration_days=envelope.expiration_days,
            expires_at=envelope.expires_at,
            void_reason=envelope.void_reason,
            created_at=envelope.created_at,
            sent_at=envelope.sent_at,
            completed_at=envelope.completed_at,
            voided_at=envelope.voided_at,
            expired_at=envelope.expired_at,
            updated_at=envelope.updated_at,
        )
        
        self.session.add(db_envelope)
        await self.session.flush()
        await self.session.refresh(db_envelope)
        
        logger.info(f"Created envelope {envelope.envelope_id}")
        return self._envelope_to_domain(db_envelope)

    async def get_envelope_by_id(
        self,
        envelope_id: UUID,
        load_relationships: bool = True
    ) -> Optional[Envelope]:
        """
        Get envelope by ID.
        
        Args:
            envelope_id: Envelope UUID
            load_relationships: Whether to eagerly load documents and recipients
            
        Returns:
            Optional[Envelope]: Envelope if found, None otherwise
        """
        query = select(EnvelopeModel).where(EnvelopeModel.envelope_id == envelope_id)
        
        if load_relationships:
            query = query.options(
                selectinload(EnvelopeModel.envelope_documents),
                selectinload(EnvelopeModel.recipients)
            )
        
        result = await self.session.execute(query)
        db_envelope = result.scalar_one_or_none()
        
        if db_envelope is None:
            return None
        
        return self._envelope_to_domain(db_envelope)

    async def update_envelope(self, envelope: Envelope) -> Envelope:
        """
        Update an existing envelope.
        
        Args:
            envelope: Envelope domain model with updated data
            
        Returns:
            Envelope: Updated envelope
            
        Raises:
            ValueError: If envelope not found
        """
        query = select(EnvelopeModel).where(
            EnvelopeModel.envelope_id == envelope.envelope_id
        )
        result = await self.session.execute(query)
        db_envelope = result.scalar_one_or_none()
        
        if db_envelope is None:
            raise ValueError(f"Envelope {envelope.envelope_id} not found")
        
        # Update fields
        db_envelope.subject = envelope.subject
        db_envelope.message = envelope.message
        db_envelope.status = envelope.status.value
        db_envelope.signing_order = envelope.signing_order.value
        db_envelope.expiration_days = envelope.expiration_days
        db_envelope.expires_at = envelope.expires_at
        db_envelope.void_reason = envelope.void_reason
        db_envelope.sent_at = envelope.sent_at
        db_envelope.completed_at = envelope.completed_at
        db_envelope.voided_at = envelope.voided_at
        db_envelope.expired_at = envelope.expired_at
        db_envelope.updated_at = envelope.updated_at
        
        await self.session.flush()
        await self.session.refresh(db_envelope)
        
        logger.info(f"Updated envelope {envelope.envelope_id}")
        return self._envelope_to_domain(db_envelope)

    async def delete_envelope(self, envelope_id: UUID) -> bool:
        """
        Delete an envelope (hard delete).
        
        Args:
            envelope_id: Envelope UUID
            
        Returns:
            bool: True if deleted, False if not found
        """
        query = select(EnvelopeModel).where(EnvelopeModel.envelope_id == envelope_id)
        result = await self.session.execute(query)
        db_envelope = result.scalar_one_or_none()
        
        if db_envelope is None:
            return False
        
        await self.session.delete(db_envelope)
        await self.session.flush()
        
        logger.info(f"Deleted envelope {envelope_id}")
        return True

    async def list_envelopes(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[EnvelopeStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Envelope], int]:
        """
        List envelopes with pagination and filtering.
        
        Args:
            user_id: Filter by sender user ID
            status: Filter by envelope status
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Tuple[List[Envelope], int]: (envelopes, total_count)
        """
        query = select(EnvelopeModel)
        
        # Apply filters
        filters = []
        if user_id is not None:
            filters.append(EnvelopeModel.sender_id == user_id)
        if status is not None:
            filters.append(EnvelopeModel.status == status.value)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()
        
        # Apply pagination and ordering
        query = query.order_by(desc(EnvelopeModel.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Load relationships for list view
        query = query.options(
            selectinload(EnvelopeModel.envelope_documents),
            selectinload(EnvelopeModel.recipients)
        )
        
        result = await self.session.execute(query)
        db_envelopes = result.scalars().all()
        
        envelopes = [self._envelope_to_domain(e) for e in db_envelopes]
        
        return envelopes, total

    # ========================================================================
    # Recipient CRUD Operations
    # ========================================================================

    async def create_recipient(self, recipient: Recipient) -> Recipient:
        """
        Create a new recipient.
        
        Args:
            recipient: Recipient domain model
            
        Returns:
            Recipient: Created recipient
        """
        db_recipient = RecipientModel(
            recipient_id=recipient.recipient_id,
            envelope_id=recipient.envelope_id,
            user_id=recipient.user_id,
            name=recipient.name,
            email=recipient.email,
            phone=recipient.phone,
            role=recipient.role.value,
            signing_order=recipient.signing_order,
            status=recipient.status.value,
            access_code=recipient.access_code,
            access_code_hash=recipient.access_code_hash,
            decline_reason=recipient.decline_reason,
            sent_at=recipient.sent_at,
            viewed_at=recipient.viewed_at,
            signed_at=recipient.signed_at,
            declined_at=recipient.declined_at,
            created_at=recipient.created_at,
            updated_at=recipient.updated_at,
        )
        
        self.session.add(db_recipient)
        await self.session.flush()
        await self.session.refresh(db_recipient)
        
        logger.info(f"Created recipient {recipient.recipient_id} for envelope {recipient.envelope_id}")
        return self._recipient_to_domain(db_recipient)

    async def get_recipient_by_id(self, recipient_id: UUID) -> Optional[Recipient]:
        """
        Get recipient by ID.
        
        Args:
            recipient_id: Recipient UUID
            
        Returns:
            Optional[Recipient]: Recipient if found, None otherwise
        """
        query = select(RecipientModel).where(RecipientModel.recipient_id == recipient_id)
        result = await self.session.execute(query)
        db_recipient = result.scalar_one_or_none()
        
        if db_recipient is None:
            return None
        
        return self._recipient_to_domain(db_recipient)

    async def update_recipient(self, recipient: Recipient) -> Recipient:
        """
        Update an existing recipient.
        
        Args:
            recipient: Recipient domain model with updated data
            
        Returns:
            Recipient: Updated recipient
            
        Raises:
            ValueError: If recipient not found
        """
        query = select(RecipientModel).where(
            RecipientModel.recipient_id == recipient.recipient_id
        )
        result = await self.session.execute(query)
        db_recipient = result.scalar_one_or_none()
        
        if db_recipient is None:
            raise ValueError(f"Recipient {recipient.recipient_id} not found")
        
        # Update fields
        db_recipient.name = recipient.name
        db_recipient.email = recipient.email
        db_recipient.phone = recipient.phone
        db_recipient.role = recipient.role.value
        db_recipient.signing_order = recipient.signing_order
        db_recipient.status = recipient.status.value
        db_recipient.decline_reason = recipient.decline_reason
        db_recipient.sent_at = recipient.sent_at
        db_recipient.viewed_at = recipient.viewed_at
        db_recipient.signed_at = recipient.signed_at
        db_recipient.declined_at = recipient.declined_at
        db_recipient.updated_at = recipient.updated_at
        
        await self.session.flush()
        await self.session.refresh(db_recipient)
        
        logger.info(f"Updated recipient {recipient.recipient_id}")
        return self._recipient_to_domain(db_recipient)

    async def get_recipients_by_envelope(self, envelope_id: UUID) -> List[Recipient]:
        """
        Get all recipients for an envelope.
        
        Args:
            envelope_id: Envelope UUID
            
        Returns:
            List[Recipient]: List of recipients ordered by signing_order
        """
        query = select(RecipientModel).where(
            RecipientModel.envelope_id == envelope_id
        ).order_by(RecipientModel.signing_order, RecipientModel.created_at)
        
        result = await self.session.execute(query)
        db_recipients = result.scalars().all()
        
        return [self._recipient_to_domain(r) for r in db_recipients]

    async def get_recipient_by_access_code_hash(
        self,
        envelope_id: UUID,
        access_code_hash: str
    ) -> Optional[Recipient]:
        """
        Get recipient by envelope ID and access code hash.
        
        Args:
            envelope_id: Envelope UUID
            access_code_hash: SHA-256 hash of access code
            
        Returns:
            Optional[Recipient]: Recipient if found, None otherwise
        """
        query = select(RecipientModel).where(
            and_(
                RecipientModel.envelope_id == envelope_id,
                RecipientModel.access_code_hash == access_code_hash
            )
        )
        result = await self.session.execute(query)
        db_recipient = result.scalar_one_or_none()
        
        if db_recipient is None:
            return None
        
        return self._recipient_to_domain(db_recipient)

    # ========================================================================
    # Envelope-Document Association Operations
    # ========================================================================

    async def add_document_to_envelope(
        self,
        envelope_document: EnvelopeDocument
    ) -> EnvelopeDocument:
        """
        Add a document to an envelope.
        
        Args:
            envelope_document: EnvelopeDocument domain model
            
        Returns:
            EnvelopeDocument: Created association
        """
        db_envelope_doc = EnvelopeDocumentModel(
            envelope_document_id=envelope_document.envelope_document_id,
            envelope_id=envelope_document.envelope_id,
            document_id=envelope_document.document_id,
            display_order=envelope_document.display_order,
            created_at=envelope_document.created_at,
        )
        
        self.session.add(db_envelope_doc)
        await self.session.flush()
        await self.session.refresh(db_envelope_doc)
        
        # Increment document usage counter
        await self._increment_document_usage(envelope_document.document_id, 1)
        
        logger.info(
            f"Added document {envelope_document.document_id} "
            f"to envelope {envelope_document.envelope_id}"
        )
        return self._envelope_document_to_domain(db_envelope_doc)

    async def remove_document_from_envelope(
        self,
        envelope_id: UUID,
        document_id: UUID
    ) -> bool:
        """
        Remove a document from an envelope.
        
        Args:
            envelope_id: Envelope UUID
            document_id: Document UUID
            
        Returns:
            bool: True if removed, False if not found
        """
        query = select(EnvelopeDocumentModel).where(
            and_(
                EnvelopeDocumentModel.envelope_id == envelope_id,
                EnvelopeDocumentModel.document_id == document_id
            )
        )
        result = await self.session.execute(query)
        db_envelope_doc = result.scalar_one_or_none()
        
        if db_envelope_doc is None:
            return False
        
        await self.session.delete(db_envelope_doc)
        await self.session.flush()
        
        # Decrement document usage counter
        await self._increment_document_usage(document_id, -1)
        
        logger.info(f"Removed document {document_id} from envelope {envelope_id}")
        return True

    async def get_envelope_documents(self, envelope_id: UUID) -> List[dict]:
        """
        Get all documents in an envelope with metadata.
        
        Args:
            envelope_id: Envelope UUID
            
        Returns:
            List[dict]: List of document info with metadata
        """
        query = (
            select(
                DocumentModel.document_id,
                DocumentModel.name,
                DocumentModel.page_count,
                EnvelopeDocumentModel.display_order
            )
            .join(
                EnvelopeDocumentModel,
                EnvelopeDocumentModel.document_id == DocumentModel.document_id
            )
            .where(EnvelopeDocumentModel.envelope_id == envelope_id)
            .order_by(EnvelopeDocumentModel.display_order)
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [
            {
                "document_id": row.document_id,
                "name": row.name,
                "page_count": row.page_count,
                "display_order": row.display_order,
            }
            for row in rows
        ]

    # ========================================================================
    # Query Operations
    # ========================================================================

    async def get_envelopes_by_recipient_email(
        self,
        email: str,
        status: Optional[RecipientStatus] = None
    ) -> List[Envelope]:
        """
        Get envelopes where user is a recipient.
        
        Args:
            email: Recipient email address
            status: Optional filter by recipient status
            
        Returns:
            List[Envelope]: List of envelopes
        """
        query = (
            select(EnvelopeModel)
            .join(RecipientModel)
            .where(RecipientModel.email == email)
        )
        
        if status is not None:
            query = query.where(RecipientModel.status == status.value)
        
        query = query.options(
            selectinload(EnvelopeModel.envelope_documents),
            selectinload(EnvelopeModel.recipients)
        ).order_by(desc(EnvelopeModel.created_at))
        
        result = await self.session.execute(query)
        db_envelopes = result.scalars().unique().all()
        
        return [self._envelope_to_domain(e) for e in db_envelopes]

    async def count_pending_recipients(self, envelope_id: UUID) -> int:
        """
        Count recipients who haven't signed yet.
        
        Args:
            envelope_id: Envelope UUID
            
        Returns:
            int: Number of pending recipients
        """
        query = select(func.count()).where(
            and_(
                RecipientModel.envelope_id == envelope_id,
                RecipientModel.role == RecipientRole.SIGNER.value,
                RecipientModel.status.in_([
                    RecipientStatus.PENDING.value,
                    RecipientStatus.SENT.value,
                    RecipientStatus.VIEWED.value
                ])
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one()

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _increment_document_usage(self, document_id: UUID, delta: int) -> None:
        """
        Increment or decrement document usage counter.
        
        Args:
            document_id: Document UUID
            delta: Amount to change (positive or negative)
        """
        query = select(DocumentModel).where(DocumentModel.document_id == document_id)
        result = await self.session.execute(query)
        db_document = result.scalar_one_or_none()
        
        if db_document:
            db_document.in_use_by_envelopes += delta
            await self.session.flush()

    def _envelope_to_domain(self, db_envelope: EnvelopeModel) -> Envelope:
        """Convert database model to domain model."""
        return Envelope(
            envelope_id=db_envelope.envelope_id,
            sender_id=db_envelope.sender_id,
            subject=db_envelope.subject,
            message=db_envelope.message,
            status=EnvelopeStatus(db_envelope.status),
            signing_order=SigningOrder(db_envelope.signing_order),
            expiration_days=db_envelope.expiration_days,
            expires_at=db_envelope.expires_at,
            void_reason=db_envelope.void_reason,
            created_at=db_envelope.created_at,
            sent_at=db_envelope.sent_at,
            completed_at=db_envelope.completed_at,
            voided_at=db_envelope.voided_at,
            expired_at=db_envelope.expired_at,
            updated_at=db_envelope.updated_at,
        )

    def _recipient_to_domain(self, db_recipient: RecipientModel) -> Recipient:
        """Convert database model to domain model."""
        return Recipient(
            recipient_id=db_recipient.recipient_id,
            envelope_id=db_recipient.envelope_id,
            user_id=db_recipient.user_id,
            name=db_recipient.name,
            email=db_recipient.email,
            phone=db_recipient.phone,
            role=RecipientRole(db_recipient.role),
            signing_order=db_recipient.signing_order,
            status=RecipientStatus(db_recipient.status),
            access_code=db_recipient.access_code,
            access_code_hash=db_recipient.access_code_hash,
            decline_reason=db_recipient.decline_reason,
            sent_at=db_recipient.sent_at,
            viewed_at=db_recipient.viewed_at,
            signed_at=db_recipient.signed_at,
            declined_at=db_recipient.declined_at,
            created_at=db_recipient.created_at,
            updated_at=db_recipient.updated_at,
        )

    def _envelope_document_to_domain(
        self,
        db_envelope_doc: EnvelopeDocumentModel
    ) -> EnvelopeDocument:
        """Convert database model to domain model."""
        return EnvelopeDocument(
            envelope_document_id=db_envelope_doc.envelope_document_id,
            envelope_id=db_envelope_doc.envelope_id,
            document_id=db_envelope_doc.document_id,
            display_order=db_envelope_doc.display_order,
            created_at=db_envelope_doc.created_at,
        )
