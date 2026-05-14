from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int
    action: str
    target: str
    timestamp: datetime
