# Owner: HAWRAA
import json
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path

import torch

from app.classifier.inference.overlays import generate_overlay
from app.classifier.inference.predictor import load_model, predict
from app.core.config import settings
from app.core.constants import BatchStatus
from app.infra.blob.minio_client import download_tiff, upload_overlay


def _log(level: str, message: str, **kwargs) -> None:
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "service": "inference_worker",
        "level": level,
        "message": message,
        **kwargs,
    }
    print(json.dumps(record), flush=True)


def _update_batch_state(batch_id: int, state: BatchStatus) -> None:
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool
    engine = create_engine(settings.DATABASE_SYNC_URL, poolclass=NullPool)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE batches SET state = :state, updated_at = NOW() WHERE id = :id"),
            {"state": state.value, "id": batch_id},
        )
    engine.dispose()


def _save_prediction(batch_id: int, label: str, confidence: float, overlay_path: str) -> None:
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool
    import redis as sync_redis

    engine = create_engine(settings.DATABASE_SYNC_URL, poolclass=NullPool)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO predictions (batch_id, label, confidence, overlay_path, created_at)"
                " VALUES (:batch_id, :label, :confidence, :overlay_path, :created_at)"
            ),
            {
                "batch_id": batch_id,
                "label": label,
                "confidence": confidence,
                "overlay_path": overlay_path,
                "created_at": datetime.utcnow(),
            },
        )
    engine.dispose()

    # Invalidate the Redis cache so the API serves fresh data
    r = sync_redis.from_url(settings.REDIS_URL)
    for key in r.keys("docclass:*"):
        r.delete(key)
    r.close()


def process_job(job: dict) -> None:
    batch_id   = job["batch_id"]
    blob_path  = job["blob_path"]
    request_id = job.get("request_id", str(uuid.uuid4()))
    filename   = Path(blob_path).name

    _log("INFO", "job received", request_id=request_id, batch_id=batch_id, blob_path=blob_path)
    _update_batch_state(batch_id, BatchStatus.PROCESSING)

    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model  = _get_model(device)

        local_tiff = download_tiff(blob_path)

        result = predict(model, local_tiff, device)
        _log("INFO", "inference complete", request_id=request_id, label=result.label, confidence=round(result.confidence, 6))

        overlay_path = f"overlays/{Path(filename).stem}.png"
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            local_overlay = tmp.name
        generate_overlay(local_tiff, result.label, result.confidence, local_overlay)

        upload_overlay(local_overlay, overlay_path)

        _save_prediction(batch_id, result.label, result.confidence, overlay_path)

        _update_batch_state(batch_id, BatchStatus.COMPLETE)
        _log("INFO", "job complete", request_id=request_id, batch_id=batch_id)

    except Exception as e:
        _update_batch_state(batch_id, BatchStatus.FAILED)
        _log("ERROR", "job failed", request_id=request_id, batch_id=batch_id, error=str(e))
        raise


_model_cache: dict = {}


def _get_model(device: torch.device) -> torch.nn.Module:
    key = str(device)
    if key not in _model_cache:
        _model_cache[key] = load_model(device)
    return _model_cache[key]


def main() -> None:
    from redis import Redis
    from rq import Worker, Queue

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _get_model(device)
    _log("INFO", "worker started, model loaded")

    redis_conn = Redis.from_url(settings.REDIS_URL)
    queue = Queue("inference", connection=redis_conn, default_timeout=600)
    Worker([queue], connection=redis_conn).work()


if __name__ == "__main__":
    main()
