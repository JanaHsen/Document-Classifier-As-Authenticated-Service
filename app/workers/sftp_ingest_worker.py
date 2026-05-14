# Owner: HADI
import os
import tempfile
import uuid

import paramiko

from app.core.config import settings
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

    for remote_path in watcher.watch():
        request_id = str(uuid.uuid4())
        filename = os.path.basename(remote_path)

        try:
            local_path = _download_from_sftp(remote_path)
            blob_path = _upload_to_minio(local_path, filename)

            # batch_id=0 is a placeholder — the real batch ID comes from
            # the batch service once the upload endpoint is wired up
            enqueue_inference_job(batch_id=0, blob_path=blob_path, request_id=request_id)

            logger.info("job enqueued", extra={"request_id": request_id, "blob_path": blob_path})
        except Exception as e:
            logger.error("failed to process file", extra={"path": remote_path, "error": str(e)})


if __name__ == "__main__":
    main()
