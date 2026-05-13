from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base
from app.core.constants import BatchStatus, Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SQLEnum(Role), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="actor", foreign_keys="AuditLog.actor_id"
    )

    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_role", "role"),
    )


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[BatchStatus] = mapped_column(SQLEnum(BatchStatus), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
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
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    overlay_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    batch: Mapped["Batch"] = relationship("Batch", back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_batch_id", "batch_id"),
        Index("ix_predictions_label", "label"),
        Index("ix_predictions_confidence", "confidence"),
        Index("ix_predictions_created_at", "created_at"),
        Index("ix_predictions_batch_created", "batch_id", "created_at"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(500), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    actor: Mapped["User"] = relationship("User", back_populates="audit_logs", foreign_keys=[actor_id])

    __table_args__ = (
        Index("ix_audit_logs_actor_id", "actor_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_actor_timestamp", "actor_id", "timestamp"),
    )
