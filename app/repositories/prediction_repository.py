"""Prediction Repository.

Handles all database operations for predictions.
No business logic, no HTTP exceptions, no cache invalidation.
"""

from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Prediction
from app.domain.prediction import PredictionInDB, PredictionCreate, PredictionUpdate
from app.exceptions import NotFoundError


class PredictionRepository:
    """Repository for prediction-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: PredictionCreate) -> PredictionInDB:
        """Create a new prediction record."""
        prediction = Prediction(
            batch_id=data.batch_id,
            label=data.label,
            confidence=data.confidence,
            overlay_path=data.overlay_path,
        )
        self.session.add(prediction)
        await self.session.flush()
        await self.session.refresh(prediction)
        return PredictionInDB.model_validate(prediction)

    async def get_by_id(self, prediction_id: int) -> PredictionInDB:
        """Get a single prediction by ID."""
        result = await self.session.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        prediction = result.scalar_one_or_none()
        if prediction is None:
            raise NotFoundError(entity="Prediction", identifier=str(prediction_id))
        return PredictionInDB.model_validate(prediction)

    async def get_recent(self, limit: int = 50) -> Sequence[PredictionInDB]:
        """Get most recent predictions ordered by creation date."""
        result = await self.session.execute(
            select(Prediction)
            .order_by(Prediction.created_at.desc())
            .limit(limit)
        )
        predictions = result.scalars().all()
        return [PredictionInDB.model_validate(p) for p in predictions]

    async def update_label(self, prediction_id: int, data: PredictionUpdate) -> PredictionInDB:
        """Update the label of a prediction (relabeling)."""
        stmt = (
            update(Prediction)
            .where(Prediction.id == prediction_id)
            .values(label=data.label)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        if result.rowcount == 0:
            raise NotFoundError(entity="Prediction", identifier=str(prediction_id))
        await self.session.flush()
        return await self.get_by_id(prediction_id)

