# Owner: HAWRAA
from pydantic import BaseModel


class InferenceResult(BaseModel):
    label: str
    confidence: float
