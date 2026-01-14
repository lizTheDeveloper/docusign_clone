"""PDF processing service for validation, metadata extraction, and thumbnail generation."""
import io
import logging
from typing import BinaryIO, Optional, Tuple

import magic
from PIL import Image
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

logger = logging.getLogger(__name__)


class PdfProcessingError(Exception):
    """Base exception for PDF processing errors."""
    pass


class PdfValidationError(PdfProcessingError):
    """Exception raised when PDF validation fails."""
    pass


class PdfService:
    """
    Service for PDF document processing operations.
    
    Provides PDF validation, metadata extraction, and thumbnail generation
    with proper error handling.
    """

    # Standard PDF page sizes in points (1 point = 1/72 inch)
    STANDARD_PAGE_SIZES = {
        'Letter': (612, 792),
        'Legal': (612, 1008),
        'A4': (595, 842),
    }

    def __init__(self):
        """Initialize PDF service."""
        logger.info("PdfService initialized")

    def validate_file_signature(self, file_content: bytes) -> Tuple[bool, Optional[str], str]:
        """
        Validate file signature (magic bytes) to verify actual file type.
        
        Args:
            file_content: Binary file content
            
        Returns:
            tuple: (is_valid, error_message, detected_mime_type)
        """
        try:
            # Detect MIME type from file content
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_buffer(file_content)
            
            # PDF files should have application/pdf MIME type
            if detected_mime == 'application/pdf':
                return True, None, detected_mime
            
            # Office document types
            office_types = {
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel',
                'application/zip',  # Office files are zip archives
            }
            
            if detected_mime in office_types:
                return True, None, detected_mime
            
            return False, f"Invalid file type. Detected: {detected_mime}", detected_mime
            
        except Exception as e:
            logger.error(f"Failed to validate file signature: {str(e)}")
            return False, "Failed to validate file type", "unknown"

    def validate_pdf_structure(self, file_content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate PDF structure and check for encryption.
        
        Args:
            file_content: Binary PDF content
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            pdf_reader = PdfReader(io.BytesIO(file_content))
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                return False, "Password-protected PDFs are not supported"
            
            # Validate we can read at least one page
            if len(pdf_reader.pages) == 0:
                return False, "PDF has no pages"
            
            # Try to access first page to ensure it's readable
            _ = pdf_reader.pages[0]
            
            return True, None
            
        except PdfReadError as e:
            error_msg = f"Invalid or corrupted PDF: {str(e)}"
            logger.warning(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to validate PDF structure: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def extract_pdf_metadata(self, file_content: bytes) -> dict:
        """
        Extract metadata from PDF document.
        
        Args:
            file_content: Binary PDF content
            
        Returns:
            dict: Metadata including page count, dimensions, etc.
            
        Raises:
            PdfProcessingError: If metadata extraction fails
        """
        try:
            pdf_reader = PdfReader(io.BytesIO(file_content))
            
            page_count = len(pdf_reader.pages)
            pages = []
            
            # Extract metadata for each page
            for page_num in range(page_count):
                page = pdf_reader.pages[page_num]
                
                # Get page dimensions (in points)
                media_box = page.mediabox
                width = float(media_box.width)
                height = float(media_box.height)
                
                pages.append({
                    'page_number': page_num + 1,  # 1-indexed
                    'width': width,
                    'height': height,
                })
            
            # Extract document metadata
            metadata = {
                'page_count': page_count,
                'pages': pages,
            }
            
            # Add document info if available
            if pdf_reader.metadata:
                info = pdf_reader.metadata
                metadata['author'] = info.get('/Author', None)
                metadata['title'] = info.get('/Title', None)
                metadata['subject'] = info.get('/Subject', None)
                metadata['creator'] = info.get('/Creator', None)
                metadata['producer'] = info.get('/Producer', None)
            
            logger.info(f"Extracted metadata for {page_count}-page PDF")
            return metadata
            
        except Exception as e:
            error_msg = f"Failed to extract PDF metadata: {str(e)}"
            logger.error(error_msg)
            raise PdfProcessingError(error_msg) from e

    def generate_thumbnail(
        self,
        file_content: bytes,
        page_number: int = 1,
        max_size: tuple = (200, 200)
    ) -> bytes:
        """
        Generate thumbnail image from PDF page.
        
        Note: This is a simplified implementation. For production,
        consider using pdf2image or similar library for better quality.
        
        Args:
            file_content: Binary PDF content
            page_number: Page number to generate thumbnail from (1-indexed)
            max_size: Maximum thumbnail dimensions (width, height)
            
        Returns:
            bytes: JPEG thumbnail image data
            
        Raises:
            PdfProcessingError: If thumbnail generation fails
        """
        try:
            # For now, create a placeholder thumbnail
            # In production, use pdf2image or similar
            thumbnail = Image.new('RGB', max_size, color='white')
            
            # Add text to indicate it's a placeholder
            # In production, render actual PDF page
            
            # Convert to JPEG bytes
            output = io.BytesIO()
            thumbnail.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            logger.info(f"Generated thumbnail for page {page_number}")
            return output.getvalue()
            
        except Exception as e:
            error_msg = f"Failed to generate thumbnail: {str(e)}"
            logger.error(error_msg)
            raise PdfProcessingError(error_msg) from e

    def extract_text(self, file_content: bytes, page_number: Optional[int] = None) -> str:
        """
        Extract text content from PDF.
        
        Args:
            file_content: Binary PDF content
            page_number: Optional specific page number (1-indexed). If None, extracts all pages.
            
        Returns:
            str: Extracted text content
            
        Raises:
            PdfProcessingError: If text extraction fails
        """
        try:
            pdf_reader = PdfReader(io.BytesIO(file_content))
            
            if page_number is not None:
                # Extract from specific page
                page_idx = page_number - 1  # Convert to 0-indexed
                if page_idx < 0 or page_idx >= len(pdf_reader.pages):
                    raise PdfProcessingError(f"Invalid page number: {page_number}")
                
                page = pdf_reader.pages[page_idx]
                text = page.extract_text()
            else:
                # Extract from all pages
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            logger.info(f"Extracted text from PDF (length: {len(text)})")
            return text.strip()
            
        except PdfProcessingError:
            raise
        except Exception as e:
            error_msg = f"Failed to extract text from PDF: {str(e)}"
            logger.error(error_msg)
            raise PdfProcessingError(error_msg) from e

    def check_for_malicious_content(self, file_content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Basic security check for potentially malicious PDF content.
        
        This is a simplified check. In production, integrate with proper
        antivirus/malware scanning service.
        
        Args:
            file_content: Binary PDF content
            
        Returns:
            tuple: (is_safe, warning_message)
        """
        try:
            pdf_reader = PdfReader(io.BytesIO(file_content))
            
            # Check for JavaScript (can be used maliciously)
            for page in pdf_reader.pages:
                if '/JS' in page or '/JavaScript' in page:
                    logger.warning("PDF contains JavaScript")
                    return False, "PDF contains potentially unsafe JavaScript"
            
            # Check for embedded files
            if '/EmbeddedFiles' in pdf_reader.trailer.get('/Root', {}):
                logger.warning("PDF contains embedded files")
                return False, "PDF contains embedded files"
            
            # Check for launch actions (can execute external programs)
            for page in pdf_reader.pages:
                if '/Launch' in page:
                    logger.warning("PDF contains launch actions")
                    return False, "PDF contains potentially unsafe launch actions"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error during security check: {str(e)}")
            # If we can't verify, fail closed for security
            return False, "Unable to verify PDF security"

    def get_pdf_info(self, file_content: bytes) -> dict:
        """
        Get comprehensive PDF information.
        
        Combines validation, metadata extraction, and security checks.
        
        Args:
            file_content: Binary PDF content
            
        Returns:
            dict: Comprehensive PDF information
            
        Raises:
            PdfValidationError: If PDF is invalid or unsafe
        """
        # Validate file signature
        is_valid_sig, sig_error, mime_type = self.validate_file_signature(file_content)
        if not is_valid_sig:
            raise PdfValidationError(sig_error or "Invalid file signature")
        
        # Only process PDFs, not other office formats
        if mime_type != 'application/pdf':
            raise PdfValidationError("Only PDF files can be processed")
        
        # Validate PDF structure
        is_valid_struct, struct_error = self.validate_pdf_structure(file_content)
        if not is_valid_struct:
            raise PdfValidationError(struct_error or "Invalid PDF structure")
        
        # Security check
        is_safe, safety_error = self.check_for_malicious_content(file_content)
        if not is_safe:
            raise PdfValidationError(safety_error or "Security threat detected")
        
        # Extract metadata
        metadata = self.extract_pdf_metadata(file_content)
        
        return {
            'mime_type': mime_type,
            'is_valid': True,
            'is_safe': True,
            'metadata': metadata,
        }
