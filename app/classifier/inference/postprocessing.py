# Owner: HAWRAA
from dataclasses import dataclass

from pydantic import BaseModel


class InferenceResult(BaseModel):
    label: str
    confidence: float


@dataclass
class PredictionResult:
    batch_id: int
    filename: str
    predicted_label: str
    confidence: float
    overlay_path: str


def format_prediction(
    batch_id: int,
    filename: str,
    predicted_label: str,
    confidence: float,
    overlay_path: str,
) -> PredictionResult:
    return PredictionResult(
        batch_id=batch_id,
        filename=filename,
        predicted_label=predicted_label,
        confidence=confidence,
        overlay_path=overlay_path,
    )
