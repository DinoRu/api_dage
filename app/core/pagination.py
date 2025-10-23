"""Pagination utilities."""

from typing import Generic, TypeVar, Sequence
from math import ceil

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Items per page"
    )
    
    @property
    def skip(self) -> int:
        """Calculate skip value."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit value."""
        return self.page_size


class PageResponse(BaseModel, Generic[T]):
    """Paginated response."""
    
    items: Sequence[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Has next page")
    has_previous: bool = Field(description="Has previous page")
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    @classmethod
    def create(
        cls,
        items: Sequence[T],
        total: int,
        params: PaginationParams
    ) -> "PageResponse[T]":
        """Create paginated response."""
        total_pages = ceil(total / params.page_size) if total > 0 else 0
        
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1
        )