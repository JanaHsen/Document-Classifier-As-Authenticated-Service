"""Prediction Service.

Handles business logic for prediction operations.
"""

from typing import List

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.domain.prediction import PredictionOut, PredictionCreate, PredictionUpdate
from app.exceptions import NotFoundError
from app.infra.blob.minio_client import download_overlay
from app.repositories.prediction_repository import PredictionRepository
from app.services.audit_service import AuditService
from app.services.cache_service import CacheService


class PredictionService:
    """Service for prediction-related business logic."""

    def __init__(
        self,
        prediction_repo: PredictionRepository,
        cache_service: CacheService,
        audit_service: AuditService,
    ) -> None:
        self.prediction_repo = prediction_repo
        self.cache_service = cache_service
        self.audit_service = audit_service

    async def get_recent(self, limit: int = 50) -> List[PredictionOut]:
        """Get most recent predictions."""
        predictions = await self.prediction_repo.get_recent(limit)
        return [PredictionOut.model_validate(p) for p in predictions]

    async def get_overlay(self, prediction_id: int) -> bytes:
        """
        Return the annotated overlay PNG bytes for a prediction.

        Read-only artifact access: no cache invalidation, no audit
        log (consistent with the architectural rule that those side
        effects belong to state-changing operations only).

        Raises 404 if the prediction does not exist or its overlay
        object is missing from blob storage. The blocking MinIO read
        runs in a threadpool so it does not stall the event loop.
        """
        try:
            prediction = await self.prediction_repo.get_by_id(prediction_id)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prediction with id '{prediction_id}' not found",
            )

        try:
            return await run_in_threadpool(
                download_overlay, prediction.overlay_path
            )
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Overlay for prediction '{prediction_id}' is not "
                    "available in storage"
                ),
            )

    async def create(
        self,
        batch_id: int,
        label: str,
        confidence: float,
        overlay_path: str,
    ) -> PredictionOut:
        """
        Create a new prediction record.

        This is called by the inference worker after classification.
        Triggers cache invalidation for recent predictions and batch detail.
        """
        prediction_in_db = await self.prediction_repo.create(
            PredictionCreate(
                batch_id=batch_id,
                label=label,
                confidence=confidence,
                overlay_path=overlay_path,
            )
        )

        # Invalidate caches: recent predictions and the corresponding batch detail
        await self.cache_service.invalidate_predictions_recent()
        await self.cache_service.invalidate_batch_detail(batch_id)

        return PredictionOut.model_validate(prediction_in_db)

    async def relabel(
        self,
        prediction_id: int,
        new_label: str,
        actor_id: int,
    ) -> PredictionOut:
        """
        Relabel a prediction with corrected label.

        Business rules:
        - Only allowed if confidence < 0.7 (human review needed)
        - Records audit log
        - Invalidates recent predictions cache
        """
        # Fetch existing prediction to check confidence and record old label
        try:
            current = await self.prediction_repo.get_by_id(prediction_id)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prediction with id '{prediction_id}' not found",
            )
        old_label = current.label

        if current.confidence >= 0.7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Prediction confidence {current.confidence} is too high for relabel; "
                    "human review only allowed for low-confidence predictions (< 0.7)"
                ),
            )

        # Perform update
        try:
            updated_in_db = await self.prediction_repo.update_label(
                prediction_id, PredictionUpdate(label=new_label)
            )
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prediction with id '{prediction_id}' not found",
            )

        # Audit log
        await self.audit_service.log_relabel(
            actor_id=actor_id,
            prediction_id=prediction_id,
            old_label=old_label,
            new_label=new_label,
        )

        # Invalidate cache
        await self.cache_service.invalidate_predictions_recent()
        await self.cache_service.invalidate_batch_detail(current.batch_id)

        return PredictionOut.model_validate(updated_in_db)


# Dependency provider
from fastapi import Depends

from app.db.dependencies import get_prediction_repository
from app.services.audit_service import get_audit_service
from app.services.cache_service import get_cache_service


async def get_prediction_service(
    prediction_repo: PredictionRepository = Depends(get_prediction_repository),
    cache_service: CacheService = Depends(get_cache_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> PredictionService:
    """FastAPI dependency for PredictionService."""
    return PredictionService(
        prediction_repo=prediction_repo,
        cache_service=cache_service,
        audit_service=audit_service,
    )
