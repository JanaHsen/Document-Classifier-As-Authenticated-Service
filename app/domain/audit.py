"""Audit log domain models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import PositiveInt


class AuditLogBase(BaseModel):
    """Base audit log schema."""

    actor_id: int = Field(..., description="ID of the user who performed the action")
    action: str = Field(..., max_length=100, description="Action performed")
    target_type: str = Field(..., max_length=50, description="Type of target entity")
    target_id: int = Field(..., description="ID of the affected record")


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log entry."""

    pass


class AuditLogOut(AuditLogBase):
    """Schema for audit log output."""

    id: PositiveInt = Field(..., description="Audit log ID")
    timestamp: datetime = Field(..., description="When the action occurred")

    model_config = ConfigDict(from_attributes=True)


class AuditLogInDB(AuditLogBase):
    """Schema for audit log as stored in database."""

    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
