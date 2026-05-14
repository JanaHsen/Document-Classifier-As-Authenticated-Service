# Owner: HADI
from functools import lru_cache

from rq import Queue

from app.infra.queue.redis_client import get_redis

INFERENCE_QUEUE_NAME = "inference"


@lru_cache(maxsize=1)
def get_inference_queue() -> Queue:
    # default_timeout must match the worker's expected job duration. CPU
    # inference + MinIO I/O can exceed RQ's 180s default, so allow 10 min.
    return Queue(INFERENCE_QUEUE_NAME, connection=get_redis(), default_timeout=600)


def enqueue_inference_job(batch_id: int, blob_path: str, request_id: str) -> None:
    queue = get_inference_queue()
    queue.enqueue(
        "app.workers.inference_worker.process_job",
        {
            "batch_id": batch_id,
            "blob_path": blob_path,
            "request_id": request_id,
        },
        job_timeout=600,
    )
