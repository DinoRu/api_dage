"""File upload endpoints."""

from typing import List

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUser
from app.config import settings
from app.services.upload_service import upload_service

router = APIRouter(prefix="/upload", tags=["File Upload"])


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: CurrentUser = None
):
    """
    Upload a single image file.
    
    **Restrictions**:
    - Max file size: 10MB (configurable)
    - Allowed formats: JPEG, PNG, WebP
    
    Returns:
    - **url**: Public URL of the uploaded file
    """
    url = await upload_service.upload_file(
        file,
        folder=settings.S3_FOLDER_READINGS
    )
    
    return {"url": url, "filename": file.filename}


@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_multiple_images(
    files: List[UploadFile] = File(..., description="Multiple image files"),
    current_user: CurrentUser = None
):
    """
    Upload multiple image files.
    
    **Restrictions**:
    - Max file size per file: 10MB (configurable)
    - Allowed formats: JPEG, PNG, WebP
    - Max 10 files per request
    
    Returns:
    - **urls**: List of public URLs
    - **count**: Number of files uploaded
    """
    if len(files) > 10:
        from app.core.exceptions import BadRequestException
        raise BadRequestException("Maximum 10 files allowed per request")
    
    urls = await upload_service.upload_multiple_files(
        files,
        folder=settings.S3_FOLDER_READINGS
    )
    
    return {
        "urls": urls,
        "count": len(urls),
        "filenames": [f.filename for f in files]
    }


@router.delete("/image")
async def delete_image(
    url: str,
    current_user: CurrentUser
):
    """
    Delete an uploaded image.
    
    **Note**: Only admins can delete files.
    """
    from app.api.deps import AdminUser
    
    success = await upload_service.delete_file(url)
    
    return {
        "success": success,
        "url": url,
        "message": "File deleted successfully" if success else "Failed to delete file"
    }