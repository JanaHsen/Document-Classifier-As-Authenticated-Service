from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):
    """
    Response shape for entries in GET /audit-log.

    Action format suggestion: dotted lowercase namespaces such as
    "users.role.toggle", "predictions.relabel", "batches.state.change".
    Coordinate with Tarek so the values written by the service layer
    match what auditors expect to filter on. Modeled as a free string
    here to stay permissive; switch to a string Enum later if a
    fixed vocabulary becomes desirable.

    target_id is required and typed as UUID because all three
    auditable actions (role change, relabel, batch state change)
    target an entity with a UUID id. If a non-UUID target ever
    needs to be recorded, widen the type then.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID
    action: str
    target_id: UUID
    timestamp: datetime
