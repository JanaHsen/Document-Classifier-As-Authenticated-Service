"""
Pydantic API schemas for the Batch resource.

A Batch represents a unit of work in the ingestion pipeline — one
TIFF (or, eventually, a group of files dropped together) uploaded
via SFTP, stored in MinIO, and queued for classification.

This is the API-boundary view — what HTTP clients see. The internal
domain model (Tarek's app/domain/batch.py) and the SQLAlchemy ORM
model (Tarek's app/db/models.py) may carry additional fields not
exposed here.

TENTATIVE FIELDS — coordinate with Tarek before settling.
The exact column set on the batches table is Tarek's call. The
fields below are the minimum the GET endpoints need to render
something useful. If Tarek's data model includes more (source_path,
processing_started_at, error_message, etc.), add them here as
needed. Card 5's two GET endpoints (/batches, /batches/{bid}) both
return BatchRead.

BatchCreate is intentionally not defined here even though Card 8
lists it. No card creates a POST/PATCH route for batches — they
are created by the SFTP ingestion worker writing directly to the
DB. Add BatchCreate later only if a manual-create endpoint becomes
a requirement.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BatchStatus(str, Enum):
    """
    Lifecycle of a batch as it moves through the pipeline.

    Coordinate with Tarek and Hadi: these strings must match the
    values that the SFTP ingestion worker (Hadi) and the inference
    worker (Hawraa) write to the batches.status column. The string
    enum gives the same typo-safety as Role on User.
    """

    PENDING = "pending"        # uploaded to MinIO, RQ job enqueued, not yet picked up
    PROCESSING = "processing"  # an inference worker has claimed the job
    COMPLETE = "complete"      # predictions written, annotated overlays generated
    FAILED = "failed"          # worker hit an error; see audit log and worker logs


class BatchRead(BaseModel):
    """
    Response shape for GET /batches and GET /batches/{bid}.

    from_attributes=True so FastAPI can serialize directly from a
    SQLAlchemy ORM instance or a Pydantic domain model without an
    explicit conversion step in the router. The service layer can
    return either; this schema reads whatever exposes the right
    attribute names.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    status: BatchStatus
    file_count: int
