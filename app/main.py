"""
FastAPI app entry point.

`uvicorn app.main:app` boots from here. The app:
  - Mounts 5 routers (auth, users, batches, predictions, audit-log)
  - Verifies on startup that the Casbin policy table is seeded
    (Card 3's "API refuses to boot if policy table empty")
  - Initializes Redis-backed cache via fastapi-cache2
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.middleware.request_id import add_request_id_middleware
from app.api.routers.audit import router as audit_router
from app.api.routers.auth import router as auth_router
from app.api.routers.batches import router as batches_router
from app.api.routers.predictions import router as predictions_router
from app.api.routers.users import router as users_router
from app.auth.casbin import assert_policies_seeded
from app.infra.cache.redis_cache import close_cache, init_cache


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

# CORS for the bundled web client. Auth is Bearer-token based (no
# cookies), so a wildcard origin with credentials disabled is safe
# and keeps local testing friction-free (Swagger, file://, a
# separate static host all work).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers. URL prefixes live here, not in the router
# files, so the entire URL surface is visible in one place. Tags
# group endpoints in the auto-generated /docs page.
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(batches_router, prefix="/batches", tags=["batches"])
app.include_router(predictions_router, prefix="/predictions", tags=["predictions"])
app.include_router(audit_router, prefix="/audit-log", tags=["audit"])

# Bundled single-file web client. Served same-origin so the client
# calls the API with no CORS hop. Resolved relative to this file so
# it works regardless of the process working directory (Docker
# WORKDIR=/app vs. running from the repo root).
_WEB_INDEX = Path(__file__).parent / "web" / "index.html"


@app.get("/", include_in_schema=False)
async def web_client() -> FileResponse:
    """Serve the Document Classifier web client."""
    return FileResponse(_WEB_INDEX)
