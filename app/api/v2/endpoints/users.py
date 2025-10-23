"""User endpoints."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import (
    DatabaseSession,
    CurrentUser,
    AdminUser,
    Pagination
)
from app.core.exceptions import ForbiddenException
from app.core.pagination import PageResponse
from app.models.user import UserRole
from app.schema.user import (
    UserCreate,
    UserUpdate,
    UserRead,
    UserReadWithCity,
    UserReadWithStats
)
from app.services.user_v2 import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PageResponse[UserRead])
async def list_users(
    db: DatabaseSession,
    current_user: AdminUser,
    pagination: Pagination,
    role: UserRole = Query(None, description="Filter by role"),
    city_id: UUID = Query(None, description="Filter by city"),
    is_active: bool = Query(None, description="Filter by active status")
):
    """
    List all users with pagination and filters.
    
    **Admin only**
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 1000)
    - **role**: Optional role filter
    - **city_id**: Optional city filter
    - **is_active**: Optional active status filter
    """
    filters = {}
    if role:
        filters["role"] = role.value
    if city_id:
        filters["city_id"] = city_id
    if is_active is not None:
        filters["is_active"] = is_active
    
    return await user_service.get_multi(db, pagination, filters, order_by="username")


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Create a new user.
    
    **Admin only**
    
    - **username**: Unique username (3-255 characters, alphanumeric, _ and -)
    - **password**: Strong password (min 8 chars, 1 uppercase, 1 lowercase, 1 digit)
    - **full_name**: User's full name
    - **role**: User role (admin, controller, supervisor)
    - **city_id**: Optional city assignment
    - **is_active**: User status (default: true)
    """
    from app.services.auth import auth_service
    return await auth_service.register(db, user_in)


@router.get("/me", response_model=UserReadWithCity)
async def get_current_user_profile(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    Get current user's profile with city information.
    """
    return await user_service.get_or_404(db, current_user.id, relationships=["city"])


@router.get("/{user_id}", response_model=UserReadWithCity)
async def get_user(
    user_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Get a user by ID with city information.
    
    **Note**: Non-admin users can only view their own profile.
    """
    # Non-admin can only view themselves
    if not current_user.is_admin() and user_id != current_user.id:
        raise ForbiddenException("You can only view your own profile")
    
    return await user_service.get_or_404(db, user_id, relationships=["city"])


@router.get("/{user_id}/stats", response_model=UserReadWithStats)
async def get_user_stats(
    user_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Get user with statistics.
    
    Includes:
    - Number of readings created
    - Date of last reading
    
    **Note**: Non-admin users can only view their own stats.
    """
    # Non-admin can only view themselves
    if not current_user.is_admin() and user_id != current_user.id:
        raise ForbiddenException("You can only view your own stats")
    
    return await user_service.get_with_stats(db, user_id)


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Update a user.
    
    **Restrictions**:
    - Users can update their own full_name
    - Only admins can update role, city_id, and is_active
    - Password changes should use the /auth/change-password endpoint
    """
    # Non-admin can only update themselves (limited fields)
    if not current_user.is_admin():
        if user_id != current_user.id:
            raise ForbiddenException("You can only update your own profile")
        
        # Non-admins can't change role, city, or status
        if user_in.role or user_in.city_id or user_in.is_active is not None:
            raise ForbiddenException("You don't have permission to update these fields")
    
    return await user_service.update(db, user_id, user_in)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Delete a user.
    
    **Admin only**
    
    Note: This sets readings' controller_id to NULL instead of deleting them.
    """
    # Prevent self-deletion
    if user_id == current_user.id:
        from app.core.exceptions import BadRequestException
        raise BadRequestException("You cannot delete your own account")
    
    await user_service.delete(db, user_id)
    return None


@router.patch("/{user_id}/activate", response_model=UserRead)
async def activate_user(
    user_id: UUID,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Activate a user.
    
    **Admin only**
    """
    return await user_service.set_active_status(db, user_id, True)


@router.patch("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: UUID,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Deactivate a user.
    
    **Admin only**
    
    Deactivated users cannot log in.
    """
    # Prevent self-deactivation
    if user_id == current_user.id:
        from app.core.exceptions import BadRequestException
        raise BadRequestException("You cannot deactivate your own account")
    
    return await user_service.set_active_status(db, user_id, False)