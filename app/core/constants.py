from enum import Enum


class BatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class Role(str, Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"
