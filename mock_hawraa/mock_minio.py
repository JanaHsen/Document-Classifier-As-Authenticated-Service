# MOCK: Hadi's MinIO client
#
# REPLACE WITH when merging:
#   from app.infra.blob.minio_client import download_tiff, upload_overlay
#
# What the real implementation must do:
#   download_tiff(blob_path) -> str:
#       downloads the TIFF at blob_path from MinIO,
#       saves it to a temp file, and returns the local temp path
#
#   upload_overlay(local_path, overlay_path) -> None:
#       uploads the file at local_path to MinIO
#       at the key overlay_path inside the overlays bucket

import shutil
from pathlib import Path

MOCK_OVERLAYS_DIR = Path("mock_hawraa/overlays")


def download_tiff(blob_path: str) -> str:
    # Mock: treat blob_path as a local file path and return it as-is
    # Real MinIO would download from the bucket and return a temp path
    return blob_path


def upload_overlay(local_path: str, overlay_path: str) -> None:
    # Mock: copy the overlay to mock_hawraa/overlays/ instead of uploading to MinIO
    MOCK_OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
    dest = MOCK_OVERLAYS_DIR / Path(overlay_path).name
    shutil.copy(local_path, dest)
    print(f"[mock_minio] overlay saved locally at {dest}")
