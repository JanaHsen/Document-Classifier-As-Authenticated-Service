# Owner: HADI
import time
from collections.abc import Iterator

import paramiko

from app.infra.logging.logger import get_logger

logger = get_logger("sftp_watcher")


class SFTPWatcher:
    """Polls an SFTP directory for new TIFF files and yields their remote paths."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        remote_path: str,
        poll_interval: int = 5,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_path = remote_path
        self.poll_interval = poll_interval
        self._seen: set[str] = set()

    def _connect(self) -> paramiko.SFTPClient:
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.password)
        return paramiko.SFTPClient.from_transport(transport)

    def watch(self) -> Iterator[str]:
        """Yield remote file paths for new TIFF files as they appear."""
        logger.info("sftp watcher started", extra={"host": self.host, "path": self.remote_path})
        while True:
            try:
                sftp = self._connect()
                entries = sftp.listdir(self.remote_path)
                for filename in entries:
                    if filename.lower().endswith(".tiff") or filename.lower().endswith(".tif"):
                        remote_path = f"{self.remote_path}/{filename}"
                        if remote_path not in self._seen:
                            self._seen.add(remote_path)
                            logger.info("new file detected", extra={"path": remote_path})
                            yield remote_path
                sftp.close()
            except Exception as e:
                logger.error("sftp connection error", extra={"error": str(e)})
            time.sleep(self.poll_interval)
