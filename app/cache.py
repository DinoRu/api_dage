from typing import Any

from app.redis_config import get_redis_client


async def set_cache(key: str, value: Any, expire_seconds: int = 60):
    redis_client = await get_redis_client()
    redis_client.setex(key, expire_seconds, value)


async def get_cache(key: str) -> Any:
    redis_client = await get_redis_client()
    value = redis_client.get(key)
    if value:
        return value
    return None

