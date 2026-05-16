# MOCK: Tarek's cache service
#
# NOTE: when swapping to real services, do NOT replace this with a direct CacheService call.
# Cache invalidation is handled automatically inside PredictionService.create():
#   await self.cache_service.invalidate_predictions_recent()
#   await self.cache_service.invalidate_batch_detail(batch_id)
#
# The correct swap is to remove Step 6 in inference_worker.py entirely once Step 5
# is wired to the real PredictionService.create().


def invalidate_batch(batch_id: int) -> None:
    # Mock: no-op — cache does not exist locally
    # Real implementation calls fastapi-cache2 to delete affected keys
    print(f"[mock_cache_service] cache invalidation skipped (mock) for batch_id={batch_id}")
