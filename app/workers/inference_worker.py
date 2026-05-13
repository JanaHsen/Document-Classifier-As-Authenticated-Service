# Owner: HAWRAA
import json
import tempfile
import time
import uuid
from pathlib import Path

import torch

from app.classifier.inference.overlays import generate_overlay
from app.classifier.inference.postprocessing import format_prediction
from app.classifier.inference.predictor import load_model, predict

# ---------------------------------------------------------------------------
# MOCK IMPORTS — replace each line when merging with teammates
# ---------------------------------------------------------------------------

# Replace with: from app.infra.blob.minio_client import download_tiff, upload_overlay
from mock_hawraa.mock_minio import download_tiff, upload_overlay

# Replace with: from app.services.prediction_service import save_prediction
from mock_hawraa.mock_prediction_service import save_prediction

# Replace with: from app.services.cache_service import invalidate_batch
from mock_hawraa.mock_cache_service import invalidate_batch

# RQ queue swap: see main() below
# Replace with: from redis import Redis / from rq import Worker, Queue

# ---------------------------------------------------------------------------
# Logging — structured JSON per contract
# Replace with Hadi's logger when merged: from app.infra.logging.logger import log
# ---------------------------------------------------------------------------

def _log(level: str, message: str, **kwargs) -> None:
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "service": "inference_worker",
        "level": level,
        "message": message,
        **kwargs,
    }
    print(json.dumps(record))


# ---------------------------------------------------------------------------
# Job processor — called by RQ for each job
# ---------------------------------------------------------------------------

def process_job(job: dict) -> None:
    batch_id   = job["batch_id"]
    blob_path  = job["blob_path"]
    request_id = job.get("request_id", str(uuid.uuid4()))
    filename   = Path(blob_path).name

    _log("INFO", "job received", request_id=request_id, batch_id=batch_id, blob_path=blob_path)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = _get_model(device)

    # Step 1: download TIFF from MinIO
    local_tiff = download_tiff(blob_path)

    # Step 2: run inference
    result = predict(model, local_tiff, device)
    _log("INFO", "inference complete", request_id=request_id, label=result.label, confidence=round(result.confidence, 6))

    # Step 3: generate overlay PNG
    overlay_path = f"overlays/{Path(filename).stem}.png"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        local_overlay = tmp.name
    generate_overlay(local_tiff, result.label, result.confidence, local_overlay)

    # Step 4: upload overlay to MinIO
    upload_overlay(local_overlay, overlay_path)

    # Step 5: save prediction to DB via service layer
    prediction = format_prediction(batch_id, filename, result.label, result.confidence, overlay_path)
    save_prediction(prediction)

    # Step 6: invalidate cache via service layer
    invalidate_batch(batch_id)

    _log("INFO", "job complete", request_id=request_id, batch_id=batch_id)


# ---------------------------------------------------------------------------
# Model is loaded once at startup, not per job
# ---------------------------------------------------------------------------

_model_cache: dict = {}


def _get_model(device: torch.device) -> torch.nn.Module:
    key = str(device)
    if key not in _model_cache:
        _model_cache[key] = load_model(device)
    return _model_cache[key]


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Startup: validate and load model — raises if weights missing or SHA-256 mismatch
    _get_model(device)
    _log("INFO", "worker started, model loaded")

    # MOCK: single test job
    # Replace with real RQ worker when merging:
    #   from redis import Redis
    #   from rq import Worker, Queue
    #   from app.core.config import settings
    #   redis_conn = Redis.from_url(settings.REDIS_URL)
    #   queue = Queue("inference", connection=redis_conn)
    #   Worker([queue], connection=redis_conn).work()
    from mock_hawraa.mock_queue import start_mock_worker
    start_mock_worker(process_job)


if __name__ == "__main__":
    main()
