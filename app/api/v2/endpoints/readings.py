"""Reading endpoints with photo upload."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
import json

from fastapi import APIRouter, Query, status, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse

from app.api.deps import (
    DatabaseSession,
    CurrentUser,
    AdminUser,
    Pagination
)
from app.config import settings
from app.core.exceptions import ForbiddenException, BadRequestException
from app.core.pagination import PageResponse
from app.schema.reading import (
    ReadingCreate,
    ReadingCreateWithPhotos,
    ReadingUpdate,
    ReadingRead,
    ReadingReadWithMeter,
    ReadingReadWithController,
    ReadingReadWithRelations,
    ReadingStats
)
from app.services.reading import reading_service
from app.services.upload_service import upload_service

from sqlalchemy import select, desc
from app.models.readings import Reading
from app.services.meter_v2 import meter_service
    

router = APIRouter(prefix="/readings", tags=["Readings"])


@router.get("", response_model=PageResponse[ReadingRead])
async def list_readings(
    db: DatabaseSession,
    current_user: CurrentUser,
    pagination: Pagination,
    meter_id: Optional[UUID] = Query(None, description="Filter by meter ID"),
    city_id: Optional[UUID] = Query(None, description="Filter by city ID"),
    controller_id: Optional[UUID] = Query(None, description="Filter by controller ID"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)")
):
    """
    List all readings with pagination and filters.
    
    **Note**: Non-admin users can only see readings from their assigned city.
    """
    # Non-admin users can only see their city's readings
    if not current_user.is_admin():
        if city_id and city_id != current_user.city_id:
            raise ForbiddenException("Vous ne pouvez voir que les lectures de votre ville")
        city_id = current_user.city_id
    
    # Get by specific filter
    if meter_id:
        return await reading_service.get_by_meter(db, meter_id, pagination, start_date, end_date)
    
    if controller_id:
        return await reading_service.get_by_controller(db, controller_id, pagination, start_date, end_date)
    
    if city_id:
        return await reading_service.get_by_city(db, city_id, pagination, start_date, end_date)
    
    # Get all (admin only)
    filters = {}
    return await reading_service.get_multi(db, pagination, filters, order_by="-reading_date")


@router.post(
    "/with-photos",
    response_model=ReadingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create reading with photo upload"
)
async def create_reading_with_photos(
    db: DatabaseSession,
    current_user: CurrentUser,
    meter_id: UUID = Form(..., description="Meter ID"),
    reading_value: float = Form(..., ge=0, description="Reading value"),
    reading_date: datetime = Form(..., description="Reading date and time"),
    photos: List[UploadFile] = File(..., min_length=2, description="Photos (minimum 2 required)"),
    comment: Optional[str] = Form(None, max_length=1000, description="Optional comment"),
    latitude: Optional[float] = Form(None, ge=-90, le=90, description="GPS latitude"),
    longitude: Optional[float] = Form(None, ge=-180, le=180, description="GPS longitude")
):
    """
    Create a new reading with photo upload.
    
    **Process**:
    1. Validates meter access
    2. Uploads photos to S3
    3. Creates reading with photo URLs
    
    **Requirements**:
    - **meter_id**: ID of the meter
    - **reading_value**: Reading value (must be >= 0 and >= previous reading)
    - **reading_date**: Date and time of reading
    - **photos**: Minimum 2 photos (max 10MB each, formats: JPEG, PNG, WebP)
    - **comment**: Optional comment (max 1000 characters)
    - **latitude/longitude**: Optional GPS coordinates (both required if one is provided)
    
    **Photo Requirements**:
    - Minimum: 2 photos
    - Maximum: 10 photos per reading
    - Max size per photo: 10MB
    - Allowed formats: JPEG, PNG, WebP
    
    **Returns**:
    - Reading with uploaded photo URLs
    """
    # Validate number of photos
    if len(photos) < 2:
        raise BadRequestException(
            "Au minimum 2 photos sont requises pour chaque lecture"
        )
    
    if len(photos) > 10:
        raise BadRequestException(
            "Maximum 10 photos autorisées par lecture"
        )
    
    # Validate geolocation consistency
    if (latitude is None) != (longitude is None):
        raise BadRequestException(
            "La latitude et la longitude doivent être fournies ensemble"
        )
    
    # Upload photos to S3
    try:
        photo_urls = await upload_service.upload_multiple_files(
            photos,
            folder=f"{settings.S3_FOLDER_READINGS}/{meter_id}"
        )
    except Exception as e:
        raise BadRequestException(f"Erreur lors de l'upload des photos: {str(e)}")
    
    # Create reading data
    reading_data = ReadingCreateWithPhotos(
        meter_id=meter_id,
        reading_value=reading_value,
        reading_date=reading_date,
        comment=comment,
        latitude=latitude,
        longitude=longitude
    )
    
    # Create reading with photo URLs
    reading_create = ReadingCreate(
        **reading_data.model_dump(),
        photo_urls=photo_urls,
        controller_id=current_user.id
    )
    
    reading = await reading_service.create(db, reading_create, current_user)
    
    # Add photos count to response
    reading_dict = reading.__dict__.copy()
    reading_dict['photos_count'] = len(photo_urls)
    
    return reading


@router.post("", response_model=ReadingRead, status_code=status.HTTP_201_CREATED)
async def create_reading_with_urls(
    reading_in: ReadingCreate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Create a reading with pre-uploaded photo URLs.
    
    **Note**: Photos must already be uploaded to S3.
    Use `/readings/with-photos` endpoint for combined upload + creation.
    
    **Requirements**:
    - Minimum 2 photo URLs
    - All URLs must be valid S3 URLs
    """
    reading = await reading_service.create(db, reading_in, current_user)
    
    # Add photos count
    reading_dict = reading.__dict__.copy()
    reading_dict['photos_count'] = len(reading.photo_urls or [])
    
    return reading


@router.get("/{reading_id}", response_model=ReadingReadWithRelations)
async def get_reading(
    reading_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Get a reading by ID with all related data.
    
    Includes:
    - Meter information
    - Controller information
    - All photo URLs
    - GPS coordinates if available
    """
    reading = await reading_service.get_or_404(
        db,
        reading_id,
        relationships=["meter", "controller"]
    )
    
    # Check access
    has_access = await reading_service.check_access(db, reading_id, current_user)
    if not has_access:
        raise ForbiddenException("Vous n'avez pas accès à cette lecture")
    
    # Add photos count
    reading_dict = reading.__dict__.copy()
    reading_dict['photos_count'] = len(reading.photo_urls or [])
    
    return reading


@router.get("/{reading_id}/photos")
async def get_reading_photos(
    reading_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Get all photo URLs for a reading.
    
    Returns:
    - List of photo URLs
    - Photo count
    - Pre-signed URLs for temporary access (if using private S3)
    """
    reading = await reading_service.get_or_404(db, reading_id)
    
    # Check access
    has_access = await reading_service.check_access(db, reading_id, current_user)
    if not has_access:
        raise ForbiddenException("Vous n'avez pas accès à cette lecture")
    
    return {
        "reading_id": reading_id,
        "photo_urls": reading.photo_urls or [],
        "photos_count": len(reading.photo_urls or []),
        "has_geolocation": reading.has_geolocation
    }


@router.put("/{reading_id}", response_model=ReadingRead)
async def update_reading(
    reading_id: UUID,
    reading_in: ReadingUpdate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Update a reading.
    
    **Restrictions**:
    - Controllers can only update their own readings
    - Controllers can only update within 24 hours of creation
    - Admins can update any reading at any time
    - If updating photos, minimum 2 photos still required
    """
    reading = await reading_service.update(db, reading_id, reading_in, current_user)
    
    reading_dict = reading.__dict__.copy()
    reading_dict['photos_count'] = len(reading.photo_urls or [])
    
    return reading


@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reading(
    reading_id: UUID,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Delete a reading.
    
    **Admin only**
    
    **Warning**: This will also delete all associated photos from S3.
    """
    await reading_service.delete(db, reading_id, current_user)
    return None


@router.get("/meter/{meter_id}/latest", response_model=ReadingRead)
async def get_latest_reading(
    meter_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Get the latest reading for a meter."""
    
    # Check meter access
    has_access = await meter_service.check_city_access(db, meter_id, current_user)
    if not has_access:
        raise ForbiddenException("Vous n'avez pas accès à ce compteur")
    
    result = await db.execute(
        select(Reading)
        .where(Reading.meter_id == meter_id)
        .order_by(desc(Reading.reading_date))
        .limit(1)
    )
    reading = result.scalar_one_or_none()
    
    if not reading:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Aucune lecture trouvée pour le compteur {meter_id}")
    
    reading_dict = reading.__dict__.copy()
    reading_dict['photos_count'] = len(reading.photo_urls or [])
    
    return reading


@router.get("/stats/overview", response_model=ReadingStats)
async def get_readings_stats(
    db: DatabaseSession,
    current_user: CurrentUser,
    meter_id: Optional[UUID] = Query(None, description="Filter by meter ID"),
    city_id: Optional[UUID] = Query(None, description="Filter by city ID"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)")
):
    """
    Get reading statistics.
    
    Returns:
    - Total number of readings
    - Average reading value
    - Min/Max reading values
    - Last reading date
    - Total number of photos
    """
    # Non-admin users can only see their city's stats
    if not current_user.is_admin():
        if city_id and city_id != current_user.city_id:
            raise ForbiddenException("Vous ne pouvez voir que les stats de votre ville")
        city_id = current_user.city_id
    
    return await reading_service.get_statistics(
        db,
        meter_id=meter_id,
        city_id=city_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/controller/my-readings", response_model=PageResponse[ReadingReadWithMeter])
async def get_my_readings(
    db: DatabaseSession,
    current_user: CurrentUser,
    pagination: Pagination,
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)")
):
    """
    Get readings created by the current user.
    
    Useful for controllers to view their own work history.
    Includes photo count for each reading.
    """
    result = await reading_service.get_by_controller(
        db,
        current_user.id,
        pagination,
        start_date,
        end_date
    )
    
    # Add photos count to each item
    for item in result.items:
        item.photos_count = len(item.photo_urls or [])
    
    return result


@router.post("/{reading_id}/add-photos", response_model=ReadingRead)
async def add_photos_to_reading(
    reading_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
    photos: List[UploadFile] = File(..., description="Additional photos to add")
):
    """
    Add additional photos to an existing reading.
    
    **Restrictions**:
    - Can only add photos within 24 hours of creation (for non-admins)
    - Maximum 10 total photos per reading
    - Only the creator or admin can add photos
    """
    reading = await reading_service.get_or_404(db, reading_id)
    
    # Check permission
    if not current_user.is_admin() and reading.controller_id != current_user.id:
        raise ForbiddenException("Vous ne pouvez modifier que vos propres lectures")
    
    # Check time restriction for non-admins
    if not current_user.is_admin():
        from datetime import timedelta
        time_diff = datetime.utcnow() - reading.created_at.replace(tzinfo=None)
        if time_diff > timedelta(hours=24):
            raise ForbiddenException(
                "Vous ne pouvez ajouter des photos que dans les 24 heures suivant la création"
            )
    
    # Check total photos limit
    current_photos = reading.photo_urls or []
    if len(current_photos) + len(photos) > 10:
        raise BadRequestException(
            f"Maximum 10 photos par lecture. "
            f"Actuellement: {len(current_photos)}, tentative d'ajout: {len(photos)}"
        )
    
    # Upload new photos
    new_photo_urls = await upload_service.upload_multiple_files(
        photos,
        folder=f"{settings.S3_FOLDER_READINGS}/{reading.meter_id}"
    )
    
    # Update reading with new photos
    reading.photo_urls = current_photos + new_photo_urls
    await db.commit()
    await db.refresh(reading)
    
    reading_dict = reading.__dict__.copy()
    reading_dict['photos_count'] = len(reading.photo_urls)
    
    return reading