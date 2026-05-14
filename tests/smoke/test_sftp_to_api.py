# Owner: HADI
"""
End-to-end smoke test: SFTP drop → ingest → inference → API result.

Requires the full docker-compose stack to be running.
Run with: pytest tests/smoke/ -v

Environment variables (all have defaults matching docker-compose defaults):
  API_BASE_URL   — default http://localhost:8000
  SFTP_HOST      — default localhost
  SFTP_PORT      — default 2222
  SFTP_USER      — default docuser
  SFTP_PASS      — default docpass
  SFTP_PATH      — default uploads
  SMOKE_TIMEOUT  — seconds to wait for batch completion, default 120
"""

import os
import time
import uuid
import pathlib
import pytest
import httpx
import paramiko

API_BASE   = os.getenv("API_BASE_URL", "http://localhost:8000")
SFTP_HOST  = os.getenv("SFTP_HOST", "localhost")
SFTP_PORT  = int(os.getenv("SFTP_PORT", "2222"))
SFTP_USER  = os.getenv("SFTP_USER", "docuser")
SFTP_PASS  = os.getenv("SFTP_PASS", "docpass")
SFTP_PATH  = os.getenv("SFTP_PATH", "uploads")
TIMEOUT    = int(os.getenv("SMOKE_TIMEOUT", "120"))

GOLDEN_TIFF = (
    pathlib.Path(__file__).parent.parent.parent
    / "app/classifier/eval/golden_images/test.tiff"
)

TEST_EMAIL    = f"smoke-{uuid.uuid4().hex[:8]}@test.local"
TEST_PASSWORD = "Smoke1234!"


def _register_and_login() -> str:
    """Register a fresh user and return a Bearer token."""
    with httpx.Client(base_url=API_BASE) as client:
        r = client.post("/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        assert r.status_code == 201, f"register failed: {r.text}"

        r = client.post(
            "/auth/jwt/login",
            data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 200, f"login failed: {r.text}"
        return r.json()["access_token"]


def _upload_via_sftp(local_path: pathlib.Path) -> str:
    """Upload file to SFTP and return the remote filename."""
    remote_name = f"{uuid.uuid4().hex}_{local_path.name}"
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        sftp.put(str(local_path), f"{SFTP_PATH}/{remote_name}")
    finally:
        sftp.close()
        transport.close()
    return remote_name


def _poll_for_complete_batch(token: str, deadline: float) -> dict:
    """Poll GET /batches until at least one batch reaches COMPLETE state."""
    headers = {"Authorization": f"Bearer {token}"}
    while time.time() < deadline:
        with httpx.Client(base_url=API_BASE) as client:
            r = client.get("/batches", headers=headers)
        assert r.status_code == 200, f"GET /batches failed: {r.text}"
        batches = r.json()
        for batch in batches:
            if batch["state"] == "complete":
                return batch
            if batch["state"] == "failed":
                pytest.fail(f"Batch {batch['id']} reached FAILED state")
        time.sleep(5)
    pytest.fail(f"No batch reached COMPLETE within {TIMEOUT}s")


@pytest.mark.smoke
def test_sftp_drop_triggers_classification():
    """
    Full pipeline: drop TIFF on SFTP → batch created → inference runs
    → batch state = complete → prediction visible in API.
    """
    assert GOLDEN_TIFF.exists(), f"Golden TIFF not found: {GOLDEN_TIFF}"

    token = _register_and_login()

    _upload_via_sftp(GOLDEN_TIFF)

    deadline = time.time() + TIMEOUT
    completed_batch = _poll_for_complete_batch(token, deadline)

    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=API_BASE) as client:
        r = client.get("/predictions/recent", headers=headers)
    assert r.status_code == 200, f"GET /predictions/recent failed: {r.text}"

    predictions = r.json()
    batch_predictions = [p for p in predictions if p["batch_id"] == completed_batch["id"]]
    assert len(batch_predictions) >= 1, "No predictions found for completed batch"

    pred = batch_predictions[0]
    assert pred["label"], "Prediction label is empty"
    assert 0.0 <= pred["confidence"] <= 1.0, "Confidence out of range"
