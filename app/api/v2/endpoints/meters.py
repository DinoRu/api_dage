"""Meter endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import (
    DatabaseSession,
    CurrentUser,
    AdminUser,
    SupervisorOrAdmin,
    Pagination
)
from app.core.exceptions import ForbiddenException
from app.core.pagination import PageResponse
from app.models.meter import MeterStatus
from app.schema.meter import (
    MeterCreate,
    MeterUpdate,
    MeterRead,
    MeterReadWithCity,
    MeterReadWithRelations,
    MeterReadWithStats
)
from app.services.meter_v2 import meter_service

router = APIRouter(prefix="/meters", tags=["Meters"])


@router.get("", response_model=PageResponse[MeterRead])
async def list_meters(
    db: DatabaseSession,
    current_user: CurrentUser,
    pagination: Pagination,
    city_id: Optional[UUID] = Query(None, description="Filter by city ID"),
    status: Optional[MeterStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by code, owner, address, or meter number")
):
    """
    List all meters with pagination and filters.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 1000)
    - **city_id**: Optional city filter
    - **status**: Optional status filter (active, inactive, maintenance, decommissioned)
    - **search**: Optional search query
    
    **Note**: Non-admin users can only see meters in their assigned city.
    """
    # Non-admin users can only see their city's meters
    if not current_user.is_admin():
        if city_id and city_id != current_user.city_id:
            raise ForbiddenException("You can only view meters in your assigned city")
        city_id = current_user.city_id
    
    if search:
        return await meter_service.search(db, search, city_id, pagination)
    
    if city_id:
        return await meter_service.get_by_city(db, city_id, pagination, status)
    
    filters = {}
    if status:
        filters["status"] = status.value
    
    return await meter_service.get_multi(db, pagination, filters, order_by="code")


@router.post("", response_model=MeterRead, status_code=status.HTTP_201_CREATED)
async def create_meter(
    meter_in: MeterCreate,
    db: DatabaseSession,
    current_user: SupervisorOrAdmin
):
    """
    Create a new meter.
    
    **Supervisor or Admin only**
    
    - **code**: Unique meter code
    - **owner_name**: Owner's name
    - **address**: Meter location address
    - **meter_number**: Unique serial number
    - **status**: Initial status (default: active)
    - **previous_reading**: Optional previous reading value
    - **city_id**: City where meter is located
    
    **Note**: Supervisors can only create meters in their assigned city.
    """
    # Supervisors can only create in their city
    if current_user.is_supervisor() and meter_in.city_id != current_user.city_id:
        raise ForbiddenException("You can only create meters in your assigned city")
    
    return await meter_service.create(db, meter_in)


@router.get("/{meter_id}", response_model=MeterReadWithCity)
async def get_meter(
    meter_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Get a meter by ID with city information.
    **Note**: Non-admin users can only view meters in their assigned city.
    """
    meter = await meter_service.get_or_404(db, meter_id, relationships=["city"])

    # Check access
    if not current_user.is_admin() and meter.city_id != current_user.city_id:
        raise ForbiddenException("You don't have access to this meter")

    return meter


@router.get("/{meter_id}/stats", response_model=MeterReadWithStats)
async def get_meter_stats(
    meter_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Get meter with statistics.
    
    Includes:
    - Number of readings
    - Last reading value and date
    - Average consumption
    
    **Note**: Non-admin users can only view meters in their assigned city.
    """
    # Check access first
    has_access = await meter_service.check_city_access(db, meter_id, current_user)
    if not has_access:
        raise ForbiddenException("You don't have access to this meter")
    
    return await meter_service.get_with_stats(db, meter_id)


@router.get("/{meter_id}/details", response_model=MeterReadWithRelations)
async def get_meter_details(
    meter_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Get meter with all related data.
    
    Includes:
    - City information
    - All readings (latest first)
    
    **Note**: Non-admin users can only view meters in their assigned city.
    """
    meter = await meter_service.get_or_404(
        db,
        meter_id,
        relationships=["city", "readings"]
    )
    
    # Check access
    if not current_user.is_admin() and meter.city_id != current_user.city_id:
        raise ForbiddenException("You don't have access to this meter")
    
    return meter


@router.put("/{meter_id}", response_model=MeterRead)
async def update_meter(
    meter_id: UUID,
    meter_in: MeterUpdate,
    db: DatabaseSession,
    current_user: SupervisorOrAdmin
):
    """
    Update a meter.
    
    **Supervisor or Admin only**
    
    **Note**: Supervisors can only update meters in their assigned city.
    """
    # Check access
    has_access = await meter_service.check_city_access(db, meter_id, current_user)
    if not has_access:
        raise ForbiddenException("You don't have access to this meter")
    
    return await meter_service.update(db, meter_id, meter_in)


@router.patch("/{meter_id}/status", response_model=MeterRead)
async def update_meter_status(
    meter_id: UUID,
    status: MeterStatus,
    db: DatabaseSession,
    current_user: SupervisorOrAdmin
):
    """
    Update meter status.
    
    **Supervisor or Admin only**
    
    Available statuses:
    - **active**: Meter is operational
    - **inactive**: Meter is not in use
    - **maintenance**: Meter is under maintenance
    - **decommissioned**: Meter is permanently retired
    """
    return await meter_service.update_status(db, meter_id, status, current_user)


@router.delete("/{meter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meter(
    meter_id: UUID,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Delete a meter.
    
    **Admin only**
    
    Warning: This will cascade delete all readings for this meter.
    """
    await meter_service.delete(db, meter_id)
    return None


@router.get("/city/{city_id}/count")
async def count_meters_by_city(
    city_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
    status: Optional[MeterStatus] = Query(None, description="Filter by status")
):
    """
    Count meters in a city.
    
    - **status**: Optional status filter
    
    **Note**: Non-admin users can only count meters in their assigned city.
    """
    # Check access
    if not current_user.is_admin() and city_id != current_user.city_id:
        raise ForbiddenException("You can only view data for your assigned city")
    
    from sqlalchemy import select, func
    from app.models.meter import Meter
    
    stmt = select(func.count()).where(Meter.city_id == city_id)
    
    if status:
        stmt = stmt.where(Meter.status == status.value)
    
    count = await db.scalar(stmt)
    
    return {"city_id": city_id, "count": count or 0, "status": status}