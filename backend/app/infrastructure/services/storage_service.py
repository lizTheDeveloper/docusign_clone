"""Storage service for S3-compatible object storage operations."""
import logging
from datetime import datetime, timedelta
from typing import BinaryIO, Optional
from uuid import UUID

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class StorageServiceError(Exception):
    """Base exception for storage service errors."""
    pass


class StorageUploadError(StorageServiceError):
    """Exception raised when upload fails."""
    pass


class StorageDownloadError(StorageServiceError):
    """Exception raised when download fails."""
    pass


class StorageService:
    """
    Service for managing document storage in S3-compatible object storage.
    
    Handles file upload, download, presigned URL generation, and deletion
    with proper error handling and retry logic.
    """

    def __init__(
        self,
        bucket_name: str,
        region: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
    ):
        """
        Initialize storage service with S3 configuration.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            access_key: AWS access key ID
            secret_key: AWS secret access key
            endpoint_url: Optional custom endpoint (for S3-compatible services)
        """
        self.bucket_name = bucket_name
        self.region = region
        
        # Configure S3 client with retry logic
        config = Config(
            region_name=region,
            retries={
                'max_attempts': 3,
                'mode': 'standard'
            }
        )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            config=config
        )
        
        logger.info(f"StorageService initialized with bucket: {bucket_name}")

    def upload_file(
        self,
        file_content: BinaryIO,
        storage_key: str,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload file to S3 storage.
        
        Args:
            file_content: Binary file content
            storage_key: Unique key for storing the file
            content_type: MIME type of the file
            metadata: Optional metadata dict
            
        Returns:
            str: Storage key where file was stored
            
        Raises:
            StorageUploadError: If upload fails after retries
        """
        try:
            extra_args = {
                'ContentType': content_type,
                'ServerSideEncryption': 'AES256',  # Enable encryption at rest
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_fileobj(
                file_content,
                self.bucket_name,
                storage_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded file to {storage_key}")
            return storage_key
            
        except (BotoCoreError, ClientError) as e:
            error_msg = f"Failed to upload file to S3: {str(e)}"
            logger.error(error_msg)
            raise StorageUploadError(error_msg) from e

    def download_file(self, storage_key: str) -> bytes:
        """
        Download file from S3 storage.
        
        Args:
            storage_key: Key where file is stored
            
        Returns:
            bytes: File content
            
        Raises:
            StorageDownloadError: If download fails
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            
            file_content = response['Body'].read()
            logger.info(f"Successfully downloaded file from {storage_key}")
            return file_content
            
        except (BotoCoreError, ClientError) as e:
            error_msg = f"Failed to download file from S3: {str(e)}"
            logger.error(error_msg)
            raise StorageDownloadError(error_msg) from e

    def generate_presigned_url(
        self,
        storage_key: str,
        expiration: int = 3600,
        filename: Optional[str] = None,
    ) -> str:
        """
        Generate presigned URL for temporary file access.
        
        Args:
            storage_key: Key where file is stored
            expiration: URL expiration time in seconds (default 1 hour)
            filename: Optional filename for Content-Disposition header
            
        Returns:
            str: Presigned URL
            
        Raises:
            StorageServiceError: If URL generation fails
        """
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': storage_key,
            }
            
            # Add Content-Disposition if filename provided
            if filename:
                params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for {storage_key}, expires in {expiration}s")
            return presigned_url
            
        except (BotoCoreError, ClientError) as e:
            error_msg = f"Failed to generate presigned URL: {str(e)}"
            logger.error(error_msg)
            raise StorageServiceError(error_msg) from e

    def delete_file(self, storage_key: str) -> bool:
        """
        Delete file from S3 storage.
        
        Args:
            storage_key: Key where file is stored
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            StorageServiceError: If deletion fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            
            logger.info(f"Successfully deleted file {storage_key}")
            return True
            
        except (BotoCoreError, ClientError) as e:
            error_msg = f"Failed to delete file from S3: {str(e)}"
            logger.error(error_msg)
            raise StorageServiceError(error_msg) from e

    def file_exists(self, storage_key: str) -> bool:
        """
        Check if file exists in S3 storage.
        
        Args:
            storage_key: Key where file should be stored
            
        Returns:
            bool: True if file exists
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def get_file_metadata(self, storage_key: str) -> dict:
        """
        Get file metadata from S3.
        
        Args:
            storage_key: Key where file is stored
            
        Returns:
            dict: File metadata including size, content type, etc.
            
        Raises:
            StorageServiceError: If metadata retrieval fails
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            
            return {
                'size': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', ''),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {}),
            }
            
        except (BotoCoreError, ClientError) as e:
            error_msg = f"Failed to get file metadata: {str(e)}"
            logger.error(error_msg)
            raise StorageServiceError(error_msg) from e

    @staticmethod
    def generate_storage_key(user_id: UUID, document_id: UUID, filename: str) -> str:
        """
        Generate unique storage key for a document.
        
        Uses a hierarchical structure: users/{user_id}/documents/{document_id}/{filename}
        
        Args:
            user_id: User ID who owns the document
            document_id: Document ID
            filename: Sanitized filename
            
        Returns:
            str: Storage key
        """
        return f"users/{user_id}/documents/{document_id}/{filename}"

    @staticmethod
    def generate_thumbnail_key(user_id: UUID, document_id: UUID, page_number: int) -> str:
        """
        Generate storage key for document page thumbnail.
        
        Args:
            user_id: User ID who owns the document
            document_id: Document ID
            page_number: Page number
            
        Returns:
            str: Storage key for thumbnail
        """
        return f"users/{user_id}/documents/{document_id}/thumbnails/page_{page_number}.jpg"
