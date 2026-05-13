"""
Pydantic API schemas for the Prediction resource.

Predictions are the output of the inference worker — one row per
classified document. The classifier produces (label, confidence)
for each TIFF processed. Reviewers can correct low-confidence
predictions via the relabel endpoint.

This is the API-boundary view. The internal domain model (Tarek's
app/domain/prediction.py) and the SQLAlchemy ORM model (Tarek's
app/db/models.py) may carry additional fields not exposed here.

TENTATIVE FIELDS — coordinate with Tarek and Hawraa.
  - Tarek owns the predictions-table column set.
  - Hawraa owns the inference output shape and the label space.
The fields below are what Card 6's endpoints need to render. If
Tarek's data model adds more (e.g., top_5 alternatives, raw
softmax scores, reviewer_id when relabeled, relabeled_at), they
can be added here without breaking the routers.

Label space: the 16 RVL-CDIP classes (Hawraa's classifier output).
Whether relabel must restrict to those 16 strings is a business
question. We model `label` as a free string here; the gate (if
any) lives in PredictionService.relabel using Hawraa's labels.json
as the source of truth.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PredictionRead(BaseModel):
    """
    Response shape for GET /predictions/recent and PATCH
    /predictions/{pid}/label.

    from_attributes=True so FastAPI can serialize from any object
    with the right attribute names — SQLAlchemy ORM instance,
    Pydantic domain model, or a SimpleNamespace from a service
    mock.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID
    label: str
    confidence: float
    created_at: datetime
    overlay_path: str


class RelabelRequest(BaseModel):
    """
    Request body for PATCH /predictions/{pid}/label.

    Sent by a reviewer correcting a prediction's label. The
    confidence < 0.7 gate that decides whether THIS specific
    prediction can be relabeled is service-layer logic (see
    PredictionService.relabel) — not a Casbin check, not a
    constraint on this schema. This schema only validates the
    shape of the body.

    extra="forbid": reject unknown fields. Defense in depth.
    min_length=1 on label: prevent silent acceptance of an empty
    string, which would otherwise pass type checks but produce a
    nonsense relabel.
    """

    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., min_length=1)
