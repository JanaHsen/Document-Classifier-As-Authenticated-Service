"""Batch Service.

Handles business logic for batch operations.
"""

from typing import List
from uuid import UUID

from fastapi import HTTPException, status

from app.core.constants import BatchStatus
from app.domain.batch import BatchOut, BatchUpdate
from app.exceptions import NotFoundError
from app.repositories.batch_repository import BatchRepository
from app.services.audit_service import AuditService
from app.services.cache_service import CacheService


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

    async def list_batches(self) -> List[BatchOut]:
        """List all batches, newest first."""
        batches = await self.batch_repo.list_all()
        return [BatchOut.model_validate(b) for b in batches]

    async def get_batch(self, batch_id: int) -> BatchOut:
        """Get a single batch by ID."""
        try:
            batch_in_db = await self.batch_repo.get_by_id(batch_id)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id '{batch_id}' not found",
            )
        return BatchOut.model_validate(batch_in_db)

    async def update_batch_state(
        self, batch_id: int, new_state: BatchStatus, actor_id: UUID
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
