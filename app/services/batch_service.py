"""Batch Service.

Handles business logic for batch operations.
"""

import os
import uuid

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.constants import BatchStatus
from app.domain.batch import BatchCreate, BatchOut, BatchUpdate
from app.exceptions import NotFoundError
from app.infra.logging.logger import get_logger
from app.infra.sftp.uploader import upload_to_sftp
from app.repositories.batch_repository import BatchRepository
from app.services.audit_service import AuditService
from app.services.cache_service import CacheService
from app.api.schemas.batch import BatchRead, IngestQueued

logger = get_logger("batch_ingest")

# Classic TIFF (LE/BE) and BigTIFF signatures. The full decode is the
# inference worker's job; this cheap sniff just rejects obvious
# non-TIFF uploads early with a clear message.
_TIFF_MAGIC = (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")
_MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024


def _safe_object_name(filename: str) -> str:
    """Strip any path, then prefix a short uuid so concurrent uploads
    of the same filename never overwrite each other in the bucket."""
    base = os.path.basename((filename or "").replace("\\", "/")).strip()
    return f"{uuid.uuid4().hex[:8]}_{base or 'upload.tiff'}"


class BatchService:
    """Service for batch-related business logic."""

    def __init__(
        self,
        batch_repo: BatchRepository,
        cache_service: CacheService,
        audit_service: AuditService,
    ) -> None:
        self.batch_repo = batch_repo
        self.cache_service = cache_service
        self.audit_service = audit_service

    async def list_batches(self) -> list[BatchRead]:
        """List all batches, newest first."""
        batches = await self.batch_repo.list_all()
        # Convert domain BatchInDB to API BatchRead.
        return [
            BatchRead(
                id=b.id,
                created_at=b.created_at,
                status=b.state,
                file_count=b.file_count,
            )
            for b in batches
        ]

    async def get_batch(self, batch_id: int) -> BatchRead:
        """Get a single batch by ID."""
        try:
            b = await self.batch_repo.get_by_id(batch_id)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id '{batch_id}' not found",
            )
        return BatchRead(
            id=b.id,
            created_at=b.created_at,
            status=b.state,
            file_count=b.file_count,
        )

    async def ingest_upload(
        self, filename: str, data: bytes, request_id: str
    ) -> IngestQueued:
        """
        Validate a TIFF upload and drop it onto the SFTP /uploads directory.

        The sftp_ingest_worker picks it up within its poll interval (5 s),
        creates the batch, stores the blob in MinIO, and enqueues inference.
        This makes HTTP upload and SFTP drop use the exact same pipeline.
        """
        name = (filename or "").lower()
        if not (name.endswith(".tif") or name.endswith(".tiff")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{label}: only .tif/.tiff documents are accepted.",
            )
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{label}: uploaded file is empty.",
            )
        if len(data) > _MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"{label}: file exceeds the {settings.MAX_UPLOAD_MB} MB upload limit.",
            )
        if data[:4] not in _TIFF_MAGIC:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{label}: not a valid TIFF (bad signature).",
            )

    async def ingest_uploads(
        self, files: list[tuple[str, bytes]], request_id: str
    ) -> BatchRead:
        """
        Ingest one upload request as a SINGLE batch.

        All files dropped together are one unit of work: validate ->
        create ONE batch (file_count = number of files) -> store each
        blob -> enqueue one inference job per file, every job carrying
        the same batch_id. The inference worker only flips the batch
        to COMPLETE once it has written file_count predictions, so the
        status reflects the whole group, not the first file to finish.

        Validation is all-or-nothing: if any file fails the pre-flight
        checks the whole request is rejected with 400 and no batch is
        created — a partial batch would be ambiguous to the reviewer.

        Transaction boundary note: get_async_session commits only
        after the request returns, but the inference worker is a
        separate process that must see the batch row the instant it
        dequeues a job. So we commit the batch here, explicitly,
        before enqueueing — the service owns the transaction boundary.
        """
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files were uploaded.",
            )
        for filename, data in files:
            self._validate_tiff(filename, data)

        safe_name = _safe_object_name(filename)
        try:
            remote_path = await run_in_threadpool(upload_to_sftp, data, safe_name)
        except Exception as exc:
            logger.error(
                "sftp upload failed",
                extra={"request_id": request_id, "filename": filename, "error": str(exc)},
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not deliver file to SFTP ingest queue.",
            )

        logger.info(
            "file dropped on sftp",
            extra={"request_id": request_id, "remote_path": remote_path},
        )
        return IngestQueued(filename=safe_name, remote_path=remote_path)

    async def update_batch_state(
        self, batch_id: int, new_state: BatchStatus, actor_id: int
    ) -> BatchOut:
        """
        Update the state of a batch.

        Triggers audit log and cache invalidation.
        """
        # Fetch current batch to record old state for audit
        try:
            current = await self.batch_repo.get_by_id(batch_id)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id '{batch_id}' not found",
            )
        old_state = current.state

        # Perform update within transaction (session auto-commits via dependency)
        try:
            updated = await self.batch_repo.update_state(
                batch_id, BatchUpdate(state=new_state)
            )
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id '{batch_id}' not found",
            )

        # Audit log
        await self.audit_service.log_batch_state_change(
            actor_id=actor_id,
            batch_id=batch_id,
            old_state=old_state,
            new_state=new_state,
        )

        # Invalidate caches
        await self.cache_service.invalidate_batch_detail(batch_id)
        await self.cache_service.invalidate_batches_list()

        return BatchOut.model_validate(updated)


# Dependency provider
from fastapi import Depends

from app.db.dependencies import get_batch_repository
from app.services.audit_service import get_audit_service
from app.services.cache_service import get_cache_service


async def get_batch_service(
    batch_repo: BatchRepository = Depends(get_batch_repository),
    cache_service: CacheService = Depends(get_cache_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> BatchService:
    """FastAPI dependency for BatchService."""
    return BatchService(
        batch_repo=batch_repo,
        cache_service=cache_service,
        audit_service=audit_service,
    )
