"""Reading schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import Field, field_validator, model_validator

from app.schema.base import BaseSchema, TimestampSchema
from app.schema.meter import MeterReadSimple
from app.schema.user import UserReadSimple
 

class ReadingBase(BaseSchema):
    """Base reading schema with common fields."""
    
    meter_id: UUID = Field(..., description="Identifiant du compteur")
    reading_value: float = Field(
        ...,
        ge=0,
        description="Valeur de la lecture",
        examples=[123.45, 456.78]
    )
    reading_date: datetime = Field(
        ...,
        description="Date et heure de la lecture"
    )
    comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="Commentaire additionnel"
    )
    photo_urls: list[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="URLs des photos (minimum 2, maximum 5)",
        examples=[["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"]]
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Latitude GPS"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Longitude GPS"
    )


class ReadingCreate(ReadingBase):
    """Schema for creating a reading."""
    
    controller_id: Optional[UUID] = Field(
        None,
        description="Identifiant du contrôleur (auto-rempli si non fourni)"
    )
    
    @field_validator('reading_date')
    @classmethod
    def validate_reading_date(cls, v: datetime) -> datetime:
        """Validate that reading date is not in the future."""
        if v > datetime.now(v.tzinfo):
            raise ValueError("La date de lecture ne peut pas être dans le futur")
        return v
    
    @field_validator('photo_urls')
    @classmethod
    def validate_photos(cls, v: list[str]) -> list[str]:
        """Validate that at least 2 photos are provided."""
        if len(v) < 2:
            raise ValueError("Au minimum 2 photos sont requises pour chaque lecture")
        
        # Validate URLs
        for url in v:
            if not url or not url.strip():
                raise ValueError("Les URLs de photos ne peuvent pas être vides")
            if not url.startswith(('http://', 'https://')):
                raise ValueError("Les URLs de photos doivent commencer par http:// ou https://")
        
        return v
    
    @model_validator(mode='after')
    def validate_geolocation(self):
        """Validate that both lat and lon are provided together."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError(
                "La latitude et la longitude doivent être fournies ensemble"
            )
        return self
    

class ReadingCreateWithPhotos(BaseSchema):
    """Schema for creating a reading (without photo URLs - they will be uploaded)."""
    
    meter_id: UUID = Field(..., description="Identifiant du compteur")
    reading_value: float = Field(
        ...,
        ge=0,
        description="Valeur de la lecture"
    )
    reading_date: datetime = Field(
        ...,
        description="Date et heure de la lecture"
    )
    comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="Commentaire additionnel"
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Latitude GPS"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Longitude GPS"
    )
    
    @field_validator('reading_date')
    @classmethod
    def validate_reading_date(cls, v: datetime) -> datetime:
        """Validate that reading date is not in the future."""
        if v > datetime.now(v.tzinfo):
            raise ValueError("La date de lecture ne peut pas être dans le futur")
        return v
    
    @model_validator(mode='after')
    def validate_geolocation(self):
        """Validate that both lat and lon are provided together."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError(
                "La latitude et la longitude doivent être fournies ensemble"
            )
        return self


class ReadingUpdate(BaseSchema):
    """Schema for updating a reading."""
    
    reading_value: Optional[float] = Field(None, ge=0)
    reading_date: Optional[datetime] = None
    comment: Optional[str] = Field(None, max_length=1000)
    photo_urls: Optional[list[str]] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        """Ensure at least one field is provided."""
        if not any([
            self.reading_value is not None,
            self.reading_date,
            self.comment,
            self.photo_urls,
            self.latitude is not None,
            self.longitude is not None
        ]):
            raise ValueError("Au moins un champ doit être fourni pour la mise à jour")
        return self


class ReadingRead(ReadingBase, TimestampSchema):
    """Schema for reading a reading."""
    
    controller_id: Optional[UUID]
    has_geolocation: bool = Field(
        default=False,
        description="Indique si la lecture a des coordonnées GPS"
    )


class ReadingReadSimple(BaseSchema):
    """Simplified reading schema for nested relations."""
    
    id: UUID
    reading_value: float
    reading_date: datetime
    comment: Optional[str] = None


class ReadingReadWithMeter(ReadingRead):
    """Schema for reading a reading with meter."""
    
    meter: "MeterReadSimple"


class ReadingReadWithController(ReadingRead):
    """Schema for reading a reading with controller."""
    
    controller: Optional["UserReadSimple"] = None


class ReadingReadWithRelations(ReadingRead):
    """Schema for reading a reading with all relations."""
    
   
    
    meter: "MeterReadSimple"
    controller: Optional[UserReadSimple] = None


class ReadingStats(BaseSchema):
    """Schema for reading statistics."""
    
    total_readings: int
    average_value: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    last_reading_date: Optional[datetime]
    

from app.schema.meter import MeterReadSimple
from app.schema.user import UserReadSimple