# Owner: HADI + HAWRAA
from app.infra.logging.logger import get_logger

logger = get_logger("startup")


def log_startup_complete() -> None:
    logger.info("application started", extra={"event": "startup"})


def log_shutdown() -> None:
    logger.info("application shutting down", extra={"event": "shutdown"})
