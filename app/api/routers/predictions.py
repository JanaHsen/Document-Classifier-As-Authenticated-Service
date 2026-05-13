"""
Prediction routes.

Two endpoints from Card 6:
  GET   /predictions/recent      — list recent predictions (all 3 roles)
  PATCH /predictions/{pid}/label — relabel a prediction  (reviewer only)

The relabel endpoint has two stacked gates:
  1. ROLE gate (Casbin) — require_permission("predictions", "relabel").
     Only the reviewer role has that policy in the seeded table;
     admin and auditor receive 403.
  2. CONFIDENCE gate (service-layer) — confidence < 0.7. Enforced
     inside PredictionService.relabel, not here. Per Card 6,
     business rules like the threshold check live in the service.

Cache invalidation and the audit log entry on relabel also live
inside PredictionService.relabel, not in this router. The router
only validates input, runs the auth chain, and calls the service.

GET uses dependencies=[...] because the handler doesn't need the
user object. PATCH puts the user in the parameter list because the
service needs it to record the actor in the audit log.
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps.permissions import require_permission
from app.api.schemas.prediction import PredictionRead, RelabelRequest
from app.db.models import User
from app.services.prediction_service import (
    PredictionService,
    get_prediction_service,
)


router = APIRouter()


@router.get(
    "/recent",
    response_model=list[PredictionRead],
    summary="List recent predictions (all three roles)",
    dependencies=[Depends(require_permission("predictions", "read"))],
)
async def get_recent_predictions(
    prediction_service: PredictionService = Depends(get_prediction_service),
):
    """
    GET /predictions/recent — return recent predictions.

    Auth chain (resolved before this body runs):
      1. current_active_user — 401 if no/invalid JWT.
      2. require_permission("predictions", "read") — 403 if the
         caller's role lacks the policy. The seeded policy table
         grants predictions:read to all three roles, so any
         authenticated active user reaches the body.

    The service may add caching later; this router does not
    configure it (cache control is the service layer's job).
    """
    return await prediction_service.get_recent()


@router.patch(
    "/{pid}/label",
    response_model=PredictionRead,
    summary="Relabel a low-confidence prediction (reviewer only)",
)
async def relabel_prediction(
    pid: UUID,
    body: RelabelRequest,
    reviewer: User = Depends(require_permission("predictions", "relabel")),
    prediction_service: PredictionService = Depends(get_prediction_service),
):
    """
    PATCH /predictions/{pid}/label — change a prediction's label.

    Auth chain (resolved before this body runs):
      1. current_active_user — 401 if no/invalid JWT.
      2. require_permission("predictions", "relabel") — 403 if the
         caller's role lacks the policy. The seeded policy table
         grants predictions:relabel to ONLY the reviewer role;
         admin and auditor get 403 here.

    The reviewer is passed through to the service so it can record
    the actor in the audit log entry.

    The service additionally enforces the confidence < 0.7 gate
    (Card 6) — returns 400 if the prediction is too confident to
    be relabeled. The service also handles cache invalidation and
    the audit log write per the architectural rule that those
    side effects live in the service layer, not the router.
    """
    return await prediction_service.relabel(
        reviewer=reviewer,
        pid=pid,
        new_label=body.label,
    )
