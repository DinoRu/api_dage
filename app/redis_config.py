from typing import Optional
from redis import Redis


REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379

redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(f'redis://{REDIS_HOST}:{REDIS_PORT}', decode_responses=True)
    return redis_client
