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


class AuditAction(str, Enum):
    """Allowed audit log action types."""

    CHANGE_ROLE = "change_role"
    RELABEL_PRED = "relabel_pred"
    CHANGE_STATE = "change_state"
