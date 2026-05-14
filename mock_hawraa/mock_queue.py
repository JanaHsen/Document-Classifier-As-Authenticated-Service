# MOCK: Hadi's RQ queue + Redis connection
#
# REPLACE WITH when merging:
#   from redis import Redis
#   from rq import Worker, Queue
#   from app.core.config import settings
#
#   redis_conn = Redis.from_url(settings.REDIS_URL)
#   queue = Queue("inference", connection=redis_conn)
#   worker = Worker([queue], connection=redis_conn)
#   worker.work()
#
# What the real implementation must do:
#   - connect to Redis using the URL from Vault via settings
#   - listen on the "inference" queue
#   - for each job dequeued, call process_job(job_payload)
#   - job payload matches the contract in CONTRACTS.md:
#     {"batch_id": int, "blob_path": str, "request_id": str}

import uuid


def get_test_job(blob_path: str = "app/classifier/eval/golden_images/test.tiff") -> dict:
    # Mock: returns a single hardcoded job for local testing
    # Real RQ would dequeue this from Redis automatically
    return {
        "batch_id": 1,
        "blob_path": blob_path,
        "request_id": str(uuid.uuid4()),
    }


def start_mock_worker(process_job_fn, blob_path: str = "app/classifier/eval/golden_images/test.tiff") -> None:
    # Mock: runs one job and exits
    # Real RQ worker would loop forever, picking up jobs as they arrive
    job = get_test_job(blob_path)
    print(f"[mock_queue] dequeued job: {job}")
    process_job_fn(job)
