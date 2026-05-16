from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.core.constants import AuditAction


class AuditLogEntry(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int
    action: AuditAction
    target_type: str
    target_id: int
    old_value: dict | None = None
    new_value: dict | None = None
    timestamp: datetime
