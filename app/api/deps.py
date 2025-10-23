"""FastAPI dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginationParams
from app.core.security import (
    get_current_active_user,
    get_current_admin_user,
    get_current_supervisor_or_admin
)
from app.db.session import get_db
from app.models.user import User

# Database
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]

# Authentication
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]
SupervisorOrAdmin = Annotated[User, Depends(get_current_supervisor_or_admin)]

# Pagination
PaginationDep = Annotated[PaginationParams, Depends()]


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page")
) -> PaginationParams:
    """Get pagination parameters."""
    return PaginationParams(page=page, page_size=page_size)


Pagination = Annotated[PaginationParams, Depends(get_pagination_params)]