import io
import os

import paramiko

SFTP_HOST = os.environ.get("SFTP_HOST", "sftp")
SFTP_PORT = int(os.environ.get("SFTP_PORT", "22"))
SFTP_USER = os.environ.get("SFTP_USER", "docuser")
SFTP_PASS = os.environ.get("SFTP_PASS", "docpass")
SFTP_PATH = os.environ.get("SFTP_PATH", "/uploads")


def upload_to_sftp(data: bytes, filename: str) -> str:
    """Write file bytes to SFTP /uploads and return the remote path."""
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)
    remote_path = f"{SFTP_PATH}/{filename}"
    try:
        sftp.putfo(io.BytesIO(data), remote_path)
    finally:
        sftp.close()
        transport.close()
    return remote_path
