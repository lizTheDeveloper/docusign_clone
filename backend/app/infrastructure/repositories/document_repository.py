"""Repository for document database operations."""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.document import Document, DocumentPage, DocumentStatus
from app.infrastructure.models import DocumentModel, DocumentPageModel

logger = logging.getLogger(__name__)


class DocumentRepository:
    """
    Repository for document persistence operations.
    
    Handles all database operations for documents and document pages,
    including CRUD operations, queries, and pagination.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create_document(self, document: Document) -> Document:
        """
        Create a new document in the database.
        
        Args:
            document: Document domain model
            
        Returns:
            Document: Created document with DB-generated fields
        """
        db_document = DocumentModel(
            document_id=document.document_id,
            user_id=document.user_id,
            name=document.name,
            original_filename=document.original_filename,
            storage_key=document.storage_key,
            file_type=document.file_type,
            file_size=document.file_size,
            page_count=document.page_count,
            checksum=document.checksum,
            encryption_key_id=document.encryption_key_id,
            status=document.status.value,
            error_message=document.error_message,
            thumbnail_storage_key=document.thumbnail_storage_key,
            in_use_by_envelopes=document.in_use_by_envelopes,
            uploaded_at=document.uploaded_at,
            deleted_at=document.deleted_at,
        )
        
        self.session.add(db_document)
        await self.session.flush()
        await self.session.refresh(db_document)
        
        logger.info(f"Created document {document.document_id}")
        return self._to_domain(db_document)

    async def get_document_by_id(
        self,
        document_id: UUID,
        include_pages: bool = False,
        include_deleted: bool = False
    ) -> Optional[Document]:
        """
        Get document by ID.
        
        Args:
            document_id: Document UUID
            include_pages: Whether to eagerly load pages
            include_deleted: Whether to include soft-deleted documents
            
        Returns:
            Optional[Document]: Document if found, None otherwise
        """
        query = select(DocumentModel).where(DocumentModel.document_id == document_id)
        
        if not include_deleted:
            query = query.where(DocumentModel.deleted_at.is_(None))
        
        if include_pages:
            query = query.options(selectinload(DocumentModel.pages))
        
        result = await self.session.execute(query)
        db_document = result.scalar_one_or_none()
        
        if db_document is None:
            return None
        
        return self._to_domain(db_document)

    async def get_documents_by_user(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "uploaded_at",
        sort_order: str = "desc",
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> tuple[list[Document], int]:
        """
        Get paginated list of documents for a user.
        
        Args:
            user_id: User UUID
            page: Page number (1-indexed)
            limit: Items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            search: Optional search term for filename
            include_deleted: Whether to include soft-deleted documents
            
        Returns:
            tuple: (list of documents, total count)
        """
        # Base query
        query = select(DocumentModel).where(DocumentModel.user_id == user_id)
        count_query = select(func.count()).select_from(DocumentModel).where(
            DocumentModel.user_id == user_id
        )
        
        # Filter deleted
        if not include_deleted:
            query = query.where(DocumentModel.deleted_at.is_(None))
            count_query = count_query.where(DocumentModel.deleted_at.is_(None))
        
        # Search filter
        if search:
            search_filter = or_(
                DocumentModel.name.ilike(f"%{search}%"),
                DocumentModel.original_filename.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Sorting
        sort_column = getattr(DocumentModel, sort_by, DocumentModel.uploaded_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        # Execute queries
        result = await self.session.execute(query)
        db_documents = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar()
        
        documents = [self._to_domain(doc) for doc in db_documents]
        
        logger.info(f"Retrieved {len(documents)} documents for user {user_id}")
        return documents, total_count

    async def update_document(self, document: Document) -> Document:
        """
        Update existing document.
        
        Args:
            document: Document domain model with updates
            
        Returns:
            Document: Updated document
        """
        query = select(DocumentModel).where(
            DocumentModel.document_id == document.document_id
        )
        result = await self.session.execute(query)
        db_document = result.scalar_one_or_none()
        
        if db_document is None:
            raise ValueError(f"Document {document.document_id} not found")
        
        # Update fields
        db_document.name = document.name
        db_document.status = document.status.value
        db_document.page_count = document.page_count
        db_document.error_message = document.error_message
        db_document.thumbnail_storage_key = document.thumbnail_storage_key
        db_document.in_use_by_envelopes = document.in_use_by_envelopes
        db_document.deleted_at = document.deleted_at
        
        await self.session.flush()
        await self.session.refresh(db_document)
        
        logger.info(f"Updated document {document.document_id}")
        return self._to_domain(db_document)

    async def soft_delete_document(self, document_id: UUID) -> bool:
        """
        Soft delete a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            bool: True if deleted, False if not found
        """
        query = select(DocumentModel).where(DocumentModel.document_id == document_id)
        result = await self.session.execute(query)
        db_document = result.scalar_one_or_none()
        
        if db_document is None:
            return False
        
        db_document.deleted_at = datetime.utcnow()
        await self.session.flush()
        
        logger.info(f"Soft deleted document {document_id}")
        return True

    async def hard_delete_document(self, document_id: UUID) -> bool:
        """
        Permanently delete a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            bool: True if deleted, False if not found
        """
        query = select(DocumentModel).where(DocumentModel.document_id == document_id)
        result = await self.session.execute(query)
        db_document = result.scalar_one_or_none()
        
        if db_document is None:
            return False
        
        await self.session.delete(db_document)
        await self.session.flush()
        
        logger.info(f"Hard deleted document {document_id}")
        return True

    async def create_document_pages(self, pages: list[DocumentPage]) -> list[DocumentPage]:
        """
        Create multiple document pages.
        
        Args:
            pages: List of DocumentPage domain models
            
        Returns:
            list[DocumentPage]: Created pages
        """
        db_pages = [
            DocumentPageModel(
                page_id=page.page_id,
                document_id=page.document_id,
                page_number=page.page_number,
                width=page.width,
                height=page.height,
                thumbnail_storage_key=page.thumbnail_storage_key,
                created_at=page.created_at,
            )
            for page in pages
        ]
        
        self.session.add_all(db_pages)
        await self.session.flush()
        
        logger.info(f"Created {len(db_pages)} pages for document")
        return pages

    async def get_document_pages(self, document_id: UUID) -> list[DocumentPage]:
        """
        Get all pages for a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            list[DocumentPage]: List of pages ordered by page number
        """
        query = select(DocumentPageModel).where(
            DocumentPageModel.document_id == document_id
        ).order_by(DocumentPageModel.page_number)
        
        result = await self.session.execute(query)
        db_pages = result.scalars().all()
        
        return [self._page_to_domain(page) for page in db_pages]

    async def document_exists(self, document_id: UUID) -> bool:
        """
        Check if document exists.
        
        Args:
            document_id: Document UUID
            
        Returns:
            bool: True if exists
        """
        query = select(func.count()).select_from(DocumentModel).where(
            and_(
                DocumentModel.document_id == document_id,
                DocumentModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0

    async def get_documents_by_checksum(
        self,
        user_id: UUID,
        checksum: str
    ) -> list[Document]:
        """
        Find documents by checksum (for deduplication).
        
        Args:
            user_id: User UUID
            checksum: File checksum
            
        Returns:
            list[Document]: Documents with matching checksum
        """
        query = select(DocumentModel).where(
            and_(
                DocumentModel.user_id == user_id,
                DocumentModel.checksum == checksum,
                DocumentModel.deleted_at.is_(None)
            )
        )
        
        result = await self.session.execute(query)
        db_documents = result.scalars().all()
        
        return [self._to_domain(doc) for doc in db_documents]

    def _to_domain(self, db_document: DocumentModel) -> Document:
        """Convert database model to domain model."""
        return Document(
            document_id=db_document.document_id,
            user_id=db_document.user_id,
            name=db_document.name,
            original_filename=db_document.original_filename,
            storage_key=db_document.storage_key,
            file_type=db_document.file_type,
            file_size=db_document.file_size,
            page_count=db_document.page_count,
            checksum=db_document.checksum,
            encryption_key_id=db_document.encryption_key_id,
            status=DocumentStatus(db_document.status),
            error_message=db_document.error_message,
            thumbnail_storage_key=db_document.thumbnail_storage_key,
            in_use_by_envelopes=db_document.in_use_by_envelopes,
            uploaded_at=db_document.uploaded_at,
            deleted_at=db_document.deleted_at,
        )

    def _page_to_domain(self, db_page: DocumentPageModel) -> DocumentPage:
        """Convert database page model to domain model."""
        return DocumentPage(
            page_id=db_page.page_id,
            document_id=db_page.document_id,
            page_number=db_page.page_number,
            width=db_page.width,
            height=db_page.height,
            thumbnail_storage_key=db_page.thumbnail_storage_key,
            created_at=db_page.created_at,
        )
