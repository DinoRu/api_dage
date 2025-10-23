"""City schemas."""

from __future__ import annotations

from uuid import UUID
from typing import Optional

from pydantic import Field, field_validator

from app.schema.base import BaseSchema, TimestampSchema



class CityBase(BaseSchema):
    """Base city schema with common fields."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nom de la ville",
        examples=["Paris", "Lyon", "Marseille"]
    )


class CityCreate(CityBase):
    """Schema for creating a city."""
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and capitalize city name."""
        if not v or not v.strip():
            raise ValueError("Le nom de la ville ne peut pas être vide")
        return v.strip().title()


class CityUpdate(BaseSchema):
    """Schema for updating a city."""
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Nom de la ville"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and capitalize city name."""
        if v is not None:
            if not v.strip():
                raise ValueError("Le nom de la ville ne peut pas être vide")
            return v.strip().title()
        return v


class CityRead(CityBase, TimestampSchema):
    """Schema for reading a city."""
    
    pass


class CityReadWithStats(CityRead):
    """Schema for reading a city with statistics."""
    
    meters_count: int = Field(default=0, description="Nombre de compteurs")
    controllers_count: int = Field(default=0, description="Nombre de contrôleurs")


class CityReadWithRelations(CityRead):
    """Schema for reading a city with relations."""
    
    meters: list["MeterRead"] = Field(default_factory=list)
    controllers: list["UserReadSimple"] = Field(default_factory=list)
    

from app.schema.meter import MeterRead
from app.schema.user import UserReadSimple