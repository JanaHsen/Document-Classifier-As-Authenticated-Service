# Owner: HAWRAA
import hashlib
import json
from pathlib import Path

import torch
import torch.nn as nn
from torchvision.models import convnext_tiny

from app.classifier.inference.postprocessing import InferenceResult
from app.classifier.inference.preprocessing import preprocess_image

WEIGHTS_PATH = Path("app/classifier/models/classifier.pt")
MODEL_CARD_PATH = Path("app/classifier/models/model_card.json")
LABELS_PATH = Path("app/classifier/models/labels.json")


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_labels() -> list[str]:
    with open(LABELS_PATH) as f:
        return json.load(f)


def _validate_model() -> None:
    if not WEIGHTS_PATH.exists():
        raise RuntimeError(f"Model weights not found at {WEIGHTS_PATH}")

    with open(MODEL_CARD_PATH) as f:
        card = json.load(f)

    expected_sha256 = card.get("sha256")
    if not expected_sha256:
        raise RuntimeError("model_card.json is missing sha256 field")

    actual_sha256 = _compute_sha256(WEIGHTS_PATH)
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"SHA-256 mismatch. Expected {expected_sha256}, got {actual_sha256}"
        )

    min_threshold = card.get("min_accuracy_threshold", 0.0)
    reported_top1 = card.get("test_top1", 0.0)
    if reported_top1 < min_threshold:
        raise RuntimeError(
            f"Model top-1 {reported_top1} is below threshold {min_threshold}"
        )


def load_model(device: torch.device) -> nn.Module:
    _validate_model()

    labels = _load_labels()
    model = convnext_tiny(weights=None)
    model.classifier[2] = nn.Linear(model.classifier[2].in_features, len(labels))
    model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=device, weights_only=False))  # noqa: S614
    model.to(device)
    model.eval()
    return model


def predict(model: nn.Module, image_path: str, device: torch.device) -> InferenceResult:
    labels = _load_labels()
    tensor = preprocess_image(image_path).to(device)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)
        confidence, idx = probs.max(1)
    return InferenceResult(label=labels[idx.item()], confidence=confidence.item())
