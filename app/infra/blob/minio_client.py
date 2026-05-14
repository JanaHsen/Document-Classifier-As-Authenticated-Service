# Owner: HADI
import tempfile

from functools import lru_cache

from minio import Minio

from app.core.config import settings


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
    client.fput_object("overlays", overlay_path, local_path, content_type="image/png")
