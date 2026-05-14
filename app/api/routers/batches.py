"""
Batch routes.

Two endpoints from Card 5:
  GET /batches       — list all batches
  GET /batches/{bid} — get one batch by id

Both are readable by all three roles (admin, reviewer, auditor) per
the seeded Casbin policy (batches:read). Caching is configured at
the service layer (per the architectural rule), so neither handler
manages cache directly.

Thin router pattern:
  - Validate input (FastAPI on the path parameter).
  - Run the auth chain (declared in the route's dependencies=[]).
  - Call ONE service method and return its result.
  - No DB access, no cache logic, no audit log writes.

Why dependencies=[...] and not a User parameter:
  When the handler does NOT need the user object (it's not
  filtering by user, not personalizing the response), declaring
  require_permission in dependencies=[] keeps the function
  signature clean. The dependency still runs and can still raise
  401/403 — the only difference is that the User isn't passed in.
"""


from fastapi import APIRouter, Depends

from app.api.deps.permissions import require_permission
from app.api.schemas.batch import BatchRead
from app.services.batch_service import BatchService, get_batch_service


router = APIRouter()


@router.get(
    "",
    response_model=list[BatchRead],
    summary="List batches (all three roles)",
    dependencies=[Depends(require_permission("batches", "read"))],
)
async def list_batches(
    batch_service: BatchService = Depends(get_batch_service),
):
    """
    GET /batches — return all batches.

    Auth chain (resolved before this body runs):
      1. current_active_user (chained from require_permission) —
         401 if JWT is missing, malformed, or expired.
      2. require_permission("batches", "read") — 403 if the caller's
         role lacks batches:read.

    The seeded policy table grants batches:read to all three roles,
    so any authenticated active user reaches the body.

    The service returns objects shaped like BatchRead;
    response_model=list[BatchRead] serializes the list element by
    element through the schema, excluding any extra fields and
    enforcing types.
    """
    return await batch_service.list_batches()


@router.get(
    "/{bid}",
    response_model=BatchRead,
    summary="Get one batch by id (all three roles)",
    dependencies=[Depends(require_permission("batches", "read"))],
)
async def get_batch(
    bid: int,
    batch_service: BatchService = Depends(get_batch_service),
):
    """
    GET /batches/{bid} — return one batch by id.

    Same auth chain as list_batches. The service raises 404 if no
    batch with this id exists; FastAPI propagates the HTTPException
    so the client sees the right status and message.
    """
    return await batch_service.get_batch(bid)
