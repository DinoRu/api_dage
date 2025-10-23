"""City endpoints."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import DatabaseSession, AdminUser, SupervisorOrAdmin, Pagination
from app.core.pagination import PageResponse
from app.schema.city import (
    CityCreate,
    CityUpdate,
    CityRead,
    CityReadWithStats,
    CityReadWithRelations
)
from app.services.city import city_service

router = APIRouter(prefix="/cities", tags=["Cities"])


@router.get("", response_model=PageResponse[CityRead])
async def list_cities(
    db: DatabaseSession,
    pagination: Pagination,
    search: str = Query(None, description="Search by city name")
):
    """
    List all cities with pagination.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 1000)
    - **search**: Optional search query for city name
    """
    if search:
        return await city_service.search(db, search, pagination)
    
    return await city_service.get_multi(db, pagination, order_by="name")


@router.post("", response_model=CityRead, status_code=status.HTTP_201_CREATED)
async def create_city(
    city_in: CityCreate,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Create a new city.
    
    **Admin only**
    
    - **name**: Unique city name (1-255 characters)
    """
    return await city_service.create(db, city_in)


@router.get("/{city_id}", response_model=CityRead)
async def get_city(
    city_id: UUID,
    db: DatabaseSession
):
    """Get a city by ID."""
    return await city_service.get_or_404(db, city_id)


@router.get("/{city_id}/stats", response_model=CityReadWithStats)
async def get_city_stats(
    city_id: UUID,
    db: DatabaseSession
):
    """
    Get city with statistics.
    
    Includes:
    - Number of meters
    - Number of controllers
    """
    return await city_service.get_with_stats(db, city_id)


@router.get("/{city_id}/details", response_model=CityReadWithRelations)
async def get_city_details(
    city_id: UUID,
    db: DatabaseSession,
    current_user: SupervisorOrAdmin
):
    """
    Get city with all related data.
    
    **Supervisor or Admin only**
    
    Includes:
    - All meters in the city
    - All controllers assigned to the city
    """
    return await city_service.get_with_relations(db, city_id)


@router.put("/{city_id}", response_model=CityRead)
async def update_city(
    city_id: UUID,
    city_in: CityUpdate,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Update a city.
    
    **Admin only**
    """
    return await city_service.update(db, city_id, city_in)


@router.delete("/{city_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_city(
    city_id: UUID,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Delete a city.
    
    **Admin only**
    
    Warning: This will cascade delete all meters and readings in the city.
    """
    await city_service.delete(db, city_id)
    return None