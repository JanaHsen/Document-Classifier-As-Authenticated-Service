import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import User, Batch, Prediction, AuditLog
from app.core.constants import BatchStatus, Role


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def sync_engine():
    """Create a synchronous engine for schema creation."""
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        TEST_SYNC_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
async def async_engine():
    """Create an async engine for tests."""
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


@pytest.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh async session for each test."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False, autoflush=False
    )
    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def user_factory(async_session):
    """Factory to create test users."""

    async def _create_user(
        email: str = "test@example.com",
        hashed_password: str = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # bcrypt hash of "secret"
        role: Role = Role.REVIEWER,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role,
        )
        async_session.add(user)
        await async_session.flush()
        await async_session.refresh(user)
        return user

    return _create_user


@pytest.fixture
def batch_factory(async_session):
    """Factory to create test batches."""

    async def _create_batch(
        state: BatchStatus = BatchStatus.PENDING,
    ) -> Batch:
        batch = Batch(state=state)
        async_session.add(batch)
        await async_session.flush()
        await async_session.refresh(batch)
        return batch

    return _create_batch


@pytest.fixture
def prediction_factory(async_session):
    """Factory to create test predictions."""

    async def _create_prediction(
        batch_id: int,
        label: str = "invoice",
        confidence: float = 0.95,
        overlay_path: str = "overlays/invoice1.png",
    ) -> Prediction:
        prediction = Prediction(
            batch_id=batch_id,
            label=label,
            confidence=confidence,
            overlay_path=overlay_path,
        )
        async_session.add(prediction)
        await async_session.flush()
        await async_session.refresh(prediction)
        return prediction

    return _create_prediction


@pytest.fixture
def audit_log_factory(async_session):
    """Factory to create test audit logs."""

    async def _create_audit_log(
        actor_id: int,
        action: str = "user.login",
        target: str = "user",
    ) -> AuditLog:
        audit_log = AuditLog(
            actor_id=actor_id,
            action=action,
            target=target,
        )
        async_session.add(audit_log)
        await async_session.flush()
        await async_session.refresh(audit_log)
        return audit_log

    return _create_audit_log


@pytest.fixture
def populated_db(
    async_session,
    user_factory,
    batch_factory,
    prediction_factory,
    audit_log_factory,
):
    """Create a populated database with sample data."""

    async def _populate():
        # Create users
        admin = await user_factory(email="admin@example.com", role=Role.ADMIN)
        reviewer = await user_factory(email="reviewer@example.com", role=Role.REVIEWER)
        auditor = await user_factory(email="auditor@example.com", role=Role.AUDITOR)

        # Create batch
        batch = await batch_factory(state=BatchStatus.PENDING)

        # Create predictions
        pred1 = await prediction_factory(batch_id=batch.id, label="invoice")
        pred2 = await prediction_factory(
            batch_id=batch.id, label="passport", confidence=0.87
        )

        # Create audit logs
        await audit_log_factory(actor_id=admin.id, action="user.create")
        await audit_log_factory(actor_id=reviewer.id, action="prediction.correct")

        await async_session.commit()
        return {
            "admin": admin,
            "reviewer": reviewer,
            "auditor": auditor,
            "batch": batch,
            "predictions": [pred1, pred2],
        }

    return _populate
