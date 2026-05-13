# MOCK: Tarek's prediction service + PredictionRepository
#
# REPLACE WITH when merging:
#   from app.services.prediction_service import save_prediction
#   from app.db.session import get_db
#
# What the real implementation must do:
#   save_prediction(prediction) -> None:
#       opens a DB session, calls PredictionRepository.create(prediction),
#       commits the transaction
#       prediction fields per CONTRACTS.md:
#           batch_id, filename, predicted_label, confidence, overlay_path
#
# Note: cache invalidation is NOT done here — it lives in the service layer (Tarek's)

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
        "batch_id":       prediction.batch_id,
        "filename":       prediction.filename,
        "predicted_label": prediction.predicted_label,
        "confidence":     prediction.confidence,
        "overlay_path":   prediction.overlay_path,
    })

    with open(MOCK_DB_PATH, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"[mock_prediction_service] saved prediction to {MOCK_DB_PATH}")
