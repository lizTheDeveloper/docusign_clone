"""Document domain models with business logic."""
import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class DocumentStatus(str, Enum):
    """Document processing status."""
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document:
    """
    Document domain model representing an uploaded document.
    
    Encapsulates document data and business logic for file management,
    security validation, and lifecycle operations.
    """

    # Constants
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    SUPPORTED_MIME_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/msword",  # .doc
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-excel",  # .xls
    }
    MAX_FILENAME_LENGTH = 255

    def __init__(
        self,
        document_id: UUID,
        user_id: UUID,
        name: str,
        original_filename: str,
        storage_key: str,
        file_type: str,
        file_size: int,
        checksum: str,
        page_count: int = 0,
        status: DocumentStatus = DocumentStatus.PROCESSING,
        error_message: Optional[str] = None,
        thumbnail_storage_key: Optional[str] = None,
        encryption_key_id: Optional[str] = None,
        in_use_by_envelopes: int = 0,
        uploaded_at: Optional[datetime] = None,
        deleted_at: Optional[datetime] = None,
    ):
        """Initialize Document domain model."""
        self.document_id = document_id
        self.user_id = user_id
        self.name = name
        self.original_filename = original_filename
        self.storage_key = storage_key
        self.file_type = file_type
        self.file_size = file_size
        self.checksum = checksum
        self.page_count = page_count
        self.status = status
        self.error_message = error_message
        self.thumbnail_storage_key = thumbnail_storage_key
        self.encryption_key_id = encryption_key_id
        self.in_use_by_envelopes = in_use_by_envelopes
        self.uploaded_at = uploaded_at or datetime.utcnow()
        self.deleted_at = deleted_at

    @staticmethod
    def validate_file_size(file_size: int) -> tuple[bool, Optional[str]]:
        """
        Validate file size is within allowed limits.
        
        Args:
            file_size: Size of file in bytes
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if file_size <= 0:
            return False, "File size must be greater than 0"
        
        if file_size > Document.MAX_FILE_SIZE:
            max_mb = Document.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File size exceeds maximum of {max_mb}MB"
        
        return True, None

    @staticmethod
    def validate_file_type(mime_type: str) -> tuple[bool, Optional[str]]:
        """
        Validate file type is supported.
        
        Args:
            mime_type: MIME type of the file
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if mime_type not in Document.SUPPORTED_MIME_TYPES:
            supported = ", ".join([
                "PDF", "DOC", "DOCX", "XLS", "XLSX"
            ])
            return False, f"File format not supported. Supported formats: {supported}"
        
        return True, None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent security issues.
        
        Removes special characters, path traversal attempts, and limits length.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove path components
        filename = filename.split("/")[-1].split("\\")[-1]
        
        # Remove or replace dangerous characters
        filename = filename.replace("..", "")
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        
        # Limit length
        if len(filename) > Document.MAX_FILENAME_LENGTH:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            max_name_len = Document.MAX_FILENAME_LENGTH - len(ext) - 1
            filename = f"{name[:max_name_len]}.{ext}" if ext else name[:Document.MAX_FILENAME_LENGTH]
        
        return filename.strip()

    @staticmethod
    def calculate_checksum(file_content: bytes) -> str:
        """
        Calculate SHA-256 checksum of file content.
        
        Args:
            file_content: Binary content of file
            
        Returns:
            str: Hexadecimal checksum
        """
        return hashlib.sha256(file_content).hexdigest()

    def can_be_deleted(self) -> tuple[bool, Optional[str]]:
        """
        Check if document can be deleted.
        
        Documents in use by envelopes cannot be deleted.
        
        Returns:
            tuple: (can_delete, error_message)
        """
        if self.in_use_by_envelopes > 0:
            return False, "Cannot delete document in use by envelope"
        
        return True, None

    def mark_ready(self, page_count: int, thumbnail_key: Optional[str] = None):
        """
        Mark document as ready after successful processing.
        
        Args:
            page_count: Number of pages in document
            thumbnail_key: Storage key for thumbnail image
        """
        self.status = DocumentStatus.READY
        self.page_count = page_count
        self.error_message = None
        if thumbnail_key:
            self.thumbnail_storage_key = thumbnail_key

    def mark_failed(self, error_message: str):
        """
        Mark document processing as failed.
        
        Args:
            error_message: Description of failure
        """
        self.status = DocumentStatus.FAILED
        self.error_message = error_message

    def soft_delete(self):
        """Soft delete the document by setting deleted_at timestamp."""
        self.deleted_at = datetime.utcnow()

    def is_deleted(self) -> bool:
        """Check if document is soft-deleted."""
        return self.deleted_at is not None

    def increment_envelope_usage(self):
        """Increment the count of envelopes using this document."""
        self.in_use_by_envelopes += 1

    def decrement_envelope_usage(self):
        """Decrement the count of envelopes using this document."""
        if self.in_use_by_envelopes > 0:
            self.in_use_by_envelopes -= 1


class DocumentPage:
    """
    Document page model representing a single page of a document.
    
    Stores page-specific metadata like dimensions and thumbnails.
    """

    def __init__(
        self,
        page_id: UUID,
        document_id: UUID,
        page_number: int,
        width: float,
        height: float,
        thumbnail_storage_key: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize DocumentPage model."""
        self.page_id = page_id
        self.document_id = document_id
        self.page_number = page_number
        self.width = width
        self.height = height
        self.thumbnail_storage_key = thumbnail_storage_key
        self.created_at = created_at or datetime.utcnow()

    @staticmethod
    def validate_dimensions(width: float, height: float) -> tuple[bool, Optional[str]]:
        """
        Validate page dimensions are positive values.
        
        Args:
            width: Page width in pixels
            height: Page height in pixels
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if width <= 0 or height <= 0:
            return False, "Page dimensions must be positive values"
        
        return True, None
