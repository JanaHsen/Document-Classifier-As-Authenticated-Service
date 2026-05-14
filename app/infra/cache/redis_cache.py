# Owner: HADI
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from app.core.config import settings


async def init_cache(app: FastAPI) -> None:
    """Initialize fastapi-cache2 with Redis backend. Call on app startup."""
    redis = aioredis.from_url(settings.REDIS_URL)
    FastAPICache.init(RedisBackend(redis), prefix="docclass")


async def close_cache() -> None:
    """Close the Redis connection on app shutdown."""
    await FastAPICache.get_backend().get_client().aclose()
