# MOCK: Tarek's prediction service + PredictionRepository
#
# REPLACE WITH when merging:
#   PredictionService.create() from app.services.prediction_service
#
# What the real swap requires (NOT a one-line swap):
#   - PredictionService.create() is async — worker must use asyncio.run() or be refactored async
#   - Requires injected dependencies: PredictionRepository, CacheService, AuditService
#   - Outside FastAPI's request context, these must be wired up manually with a DB session
#   - Signature: create(batch_id, label, confidence, overlay_path) — no filename parameter
#   - Cache invalidation (invalidate_predictions_recent + invalidate_batch_detail) happens
#     inside create() automatically — remove the separate Step 6 invalidate_batch call
#
# Note: filename is intentionally excluded — Tarek's DB Prediction model has no filename column

import json
from pathlib import Path

MOCK_DB_PATH = Path("mock_hawraa/mock_predictions.json")


def save_prediction(prediction) -> None:
    # Mock: appends prediction to a local JSON file instead of writing to PostgreSQL
    MOCK_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    existing = []
    if MOCK_DB_PATH.exists():
        with open(MOCK_DB_PATH) as f:
            existing = json.load(f)

    existing.append({
        "batch_id":     prediction.batch_id,
        "label":        prediction.label,
        "confidence":   prediction.confidence,
        "overlay_path": prediction.overlay_path,
    })

    with open(MOCK_DB_PATH, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"[mock_prediction_service] saved prediction to {MOCK_DB_PATH}")
