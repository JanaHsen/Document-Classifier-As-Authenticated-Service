"""Cache Service.

Handles cache invalidation for cached endpoints using fastapi-cache2.
All cached endpoints are invalidated via FastAPICache.clear() to guarantee
fresh data after writes.
"""

from fastapi_cache import FastAPICache


class CacheService:
    """Service for managing application cache invalidation."""

    async def invalidate_batches_list(self) -> None:
        """Invalidate the GET /batches list cache."""
        await FastAPICache.clear()

    async def invalidate_batch_detail(self, batch_id: int) -> None:
        """Invalidate the GET /batches/{batch_id} detail cache."""
        await FastAPICache.clear()

    async def invalidate_predictions_recent(self) -> None:
        """Invalidate the GET /predictions/recent cache."""
        await FastAPICache.clear()

    async def invalidate_user_me(self) -> None:
        """Invalidate the GET /me cache."""
        await FastAPICache.clear()

    async def clear_all(self) -> None:
        """Clear entire cache (emergency use)."""
        await FastAPICache.clear()


# Dependency provider
from fastapi import Depends

def get_cache_service() -> CacheService:
    """FastAPI dependency for CacheService."""
    return CacheService()
