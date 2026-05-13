# MOCK: Tarek's cache service
#
# REPLACE WITH when merging:
#   from app.services.cache_service import invalidate_batch
#
# What the real implementation must do:
#   invalidate_batch(batch_id) -> None:
#       invalidates the Redis cache keys for:
#           GET /batches
#           GET /batches/{batch_id}
#           GET /predictions/recent
#       per CONTRACTS.md cache invalidation rules


def invalidate_batch(batch_id: int) -> None:
    # Mock: no-op — cache does not exist locally
    # Real implementation calls fastapi-cache2 to delete affected keys
    print(f"[mock_cache_service] cache invalidation skipped (mock) for batch_id={batch_id}")
