# Owner: HADI
from fastapi import FastAPI
from fastapi_cache import FastAPICache
import redis.asyncio as aioredis

from app.core.config import settings


class _RedisBackend:
    """Redis backend for fastapi-cache2 using redis.asyncio (Python 3.12 compatible).

    Replaces fastapi_cache.backends.redis.RedisBackend which depends on
    aioredis — unmaintained and broken on Python 3.12 (duplicate base class).
    """

    def __init__(self, redis: aioredis.Redis) -> None:
        self.redis = redis

    async def get_with_ttl(self, key: str) -> tuple[int, str | None]:
        async with self.redis.pipeline(transaction=True) as pipe:
            return await (pipe.ttl(key).get(key).execute())

    async def get(self, key: str) -> str | None:
        return await self.redis.get(key)

    async def set(self, key: str, value: str, expire: int | None = None) -> None:
        await self.redis.set(key, value, ex=expire)

    async def clear(self, namespace: str | None = None, key: str | None = None) -> int:
        if namespace:
            lua = """
local keys = redis.call('keys', ARGV[1])
for i = 1, #keys, 5000 do
  redis.call('del', unpack(keys, i, math.min(i+4999, #keys)))
end
return 0
"""
            return await self.redis.eval(lua, 0, f"{namespace}:*")
        if key:
            return await self.redis.delete(key)
        return 0


async def init_cache(app: FastAPI) -> None:
    """Initialize fastapi-cache2 with Redis backend. Call on app startup."""
    redis = aioredis.from_url(settings.REDIS_URL)
    FastAPICache.init(_RedisBackend(redis), prefix="docclass")


async def close_cache() -> None:
    """Close the Redis connection on app shutdown."""
    backend = FastAPICache.get_backend()
    if hasattr(backend, "redis"):
        await backend.redis.aclose()
