"""Tests for reading with photos."""

import pytest
from fastapi import UploadFile
from io import BytesIO

from app.schema.reading import ReadingCreate


@pytest.mark.asyncio
async def test_create_reading_minimum_photos():
    """Test that minimum 2 photos are required."""
    # Test with 0 photos
    with pytest.raises(ValueError, match="Au minimum 2 photos"):
        ReadingCreate(
            meter_id="uuid-here",
            reading_value=100.0,
            reading_date="2024-01-01T10:00:00",
            photo_urls=[]
        )
    
    # Test with 1 photo
    with pytest.raises(ValueError, match="Au minimum 2 photos"):
        ReadingCreate(
            meter_id="uuid-here",
            reading_value=100.0,
            reading_date="2024-01-01T10:00:00",
            photo_urls=["https://example.com/photo1.jpg"]
        )
    
    # Test with 2 photos (should pass)
    reading = ReadingCreate(
        meter_id="uuid-here",
        reading_value=100.0,
        reading_date="2024-01-01T10:00:00",
        photo_urls=[
            "https://example.com/photo1.jpg",
            "https://example.com/photo2.jpg"
        ]
    )
    assert len(reading.photo_urls) == 2