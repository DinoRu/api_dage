from typing import List, Optional, Dict, Any

from app.models.meter import Meter as MeterModel
from app.schema.meter import Meter as MeterResponse, Meter


def meter_to_dict(meter) -> dict:
    return {
        "meter_id": str(meter.meter_id),
        "code": meter.code,
        "owner_name": meter.owner_name,
        "meter_number": meter.meter_number,
        "address": meter.address,
        "previous_reading": meter.previous_reading,
        "current_reading": meter.current_reading,
        "latitude": meter.latitude,
        "longitude": meter.longitude,
        "supervisor": meter.supervisor,
        "comment": meter.comment,
        "created_at": meter.created_at.isoformat(),
        "completion_date": meter.completion_date.isoformat() if meter.completion_date else None,
        "photo1_url": meter.photo1_url,
        "photo2_url": meter.photo2_url,
        "status": meter.status.value  # Assuming StatusState is used as a string
    }


def convert_meter_to_pydantic(meters: List[MeterModel]) -> List[dict]:
    return [meter_to_dict(meter) for meter in meters]


def create_response(
        status_code: int,
        data: List[dict],
        pagination: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if pagination is None:
        pagination = {
            'offset': 0,
            'limit': len(data),
            'total': len(data),
            'order': 'asc'
        }
    return {
        'status': status_code,
        'result': {
            'data': data,
            'pagination': pagination
        }

    }
