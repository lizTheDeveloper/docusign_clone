"""Document management API endpoints."""
import logging
from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import RedirectResponse

from app.api.deps import get_current_user, get_document_service
from app.application.services.document_service import (
    DocumentNotFoundError,
    DocumentPermissionError,
    DocumentService,
    DocumentServiceError,
    DocumentValidationError,
)
from app.domain.models.user import User
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentListItemSchema,
    DocumentListResponse,
    DocumentMetadataResponse,
    DocumentPageSchema,
    DocumentUploadResponse,
    DocumentValidationError as DocumentValidationErrorSchema,
    ErrorResponse,
    PaginationSchema,
    PreviewUrlResponse,
    UserInfoSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="Upload a PDF or Office document. Max file size: 50MB. Supported formats: PDF, DOC, DOCX, XLS, XLSX.",
    responses={
        201: {"description": "Document uploaded successfully"},
        400: {"description": "Invalid file format or validation error"},
        413: {"description": "File too large"},
        422: {"description": "Virus detected or corrupted file"},
    }
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    name: Optional[str] = Form(None, description="Optional custom name"),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    """
    Upload a new document.
    
    The document will be validated, virus scanned, and processed.
    PDF metadata including page count and dimensions will be extracted.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload document
        document = await document_service.upload_document(
            user_id=current_user.user_id,
            file_content=file_content,
            filename=file.filename or "document.pdf",
            mime_type=file.content_type or "application/pdf",
            name=name,
        )
        
        return DocumentUploadResponse(
            document_id=document.document_id,
            name=document.name,
            original_filename=document.original_filename,
            file_type=document.file_type,
            file_size=document.file_size,
            page_count=document.page_count,
            status=document.status.value,
            thumbnail_url=None,  # Will be populated after processing
            checksum=document.checksum,
            uploaded_at=document.uploaded_at,
        )
        
    except DocumentValidationError as e:
        logger.warning(f"Document validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except DocumentServiceError as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.get(
    "/{document_id}",
    response_model=DocumentMetadataResponse,
    summary="Get document metadata",
    description="Retrieve detailed metadata for a document including pages information.",
    responses={
        200: {"description": "Document metadata retrieved"},
        403: {"description": "Not authorized to access document"},
        404: {"description": "Document not found"},
    }
)
async def get_document_metadata(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentMetadataResponse:
    """Get detailed document metadata."""
    try:
        # Get document
        document = await document_service.get_document(
            document_id=document_id,
            user_id=current_user.user_id,
            include_pages=False,
        )
        
        # Get pages
        pages = await document_service.get_document_pages(
            document_id=document_id,
            user_id=current_user.user_id,
        )
        
        # Build response
        return DocumentMetadataResponse(
            document_id=document.document_id,
            name=document.name,
            original_filename=document.original_filename,
            file_type=document.file_type,
            file_size=document.file_size,
            page_count=document.page_count,
            status=document.status.value,
            thumbnail_url=None,  # TODO: Generate presigned URL
            checksum=document.checksum,
            uploaded_at=document.uploaded_at,
            uploaded_by=UserInfoSchema(
                user_id=current_user.user_id,
                name=current_user.full_name,
                email=current_user.email,
            ),
            pages=[
                DocumentPageSchema(
                    page_number=page.page_number,
                    width=page.width,
                    height=page.height,
                    thumbnail_url=None,  # TODO: Generate presigned URL
                )
                for page in pages
            ],
        )
        
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    except DocumentPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document",
        )
    except Exception as e:
        logger.error(f"Error retrieving document metadata: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document",
        )


@router.get(
    "/{document_id}/download",
    summary="Download document",
    description="Download document file. Returns a redirect to presigned URL.",
    responses={
        302: {"description": "Redirect to presigned download URL"},
        403: {"description": "Not authorized"},
        404: {"description": "Document not found"},
    }
)
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Download document file.
    
    Returns a redirect to a presigned URL valid for 1 hour.
    """
    try:
        download_url, expires_at = await document_service.get_download_url(
            document_id=document_id,
            user_id=current_user.user_id,
        )
        
        return RedirectResponse(url=download_url, status_code=status.HTTP_302_FOUND)
        
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    except DocumentPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document",
        )
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL",
        )


@router.get(
    "/{document_id}/preview",
    response_model=PreviewUrlResponse,
    summary="Get document preview URL",
    description="Get a presigned URL for document preview (valid for 1 hour).",
    responses={
        200: {"description": "Preview URL generated"},
        403: {"description": "Not authorized"},
        404: {"description": "Document not found"},
    }
)
async def get_document_preview(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> PreviewUrlResponse:
    """Get document preview URL."""
    try:
        preview_url, expires_at = await document_service.get_preview_url(
            document_id=document_id,
            user_id=current_user.user_id,
        )
        
        return PreviewUrlResponse(
            preview_url=preview_url,
            expires_at=expires_at,
        )
        
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    except DocumentPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document",
        )
    except Exception as e:
        logger.error(f"Error generating preview URL: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate preview URL",
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Delete a document. Only allowed if document is not used in any envelope.",
    responses={
        204: {"description": "Document deleted successfully"},
        403: {"description": "Not authorized or document in use"},
        404: {"description": "Document not found"},
        409: {"description": "Document is in use by envelope"},
    }
)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Delete a document.
    
    Documents that are in use by envelopes cannot be deleted.
    Deletion is soft-delete; document is retained for 30 days.
    """
    try:
        await document_service.delete_document(
            document_id=document_id,
            user_id=current_user.user_id,
        )
        
        return None  # 204 No Content
        
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    except DocumentPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document",
        )
    except DocumentServiceError as e:
        # Document in use
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List user documents",
    description="Get paginated list of user's documents with optional search and sorting.",
    responses={
        200: {"description": "Document list retrieved"},
    }
)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("uploaded_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    search: Optional[str] = Query(None, description="Search term for filename"),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """
    List user's documents with pagination.
    
    Supports searching by filename and sorting by various fields.
    """
    try:
        documents, total_count = await document_service.list_user_documents(
            user_id=current_user.user_id,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
        )
        
        # Calculate pagination metadata
        total_pages = ceil(total_count / limit) if total_count > 0 else 0
        
        return DocumentListResponse(
            documents=[
                DocumentListItemSchema(
                    document_id=doc.document_id,
                    name=doc.name,
                    file_size=doc.file_size,
                    page_count=doc.page_count,
                    uploaded_at=doc.uploaded_at,
                    thumbnail_url=None,  # TODO: Generate presigned URL
                )
                for doc in documents
            ],
            pagination=PaginationSchema(
                page=page,
                limit=limit,
                total_pages=total_pages,
                total_items=total_count,
            ),
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents",
        )
