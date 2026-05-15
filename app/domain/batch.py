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
    """Schema for creating a new batch.

    Batches are created with default state=PENDING. file_count is how
    many documents the batch will hold — an upload of N files creates
    ONE batch with file_count=N. Defaults to 1 for callers that still
    create one-file batches (e.g. the SFTP ingest worker).
    """

    file_count: int = Field(default=1, ge=1, description="Documents in this batch")


class BatchUpdate(BaseModel):
    """Schema for updating batch state."""

    state: BatchStatus = Field(..., description="Updated batch state")


class BatchOut(BatchBase):
    """Schema for batch output (response)."""

    id: PositiveInt = Field(..., description="Batch ID")
    file_count: int = Field(..., description="Documents in this batch")
    created_at: datetime = Field(..., description="Batch creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class BatchInDB(BatchBase):
    """Schema for batch as stored in database."""

    id: int
    file_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
