# Owner: HAWRAA
import asyncio
import json
import tempfile
import time
import uuid
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
    print(json.dumps(record))


def _make_session():
    """Fresh async session with NullPool — safe for repeated asyncio.run() calls in the worker."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import NullPool
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False), engine


async def _update_batch_state(batch_id: int, state: BatchStatus) -> None:
    """Update batch state directly via repository (no actor — system-initiated)."""
    from app.domain.batch import BatchUpdate
    from app.repositories.batch_repository import BatchRepository

    session_factory, engine = _make_session()
    async with session_factory() as session:
        repo = BatchRepository(session)
        await repo.update_state(batch_id, BatchUpdate(state=state))
        await session.commit()
    await engine.dispose()


async def _save_prediction(
    batch_id: int, label: str, confidence: float, overlay_path: str
) -> None:
    """Save prediction to DB and invalidate cache."""
    import redis.asyncio as aioredis
    from fastapi_cache import FastAPICache
    from app.domain.prediction import PredictionCreate
    from app.infra.cache.redis_cache import _RedisBackend
    from app.repositories.prediction_repository import PredictionRepository

    # Reinitialize cache with a fresh Redis client bound to this event loop.
    # The client from _init_cache() belongs to the parent process's event loop
    # and deadlocks when used in the forked work-horse process.
    r = aioredis.from_url(settings.REDIS_URL)
    FastAPICache.init(_RedisBackend(r), prefix="docclass")

    session_factory, engine = _make_session()
    async with session_factory() as session:
        repo = PredictionRepository(session)
        await repo.create(PredictionCreate(
            batch_id=batch_id,
            label=label,
            confidence=confidence,
            overlay_path=overlay_path,
        ))
        await session.commit()
    await engine.dispose()

    await FastAPICache.clear()
    await r.aclose()


def process_job(job: dict) -> None:
    batch_id   = job["batch_id"]
    blob_path  = job["blob_path"]
    request_id = job.get("request_id", str(uuid.uuid4()))
    filename   = Path(blob_path).name

    _log("INFO", "job received", request_id=request_id, batch_id=batch_id, blob_path=blob_path)

    asyncio.run(_update_batch_state(batch_id, BatchStatus.PROCESSING))

    try:
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

        # Step 5: save prediction — PredictionService.create() handles DB write
        # and cache invalidation (invalidate_predictions_recent + invalidate_batch_detail)
        asyncio.run(_save_prediction(batch_id, result.label, result.confidence, overlay_path))

        asyncio.run(_update_batch_state(batch_id, BatchStatus.COMPLETE))
        _log("INFO", "job complete", request_id=request_id, batch_id=batch_id)

    except Exception as e:
        asyncio.run(_update_batch_state(batch_id, BatchStatus.FAILED))
        _log("ERROR", "job failed", request_id=request_id, batch_id=batch_id, error=str(e))
        raise


_model_cache: dict = {}


def _get_model(device: torch.device) -> torch.nn.Module:
    key = str(device)
    if key not in _model_cache:
        _model_cache[key] = load_model(device)
    return _model_cache[key]


async def _init_cache() -> None:
    """Initialize FastAPICache so CacheService.invalidate_* works in the worker process."""
    import redis.asyncio as aioredis
    from fastapi_cache import FastAPICache
    from app.infra.cache.redis_cache import _RedisBackend
    r = aioredis.from_url(settings.REDIS_URL)
    FastAPICache.init(_RedisBackend(r), prefix="docclass")


def main() -> None:
    from redis import Redis
    from rq import Worker, Queue

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _get_model(device)
    _log("INFO", "worker started, model loaded")

    asyncio.run(_init_cache())

    redis_conn = Redis.from_url(settings.REDIS_URL)
    queue = Queue("inference", connection=redis_conn)
    Worker([queue], connection=redis_conn).work()


if __name__ == "__main__":
    main()
