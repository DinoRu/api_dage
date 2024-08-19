from fastapi import APIRouter
from fastapi.responses import JSONResponse

health_router = APIRouter()


@health_router.get("/health")
async def health_check():
    return JSONResponse(content={'status': 'ok'}, status_code=200)
