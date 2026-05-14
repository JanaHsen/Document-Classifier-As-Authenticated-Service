"""Prediction domain model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import PositiveInt, PositiveFloat


class PredictionBase(BaseModel):
    """Base prediction schema."""

    batch_id: PositiveInt = Field(..., description="Associated batch ID")
    label: str = Field(..., max_length=100, description="Predicted class label")
    confidence: PositiveFloat = Field(..., description="Confidence score (0-1)")
    overlay_path: str = Field(..., description="Path to overlay image")


class PredictionCreate(PredictionBase):
    """Schema for creating a new prediction record."""

    pass


class PredictionUpdate(BaseModel):
    """Schema for updating a prediction (e.g., relabeling)."""

    label: Optional[str] = Field(None, max_length=100, description="Corrected label")


class PredictionOut(PredictionBase):
    """Schema for prediction output (response)."""

    id: PositiveInt = Field(..., description="Prediction ID")
    created_at: datetime = Field(..., description="Prediction creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class PredictionInDB(PredictionBase):
    """Schema for prediction as stored in database."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
