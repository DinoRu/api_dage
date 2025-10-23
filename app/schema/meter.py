"""Meter schemas."""

from __future__ import annotations

from uuid import UUID
from typing import Optional

from pydantic import Field, field_validator, model_validator

from app.models.meter import MeterStatus
from app.schema.base import BaseSchema, TimestampSchema



class MeterBase(BaseSchema):
    """Base meter schema with common fields."""
    
    code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Code unique du compteur",
        examples=["MTR-001", "WTR-2024-001"]
    )
    owner_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nom du propriétaire",
        examples=["Jean Dupont", "Marie Martin"]
    )
    address: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Adresse du compteur",
        examples=["123 Rue de la République, 75001 Paris"]
    )
    
    meter_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type de compteur")
    
    meter_number: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Numéro de série du compteur",
        examples=["SN-123456789"]
    )
    status: MeterStatus = Field(
        default=MeterStatus.ACTIVE,
        description="Statut du compteur"
    )
    previous_reading: Optional[float] = Field(
        None,
        ge=0,
        description="Dernière lecture enregistrée"
    )
    city_id: UUID = Field(
        ...,
        description="Identifiant de la ville"
    )


class MeterCreate(MeterBase):
    """Schema for creating a meter."""
    
    @field_validator('code', 'meter_number', 'meter_type')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate and uppercase codes."""
        if not v or not v.strip():
            raise ValueError(f"Le {v} ne peut pas être vide")
        return v.strip().upper()
    
    @field_validator('owner_name')
    @classmethod
    def validate_owner_name(cls, v: str) -> str:
        """Validate owner name."""
        if not v or not v.strip():
            raise ValueError("Le nom du propriétaire ne peut pas être vide")
        return v.strip().title()


class MeterUpdate(BaseSchema):
    """Schema for updating a meter."""
    
    code: Optional[str] = Field(None, min_length=1, max_length=100)
    owner_name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    meter_number: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[MeterStatus] = None
    previous_reading: Optional[float] = Field(None, ge=0)
    city_id: Optional[UUID] = None
    
    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        """Ensure at least one field is provided."""
        if not any([
            self.code, self.owner_name, self.address, 
            self.meter_number, self.status, self.previous_reading, self.city_id
        ]):
            raise ValueError("Au moins un champ doit être fourni pour la mise à jour")
        return self


class MeterRead(MeterBase, TimestampSchema):
    """Schema for reading a meter."""
    
    pass


class MeterReadSimple(BaseSchema):
    """Simplified meter schema for nested relations."""
    
    id: UUID
    code: str
    owner_name: str
    meter_number: str
    status: MeterStatus


class MeterReadWithCity(MeterRead):
    """Schema for reading a meter with city."""
    
    city: "CityRead"


class MeterReadWithRelations(MeterRead):
    """Schema for reading a meter with all relations."""
    
    city: "CityRead"
    readings: list[ReadingRead] = Field(default_factory=list)
    readings_count: int = Field(default=0, description="Nombre de lectures")


class MeterReadWithStats(MeterRead):
    """Schema for reading a meter with statistics."""
    
    readings_count: int = Field(default=0)
    last_reading_value: Optional[float] = None
    last_reading_date: Optional[str] = None
    average_consumption: Optional[float] = None
    

class MeterImportRow(BaseSchema):
    """Schema for a single meter row from Excel."""
    
    code: str = Field(..., description="Unique meter code")
    owner_name: str = Field(..., description="Owner's name")
    address: str = Field(..., description="Meter address")
    meter_type: str = Field(..., description="Type of meter")
    meter_number: str = Field(..., description="Serial number")
    previous_reading: Optional[float] = Field(None, ge=0, description="Previous reading value")
    status: str = Field(default="active", description="Meter status")
    
    @field_validator('code', 'meter_number')
    @classmethod
    def validate_codes(cls, v: str) -> str:
        """Validate and uppercase codes."""
        if not v or not v.strip():
            raise ValueError("Code cannot be empty")
        return v.strip().upper()
    
    @field_validator('owner_name', 'address')
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        """Validate text fields."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    # @field_validator('status')
    # @classmethod
    # def validate_status(cls, v: str) -> str:
    #     """Validate status."""
    #     valid_statuses = ['active', 'inactive', 'maintenance', 'decommissioned']
    #     v_lower = v.lower().strip()
    #     if v_lower not in valid_statuses:
    #         raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
    #     return v_lower


class MeterImportResult(BaseSchema):
    """Result of meter import operation."""
    
    success: bool = Field(..., description="Overall success status")
    total_rows: int = Field(..., description="Total rows processed")
    success_count: int = Field(..., description="Number of successful imports")
    error_count: int = Field(..., description="Number of failed imports")
    skipped_count: int = Field(default=0, description="Number of skipped rows")
    errors: list[dict] = Field(default_factory=list, description="List of errors")
    created_meters: list[UUID] = Field(default_factory=list, description="IDs of created meters")
    message: str = Field(..., description="Summary message")


class MeterImportError(BaseSchema):
    """Error details for a failed import row."""
    
    row_number: int = Field(..., description="Excel row number")
    code: Optional[str] = Field(None, description="Meter code if available")
    meter_number: Optional[str] = Field(None, description="Meter number if available")
    error: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")

    
from app.schema.city import CityRead
from app.schema.reading import ReadingRead