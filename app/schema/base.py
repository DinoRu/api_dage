"""Base schemas with common fields."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        arbitrary_types_allowed=True
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    skip: int = 0
    limit: int = 1000
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skip": 0,
                "limit": 1000
            }
        }
    )


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""
    
    total: int
    skip: int
    limit: int
    items: list