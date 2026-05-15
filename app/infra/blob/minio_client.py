# Owner: HADI
import io
import tempfile

from functools import lru_cache

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.exceptions import NotFoundError

OVERLAY_BUCKET = "overlays"


@lru_cache(maxsize=1)
def _get_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def download_tiff(blob_path: str) -> str:
    """Download a TIFF from MinIO and return the local temp file path."""
    client = _get_client()
    tmp = tempfile.NamedTemporaryFile(suffix=".tiff", delete=False)
    client.fget_object(settings.MINIO_BUCKET, blob_path, tmp.name)
    return tmp.name


def upload_overlay(local_path: str, overlay_path: str) -> None:
    """Upload a local overlay PNG to the overlays bucket in MinIO."""
    client = _get_client()
    client.fput_object(
        OVERLAY_BUCKET, overlay_path, local_path, content_type="image/png"
    )


def download_overlay(overlay_path: str) -> bytes:
    """
    Fetch an overlay PNG from the overlays bucket and return its bytes.

    Raises NotFoundError (the same non-HTTP exception the repository
    layer raises) when the object or bucket is missing, so the
    service layer can translate it to a 404 uniformly. Other S3
    errors propagate unchanged.
    """
    client = _get_client()
    try:
        response = client.get_object(OVERLAY_BUCKET, overlay_path)
    except S3Error as exc:
        if exc.code in ("NoSuchKey", "NoSuchBucket"):
            raise NotFoundError(entity="Overlay", identifier=overlay_path)
        raise
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def upload_document(data: bytes, object_name: str) -> str:
    """
    Upload a raw document into the documents bucket under the same
    ``incoming/`` prefix the SFTP ingest worker uses, so a UI upload
    is indistinguishable to the inference worker. Returns the blob
    path to put on the inference job.
    """
    client = _get_client()
    blob_path = f"incoming/{object_name}"
    client.put_object(
        settings.MINIO_BUCKET,
        blob_path,
        io.BytesIO(data),
        length=len(data),
        content_type="image/tiff",
    )
    return blob_path
