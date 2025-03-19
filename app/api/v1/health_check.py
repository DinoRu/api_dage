from fastapi import APIRouter, status, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

health_router = APIRouter()

@health_router.get("/healthcheck", status_code=status.HTTP_200_OK)
async def healthcheck(session: AsyncSession = Depends(get_db)):
    """
        Health check endpoint.
        - Verifies database connectivity.
        - Provides applications health status
    :return:
    """
    try:
        # Test database connectivity
        result = await session.execute(text("SELECT 1"))
        result.fetchone()
        return {"status": "Healthy", "dependencies": {"database": "Healthy"}}
    except Exception as e:
        return {"status": "Degrade", "dependencies": {"database": "Unhealthy" + str(e)}}


