from datetime import datetime

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from app.core.constants import BatchStatus, Role
from fastapi_users.db import SQLAlchemyBaseUserTable


class User(SQLAlchemyBaseUserTable[int], Base):
    """User ORM model with fastapi-users authentication fields."""

    __tablename__ = "users"

    # Primary key (required, not provided by mixin at runtime)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Custom fields
    role: Mapped[Role] = mapped_column(SQLEnum(Role), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="actor", foreign_keys="AuditLog.actor_id"
    )

    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_created_at", "created_at"),
    )


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[BatchStatus] = mapped_column(SQLEnum(BatchStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="batch", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_batches_state", "state"),
        Index("ix_batches_created_at", "created_at"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    overlay_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    batch: Mapped["Batch"] = relationship("Batch", back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_batch_id", "batch_id"),
        Index("ix_predictions_confidence", "confidence"),
        Index("ix_predictions_created_at", "created_at"),
        Index("ix_predictions_batch_created", "batch_id", "created_at"),
    )


class AuditLog(Base):
    """Audit log for tracking user actions on entities."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    actor: Mapped["User"] = relationship(
        "User", back_populates="audit_logs", foreign_keys=[actor_id]
    )

    __table_args__ = (
        Index("ix_audit_logs_actor_id", "actor_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_actor_timestamp", "actor_id", "timestamp"),
        Index("ix_audit_logs_target", "target_type", "target_id"),
    )
