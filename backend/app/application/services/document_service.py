"""Document business service for orchestrating document operations."""
import io
import logging
from datetime import datetime, timedelta
from typing import BinaryIO, Optional
from uuid import UUID, uuid4

from app.domain.models.document import Document, DocumentPage, DocumentStatus
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.services.pdf_service import PdfService, PdfValidationError
from app.infrastructure.services.storage_service import StorageService, StorageServiceError

logger = logging.getLogger(__name__)


class DocumentServiceError(Exception):
    """Base exception for document service errors."""
    pass


class DocumentValidationError(DocumentServiceError):
    """Exception raised when document validation fails."""
    pass


class DocumentNotFoundError(DocumentServiceError):
    """Exception raised when document is not found."""
    pass


class DocumentPermissionError(DocumentServiceError):
    """Exception raised when user lacks permission for document operation."""
    pass


class DocumentService:
    """
    Document business service for handling document operations.
    
    Orchestrates document upload, processing, retrieval, and deletion
    by coordinating between storage, PDF processing, and database operations.
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        storage_service: StorageService,
        pdf_service: PdfService,
    ):
        """
        Initialize document service.
        
        Args:
            document_repository: Repository for document persistence
            storage_service: Service for S3 storage operations
            pdf_service: Service for PDF processing
        """
        self.document_repository = document_repository
        self.storage_service = storage_service
        self.pdf_service = pdf_service

    async def upload_document(
        self,
        user_id: UUID,
        file_content: bytes,
        filename: str,
        mime_type: str,
        name: Optional[str] = None,
    ) -> Document:
        """
        Upload and process a new document.
        
        Validates file, uploads to storage, processes PDF, and saves metadata.
        
        Args:
            user_id: User ID uploading the document
            file_content: Binary file content
            filename: Original filename
            mime_type: MIME type
            name: Optional custom name (defaults to filename)
            
        Returns:
            Document: Created document with metadata
            
        Raises:
            DocumentValidationError: If validation fails
            DocumentServiceError: If upload or processing fails
        """
        try:
            # Validate file size
            file_size = len(file_content)
            is_valid_size, size_error = Document.validate_file_size(file_size)
            if not is_valid_size:
                raise DocumentValidationError(size_error)
            
            # Validate file type
            is_valid_type, type_error = Document.validate_file_type(mime_type)
            if not is_valid_type:
                raise DocumentValidationError(type_error)
            
            # Sanitize filename
            sanitized_filename = Document.sanitize_filename(filename)
            document_name = name or sanitized_filename
            
            # Calculate checksum
            checksum = Document.calculate_checksum(file_content)
            
            # Check for duplicate (optional deduplication)
            # Could check if same user already uploaded same file
            
            # Process PDF and validate
            try:
                pdf_info = self.pdf_service.get_pdf_info(file_content)
            except PdfValidationError as e:
                raise DocumentValidationError(str(e)) from e
            
            # Generate unique document ID
            document_id = uuid4()
            
            # Generate storage key
            storage_key = StorageService.generate_storage_key(
                user_id, document_id, sanitized_filename
            )
            
            # Upload to storage
            try:
                file_stream = io.BytesIO(file_content)
                self.storage_service.upload_file(
                    file_stream,
                    storage_key,
                    mime_type,
                    metadata={
                        'user_id': str(user_id),
                        'document_id': str(document_id),
                        'original_filename': filename,
                    }
                )
            except StorageServiceError as e:
                raise DocumentServiceError(f"Failed to upload file: {str(e)}") from e
            
            # Create document domain model
            document = Document(
                document_id=document_id,
                user_id=user_id,
                name=document_name,
                original_filename=filename,
                storage_key=storage_key,
                file_type=mime_type,
                file_size=file_size,
                checksum=checksum,
                page_count=0,
                status=DocumentStatus.PROCESSING,
            )
            
            # Save to database
            document = await self.document_repository.create_document(document)
            
            # Process document asynchronously (in real app, use background task)
            # For now, process synchronously
            await self._process_document(document, file_content, pdf_info)
            
            logger.info(f"Successfully uploaded document {document_id} for user {user_id}")
            return document
            
        except (DocumentValidationError, DocumentServiceError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading document: {str(e)}")
            raise DocumentServiceError(f"Failed to upload document: {str(e)}") from e

    async def _process_document(
        self,
        document: Document,
        file_content: bytes,
        pdf_info: dict
    ):
        """
        Process document after upload (extract metadata, generate thumbnails).
        
        Args:
            document: Document domain model
            file_content: Binary file content
            pdf_info: PDF information from validation
        """
        try:
            metadata = pdf_info['metadata']
            page_count = metadata['page_count']
            pages_info = metadata['pages']
            
            # Generate thumbnail for first page
            thumbnail_key = None
            try:
                thumbnail_data = self.pdf_service.generate_thumbnail(file_content)
                thumbnail_key = StorageService.generate_thumbnail_key(
                    document.user_id,
                    document.document_id,
                    1  # First page
                )
                
                thumbnail_stream = io.BytesIO(thumbnail_data)
                self.storage_service.upload_file(
                    thumbnail_stream,
                    thumbnail_key,
                    'image/jpeg'
                )
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail: {str(e)}")
                # Non-fatal, continue processing
            
            # Create page records
            pages = []
            for page_info in pages_info:
                page = DocumentPage(
                    page_id=uuid4(),
                    document_id=document.document_id,
                    page_number=page_info['page_number'],
                    width=page_info['width'],
                    height=page_info['height'],
                    thumbnail_storage_key=thumbnail_key if page_info['page_number'] == 1 else None,
                )
                pages.append(page)
            
            # Save pages to database
            await self.document_repository.create_document_pages(pages)
            
            # Update document status to ready
            document.mark_ready(page_count, thumbnail_key)
            await self.document_repository.update_document(document)
            
            logger.info(f"Successfully processed document {document.document_id}")
            
        except Exception as e:
            logger.error(f"Error processing document {document.document_id}: {str(e)}")
            document.mark_failed(str(e))
            await self.document_repository.update_document(document)

    async def get_document(
        self,
        document_id: UUID,
        user_id: UUID,
        include_pages: bool = False
    ) -> Document:
        """
        Get document by ID with permission check.
        
        Args:
            document_id: Document UUID
            user_id: Requesting user ID
            include_pages: Whether to include page metadata
            
        Returns:
            Document: Document with metadata
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentPermissionError: If user lacks permission
        """
        document = await self.document_repository.get_document_by_id(
            document_id,
            include_pages=include_pages
        )
        
        if document is None:
            raise DocumentNotFoundError(f"Document {document_id} not found")
        
        # Check permission
        if document.user_id != user_id:
            raise DocumentPermissionError("Not authorized to access this document")
        
        return document

    async def list_user_documents(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "uploaded_at",
        sort_order: str = "desc",
        search: Optional[str] = None,
    ) -> tuple[list[Document], int]:
        """
        List documents for a user with pagination.
        
        Args:
            user_id: User UUID
            page: Page number (1-indexed)
            limit: Items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            search: Optional search term
            
        Returns:
            tuple: (list of documents, total count)
        """
        documents, total_count = await self.document_repository.get_documents_by_user(
            user_id=user_id,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
        )
        
        return documents, total_count

    async def get_download_url(
        self,
        document_id: UUID,
        user_id: UUID,
        expiration: int = 3600,
    ) -> tuple[str, datetime]:
        """
        Generate presigned URL for document download.
        
        Args:
            document_id: Document UUID
            user_id: Requesting user ID
            expiration: URL expiration in seconds (default 1 hour)
            
        Returns:
            tuple: (presigned_url, expiration_datetime)
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentPermissionError: If user lacks permission
        """
        document = await self.get_document(document_id, user_id)
        
        # Generate presigned URL
        presigned_url = self.storage_service.generate_presigned_url(
            document.storage_key,
            expiration=expiration,
            filename=document.original_filename,
        )
        
        expires_at = datetime.utcnow() + timedelta(seconds=expiration)
        
        logger.info(f"Generated download URL for document {document_id}")
        return presigned_url, expires_at

    async def get_preview_url(
        self,
        document_id: UUID,
        user_id: UUID,
        expiration: int = 3600,
    ) -> tuple[str, datetime]:
        """
        Generate presigned URL for document preview.
        
        Args:
            document_id: Document UUID
            user_id: Requesting user ID
            expiration: URL expiration in seconds
            
        Returns:
            tuple: (presigned_url, expiration_datetime)
        """
        # Same as download but without Content-Disposition attachment header
        document = await self.get_document(document_id, user_id)
        
        presigned_url = self.storage_service.generate_presigned_url(
            document.storage_key,
            expiration=expiration,
        )
        
        expires_at = datetime.utcnow() + timedelta(seconds=expiration)
        
        return presigned_url, expires_at

    async def delete_document(
        self,
        document_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a document (soft delete if not in use).
        
        Args:
            document_id: Document UUID
            user_id: Requesting user ID
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentPermissionError: If user lacks permission
            DocumentServiceError: If document is in use
        """
        document = await self.get_document(document_id, user_id)
        
        # Check if can be deleted
        can_delete, error = document.can_be_deleted()
        if not can_delete:
            raise DocumentServiceError(error)
        
        # Soft delete
        document.soft_delete()
        await self.document_repository.update_document(document)
        
        logger.info(f"Soft deleted document {document_id}")
        return True

    async def get_document_pages(
        self,
        document_id: UUID,
        user_id: UUID,
    ) -> list[DocumentPage]:
        """
        Get all pages for a document.
        
        Args:
            document_id: Document UUID
            user_id: Requesting user ID
            
        Returns:
            list[DocumentPage]: List of pages
        """
        # Verify permission
        await self.get_document(document_id, user_id)
        
        pages = await self.document_repository.get_document_pages(document_id)
        return pages
