# Owner: HADI
import asyncio
import os
import tempfile
import time
import uuid

import paramiko

from app.core.config import settings
from app.domain.batch import BatchUpdate
from app.infra.blob.minio_client import _get_client as get_minio
from app.infra.logging.logger import get_logger
from app.infra.queue.rq_queue import enqueue_inference_job
from app.infra.sftp.watcher import SFTPWatcher

logger = get_logger("sftp_ingest_worker")

SFTP_HOST = os.environ.get("SFTP_HOST", "sftp")
SFTP_PORT = int(os.environ.get("SFTP_PORT", "22"))
SFTP_USER = os.environ.get("SFTP_USER", "docuser")
SFTP_PASS = os.environ.get("SFTP_PASS", "docpass")
SFTP_PATH = os.environ.get("SFTP_PATH", "/uploads")

# Files arriving within this window (in seconds) are grouped into the same batch.
BATCH_WINDOW_SECONDS = 30


async def _create_batch() -> int:
    """Create a new PENDING batch in the DB and return its ID."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import NullPool
    from app.domain.batch import BatchCreate
    from app.repositories.batch_repository import BatchRepository

    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    async with session_factory() as session:
        repo = BatchRepository(session)
        batch = await repo.create(BatchCreate())
        await session.commit()
        batch_id = batch.id
    await engine.dispose()
    return batch_id

async def _update_batch_file_count(batch_id: int, file_count: int) -> None:
    """Update the file count of an existing batch."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import NullPool
    from app.domain.batch import BatchCreate
    from app.repositories.batch_repository import BatchRepository

    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    async with session_factory() as session:
        repo = BatchRepository(session)
        batch = await repo.update_file_count(batch_id, BatchCreate(file_count=file_count))
        await session.commit()
        batch_id = batch.id
    await engine.dispose()
    return batch_id


def _download_from_sftp(remote_path: str) -> str:
    """Download file from SFTP to a local temp file, return local path."""
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)

    tmp = tempfile.NamedTemporaryFile(suffix=".tiff", delete=False)
    sftp.get(remote_path, tmp.name)
    sftp.close()
    return tmp.name


def _upload_to_minio(local_path: str, filename: str) -> str:
    """Upload file to MinIO documents bucket, return the blob path."""
    blob_path = f"incoming/{filename}"
    get_minio().fput_object(settings.MINIO_BUCKET, blob_path, local_path)
    return blob_path


def main() -> None:
    logger.info("sftp ingest worker started")

    watcher = SFTPWatcher(
        host=SFTP_HOST,
        port=SFTP_PORT,
        username=SFTP_USER,
        password=SFTP_PASS,
        remote_path=SFTP_PATH,
    )

    current_batch_id: int | None = None
    last_file_time: float = 0.0
    

    for remote_path in watcher.watch():
        request_id = str(uuid.uuid4())
        filename = os.path.basename(remote_path)
        now = time.time()

        try:
            # Start a new batch if none exists or the window has expired
            if current_batch_id is None or (now - last_file_time) > BATCH_WINDOW_SECONDS:
                current_batch_id = asyncio.run(_create_batch())
                count: int = 0
                logger.info("new batch created", extra={"batch_id": current_batch_id})
                
            last_file_time = now
            
            count += 1
            
            update_file_count = asyncio.run(_update_batch_file_count(current_batch_id, count))
            local_path = _download_from_sftp(remote_path)
            blob_path = _upload_to_minio(local_path, filename)
            enqueue_inference_job(
                batch_id=current_batch_id,
                blob_path=blob_path,
                request_id=request_id,
            )

            logger.info("job enqueued", extra={
                "request_id": request_id,
                "batch_id": current_batch_id,
                "blob_path": blob_path,
            })
        except Exception as e:
            logger.error("failed to process file", extra={"path": remote_path, "error": str(e)})


if __name__ == "__main__":
    main()
