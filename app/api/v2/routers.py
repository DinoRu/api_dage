"""API v2 router."""

from fastapi import APIRouter

from app.api.v2.endpoints import (
    auth,
    users,
    cities,
    meters,
    meter_import,
    readings,
    # upload
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(cities.router)
api_router.include_router(meters.router)
api_router.include_router(meter_import.router) 
api_router.include_router(readings.router)