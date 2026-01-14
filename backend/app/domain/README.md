# Document Management Implementation

This directory contains the implementation of the document management system for the DocuSign Clone application.

## Overview

The document management system provides secure document upload, storage, retrieval, and management capabilities for PDF and Office documents. It includes:

- Document upload with validation (size, type, security)
- PDF processing and metadata extraction
- Secure S3 storage with encryption at rest
- Presigned URL generation for downloads and previews
- Document listing with pagination and search
- Soft delete with 30-day retention
- Integration with envelope management (prevents deletion of documents in use)

## Architecture

The implementation follows clean architecture principles with clear separation of concerns:

### Domain Layer (`app/domain/models/`)
- **document.py**: Domain models with business logic
  - `Document`: Core document entity with validation and lifecycle methods
  - `DocumentPage`: Individual page metadata
  - `DocumentStatus`: Enum for processing states

### Infrastructure Layer (`app/infrastructure/`)

#### Models (`models.py`)
- `DocumentModel`: SQLAlchemy ORM model for documents table
- `DocumentPageModel`: SQLAlchemy ORM model for document_pages table

#### Repositories (`repositories/document_repository.py`)
- `DocumentRepository`: Database operations
  - CRUD operations for documents and pages
  - Pagination and search
  - Soft delete support

#### Services
- **storage_service.py**: S3 operations
  - Upload/download files
  - Generate presigned URLs
  - Encryption at rest (AES-256)
  
- **pdf_service.py**: PDF processing
  - File signature validation
  - PDF structure validation
  - Metadata extraction (page count, dimensions)
  - Thumbnail generation
  - Security checks (JavaScript, embedded files)

### Application Layer (`app/application/services/`)
- **document_service.py**: Business logic orchestration
  - Coordinates between storage, PDF processing, and database
  - Handles document upload workflow
  - Enforces permissions and ownership
  - Manages document lifecycle

### API Layer (`app/api/v1/endpoints/`)
- **documents.py**: REST API endpoints
  - `POST /documents` - Upload document
  - `GET /documents/{id}` - Get document metadata
  - `GET /documents/{id}/download` - Download document
  - `GET /documents/{id}/preview` - Get preview URL
  - `DELETE /documents/{id}` - Delete document
  - `GET /documents` - List documents with pagination

## Database Schema

### documents table
```sql
- document_id (UUID, primary key)
- user_id (UUID, foreign key to users)
- name (VARCHAR)
- original_filename (VARCHAR)
- storage_key (VARCHAR) - S3 object key
- file_type (VARCHAR) - MIME type
- file_size (BIGINT)
- page_count (INTEGER)
- checksum (VARCHAR) - SHA-256
- encryption_key_id (VARCHAR, optional)
- status (VARCHAR) - processing/ready/failed
- error_message (TEXT, optional)
- thumbnail_storage_key (VARCHAR, optional)
- in_use_by_envelopes (INTEGER) - Prevents deletion
- uploaded_at (TIMESTAMP)
- deleted_at (TIMESTAMP, optional) - Soft delete
```

### document_pages table
```sql
- page_id (UUID, primary key)
- document_id (UUID, foreign key)
- page_number (INTEGER)
- width (FLOAT) - Pixels
- height (FLOAT) - Pixels
- thumbnail_storage_key (VARCHAR, optional)
- created_at (TIMESTAMP)
```

## Configuration

Required environment variables (add to `.env`):

```bash
# S3 Storage
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_ENDPOINT_URL=  # Optional, for S3-compatible services
S3_PRESIGNED_URL_EXPIRATION=3600  # 1 hour
```

## Security Features

1. **File Validation**
   - File size limits (50MB max)
   - MIME type validation
   - File signature (magic bytes) verification
   - Filename sanitization

2. **PDF Security Checks**
   - Rejects password-protected PDFs
   - Detects JavaScript in PDFs
   - Detects embedded files
   - Detects launch actions

3. **Storage Security**
   - Encryption at rest (AES-256)
   - Presigned URLs with expiration
   - Access control by user ownership

4. **API Security**
   - JWT authentication required
   - Permission checks (user can only access own documents)
   - Rate limiting
   - Input validation

## Usage Example

### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf" \
  -F "name=My Document"
```

### List Documents
```bash
curl -X GET "http://localhost:8000/api/v1/documents?page=1&limit=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Document Metadata
```bash
curl -X GET http://localhost:8000/api/v1/documents/{document_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Download Document
```bash
curl -X GET http://localhost:8000/api/v1/documents/{document_id}/download \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -L  # Follow redirect to presigned URL
```

### Delete Document
```bash
curl -X DELETE http://localhost:8000/api/v1/documents/{document_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Testing

Run document management tests:
```bash
pytest tests/test_documents.py -v
```

## Dependencies

New dependencies added to `requirements.txt`:
- `boto3` - AWS S3 SDK
- `PyPDF2` - PDF processing
- `python-magic` - File type detection
- `Pillow` - Image processing for thumbnails

## Migration

Apply database migration:
```bash
alembic upgrade head
```

The migration (`002_add_documents_tables.py`) creates:
- `documents` table with indexes
- `document_pages` table with unique constraint

## Future Enhancements

1. **Background Processing**: Move PDF processing to background workers (Celery)
2. **Advanced Thumbnails**: Use pdf2image for better quality thumbnails
3. **OCR**: Extract text from scanned PDFs
4. **Document Conversion**: Convert Office formats to PDF
5. **Virus Scanning**: Integrate with ClamAV or cloud antivirus
6. **Deduplication**: Check for duplicate uploads by checksum
7. **Versioning**: Support document versions
8. **Storage Quotas**: Enforce per-user storage limits
9. **Audit Trail**: Log all document access and modifications

## Notes

- Documents are soft-deleted (retained for 30 days)
- Documents in use by envelopes cannot be deleted
- Presigned URLs expire after 1 hour by default
- PDF processing happens synchronously (should be async in production)
- Thumbnail generation currently uses placeholder (should use pdf2image)
