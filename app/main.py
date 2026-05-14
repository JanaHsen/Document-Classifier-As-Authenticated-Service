"""
FastAPI app entry point.

`uvicorn app.main:app` boots from here. The app:
  - Mounts 5 routers (auth, users, batches, predictions, audit-log)
  - Verifies on startup that the Casbin policy table is seeded
    (Card 3's "API refuses to boot if policy table empty")
  - Initializes Redis-backed cache via fastapi-cache2
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware.request_id import add_request_id_middleware
from app.api.routers.audit import router as audit_router
from app.api.routers.auth import router as auth_router
from app.api.routers.batches import router as batches_router
from app.api.routers.predictions import router as predictions_router
from app.api.routers.users import router as users_router
from app.auth.casbin import assert_policies_seeded
from app.core.config import settings

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis.asyncio as redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown hooks for the app.

    On startup:
      - assert_policies_seeded() raises RuntimeError if the Casbin
        policy table is empty. The exception propagates and the
        app fails to start.
      - Initialize Redis-backed cache (fastapi-cache2).

    On shutdown:
      - Close Redis connection.
    """
    assert_policies_seeded()

    # Initialize fastapi-cache2 with Redis backend
    redis_client = redis.from_url(settings.REDIS_URL)
    FastAPICache.init(RedisBackend(redis_client), prefix="docclass")

    yield

    await redis_client.close()


# App metadata. Hadi will refactor these into a Settings module
# (title, version, description from env or Vault). Hardcoded here
# for now so main.py is self-contained.
app = FastAPI(
    title="Document Classifier as Authenticated Service",
    description=(
        "Document classification API with JWT authentication, "
        "Casbin RBAC, audit logging, and batch/prediction "
        "review endpoints."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

add_request_id_middleware(app)

# Mount all routers. URL prefixes live here, not in the router
# files, so the entire URL surface is visible in one place. Tags
# group endpoints in the auto-generated /docs page.
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(batches_router, prefix="/batches", tags=["batches"])
app.include_router(predictions_router, prefix="/predictions", tags=["predictions"])
app.include_router(audit_router, prefix="/audit-log", tags=["audit"])
