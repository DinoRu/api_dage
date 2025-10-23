"""File upload service."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status

from app.config import settings
from app.core.exceptions import BadRequestException


class UploadService:
    """File upload service for S3."""
    
    def __init__(self):
        if settings.S3_ENABLED:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
                config=BotoConfig(
                signature_version="s3v4",
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
                s3={
                    "addressing_style": "path",
                    "payload_signing_enabled": True,
                },
            ),
            )
        else:
            self.s3_client = None
    
    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to start
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise BadRequestException(
                f"File size ({file_size} bytes) exceeds maximum allowed size "
                f"({settings.MAX_UPLOAD_SIZE} bytes)"
            )
        
        # Check content type
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise BadRequestException(
                f"File type '{file.content_type}' not allowed. "
                f"Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
            )
    
    def _generate_filename(self, original_filename: str, folder: str) -> str:
        """Generate unique filename."""
        # Get file extension
        ext = Path(original_filename).suffix.lower()
        
        # Generate unique name with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{folder}/{timestamp}_{unique_id}{ext}"
    
    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "uploads"
    ) -> str:
        """
        Upload file to S3.
        
        Returns:
            str: Public URL of uploaded file
        """
        if not settings.S3_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="File upload is not configured"
            )

        # Validate file
        self._validate_file(file)

        # Generate filename
        filename = self._generate_filename(file.filename, folder)

        try:
            # Upload to S3
            self.s3_client.upload_fileobj(
                file.file,
                settings.S3_BUCKET_NAME,
                filename,
                ExtraArgs={
                    'ContentType': file.content_type,
                    # 'ACL': 'public-read'  # Make file publicly accessible
                }
            )
            
            # Generate public URL
            url = f"{settings.S3_BASE_URL}/{filename}"
            
            return url
            
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    async def upload_multiple_files(
        self,
        files: list[UploadFile],
        folder: str = "uploads"
    ) -> list[str]:
        """
        Upload multiple files to S3.
        
        Returns:
            list[str]: List of public URLs
        """
        urls = []
        
        for file in files:
            url = await self.upload_file(file, folder)
            urls.append(url)
        
        return urls
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file from S3."""
        if not settings.S3_ENABLED:
            return False
        
        try:
            # Extract filename from URL
            filename = file_url.replace(f"{settings.S3_BASE_URL}/", "")
            
            # Delete from S3
            self.s3_client.delete_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=filename
            )
            
            return True
            
        except ClientError:
            return False
    
    async def delete_multiple_files(self, file_urls: list[str]) -> int:
        """
        Delete multiple files from S3.
        
        Returns:
            int: Number of files successfully deleted
        """
        deleted_count = 0
        
        for url in file_urls:
            if await self.delete_file(url):
                deleted_count += 1
        
        return deleted_count


upload_service = UploadService()