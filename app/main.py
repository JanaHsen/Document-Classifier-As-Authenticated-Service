"""
FastAPI app entry point.

`uvicorn app.main:app` boots from here. The app:
  - Mounts 5 routers (auth, users, batches, predictions, audit-log)
  - Verifies on startup that the Casbin policy table is seeded
    (Card 3's "API refuses to boot if policy table empty")

When Hadi's Settings module lands, swap the hardcoded title and
description below for values from Settings. When Tarek's real
services adopt @cache decorators, initialize fastapi-cache2 inside
the lifespan (see TODO).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware.request_id import add_request_id_middleware
from app.infra.cache.redis_cache import close_cache, init_cache
from app.api.routers.audit import router as audit_router
from app.api.routers.auth import router as auth_router
from app.api.routers.batches import router as batches_router
from app.api.routers.predictions import router as predictions_router
from app.api.routers.users import router as users_router
from app.auth.casbin import assert_policies_seeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown hooks for the app.

    On startup:
      - assert_policies_seeded() raises RuntimeError if the Casbin
        policy table is empty. The exception propagates and the
        app fails to start. This is the brief's "refuse to boot"
        enforcement for the policy table.

    On shutdown:
      - nothing for now.

    TODO Hadi / Tarek: when fastapi-cache2 is needed (i.e., when
    real services start applying @cache decorators), initialize it
    here. Sketch:

        from fastapi_cache import FastAPICache
        from fastapi_cache.backends.redis import RedisBackend
        from redis import asyncio as aioredis

        redis = aioredis.from_url(REDIS_URL)
        FastAPICache.init(RedisBackend(redis), prefix="docclass")
        yield
        await redis.close()

    Until then, the mock services don't cache and the app boots
    without a Redis dependency.
    """
    assert_policies_seeded()
    await init_cache(app)
    yield
    await close_cache()


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
