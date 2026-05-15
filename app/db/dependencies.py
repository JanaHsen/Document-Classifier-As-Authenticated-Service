"""Dependency providers for repositories.

This module centralizes FastAPI dependency providers for all repositories,
keeping repository modules free of FastAPI imports. This allows repositories
to be imported in contexts where FastAPI is not installed (e.g., unit tests,
scripts).
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.repositories.audit_repository import AuditRepository
from app.repositories.batch_repository import BatchRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.user_repository import UserRepository


def get_batch_repository(
    session: AsyncSession = Depends(get_async_session),
) -> BatchRepository:
    """Provide BatchRepository dependency."""
    return BatchRepository(session)


def get_prediction_repository(
    session: AsyncSession = Depends(get_async_session),
) -> PredictionRepository:
    """Provide PredictionRepository dependency."""
    return PredictionRepository(session)


def get_user_repository(
    session: AsyncSession = Depends(get_async_session),
) -> UserRepository:
    """Provide UserRepository dependency."""
    return UserRepository(session)


def get_audit_repository(
    session: AsyncSession = Depends(get_async_session),
) -> AuditRepository:
    """Provide AuditRepository dependency."""
    return AuditRepository(session)
