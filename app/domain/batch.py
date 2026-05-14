"""Batch domain model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import PositiveInt

from app.core.constants import BatchStatus


class BatchBase(BaseModel):
    """Base batch schema."""

    state: BatchStatus = Field(..., description="Current batch processing state")


class BatchCreate(BaseModel):
    """Schema for creating a new batch."""

    pass  # Batches are created with default state=PENDING


class BatchUpdate(BaseModel):
    """Schema for updating batch state."""

    state: BatchStatus = Field(..., description="Updated batch state")


class BatchOut(BatchBase):
    """Schema for batch output (response)."""

    id: PositiveInt = Field(..., description="Batch ID")
    created_at: datetime = Field(..., description="Batch creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class BatchInDB(BatchBase):
    """Schema for batch as stored in database."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
