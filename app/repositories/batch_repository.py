"""Batch Repository.

Handles all database operations for batches.
No business logic, no HTTP exceptions, no cache invalidation.
"""

from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Batch
from app.domain.batch import BatchInDB, BatchCreate, BatchUpdate
from app.exceptions import NotFoundError


class BatchRepository:
    """Repository for batch-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: BatchCreate) -> BatchInDB:
        """Create a new batch with default PENDING state."""
        from app.core.constants import BatchStatus

        batch = Batch(state=BatchStatus.PENDING, file_count=data.file_count)
        self.session.add(batch)
        await self.session.flush()
        await self.session.refresh(batch)
        return BatchInDB.model_validate(batch)

    async def get_by_id(self, batch_id: int) -> BatchInDB:
        """Get a single batch by ID."""
        result = await self.session.execute(
            select(Batch).where(Batch.id == batch_id)
        )
        batch = result.scalar_one_or_none()
        if batch is None:
            raise NotFoundError(entity="Batch", identifier=str(batch_id))
        return BatchInDB.model_validate(batch)

    async def list_all(self) -> Sequence[BatchInDB]:
        """List all batches ordered by creation date (newest first)."""
        result = await self.session.execute(
            select(Batch).order_by(Batch.created_at.desc())
        )
        batches = result.scalars().all()
        return [BatchInDB.model_validate(b) for b in batches]

    async def update_state(self, batch_id: int, data: BatchUpdate) -> BatchInDB:
        """Update the state of a batch."""
        stmt = (
            update(Batch)
            .where(Batch.id == batch_id)
            .values(state=data.state)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        if result.rowcount == 0:
            raise NotFoundError(entity="Batch", identifier=str(batch_id))
        await self.session.flush()
        return await self.get_by_id(batch_id)

