"""Base service with common CRUD operations."""

from typing import Generic, TypeVar, Type, Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, PageResponse
from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service with CRUD operations."""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get(
        self,
        db: AsyncSession,
        id: UUID,
        relationships: Optional[list[str]] = None
    ) -> Optional[ModelType]:
        """Get a single record by ID."""
        query = select(self.model).where(self.model.id == id)
        
        # Load relationships if specified
        if relationships:
            for rel in relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_or_404(
        self,
        db: AsyncSession,
        id: UUID,
        relationships: Optional[list[str]] = None
    ) -> ModelType:
        """Get a record by ID or raise 404."""
        obj = await self.get(db, id, relationships)
        if not obj:
            raise NotFoundException(
                f"{self.model.__name__} with id {id} not found"
            )
        return obj
    
    async def get_multi(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        filters: Optional[dict] = None,
        order_by: Optional[str] = None
    ) -> PageResponse[ModelType]:
        """Get multiple records with pagination."""
        # Base query
        query = select(self.model)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if value is not None:
                    query = query.where(getattr(self.model, key) == value)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Apply ordering
        if order_by:
            if order_by.startswith("-"):
                query = query.order_by(
                    getattr(self.model, order_by[1:]).desc()
                )
            else:
                query = query.order_by(getattr(self.model, order_by))
        
        # Apply pagination
        query = query.offset(pagination.skip).limit(pagination.limit)
        
        # Execute
        result = await db.execute(query)
        items = result.scalars().all()
        
        return PageResponse.create(items, total or 0, pagination)
    
    async def create(
        self,
        db: AsyncSession,
        obj_in: CreateSchemaType,
        **kwargs
    ) -> ModelType:
        """Create a new record."""
        obj_data = obj_in.model_dump()
        obj_data.update(kwargs)
        
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj
    
    async def update(
        self,
        db: AsyncSession,
        id: UUID,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update a record."""
        db_obj = await self.get_or_404(db, id)
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj
    
    async def delete(
        self,
        db: AsyncSession,
        id: UUID
    ) -> bool:
        """Delete a record."""
        db_obj = await self.get_or_404(db, id)
        await db.delete(db_obj)
        await db.commit()
        return True
    
    async def exists(
        self,
        db: AsyncSession,
        filters: dict
    ) -> bool:
        """Check if a record exists."""
        query = select(self.model)
        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None