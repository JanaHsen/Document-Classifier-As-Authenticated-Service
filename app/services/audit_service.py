"""Audit Service.

Handles audit log creation with business rules.
"""

from app.core.constants import AuditAction
from app.domain.audit import AuditLogCreate, AuditLogInDB, AuditLogOut
from app.repositories.audit_repository import AuditRepository


class AuditService:
    """Service for audit log operations."""

    def __init__(self, audit_repository: AuditRepository) -> None:
        self.audit_repository = audit_repository

    async def create(
        self,
        actor_id: int,
        action: AuditAction,
        target_type: str,
        target_id: int,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> AuditLogOut:
        """Create a new audit log entry."""
        audit_in = AuditLogCreate(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
        )
        audit_in_db = await self.audit_repository.create(audit_in)
        return AuditLogOut.model_validate(audit_in_db)

    async def log_role_change(
        self, actor_id: int, target_user_id: int, old_role: str, new_role: str
    ) -> AuditLogOut:
        """Log a user role change."""
        return await self.create(
            actor_id=actor_id,
            action=AuditAction.CHANGE_ROLE,
            target_type="user",
            target_id=target_user_id,
            old_value={"role": old_role},
            new_value={"role": new_role},
        )

    async def log_batch_state_change(
        self, actor_id: int, batch_id: int, old_state: str, new_state: str
    ) -> AuditLogOut:
        """Log a batch state change."""
        return await self.create(
            actor_id=actor_id,
            action=AuditAction.CHANGE_STATE,
            target_type="batch",
            target_id=batch_id,
            old_value={"state": old_state},
            new_value={"state": new_state},
        )

    async def log_relabel(
        self, actor_id: int, prediction_id: int, old_label: str, new_label: str
    ) -> AuditLogOut:
        """Log a prediction relabel."""
        return await self.create(
            actor_id=actor_id,
            action=AuditAction.RELABEL_PRED,
            target_type="prediction",
            target_id=prediction_id,
            old_value={"label": old_label},
            new_value={"label": new_label},
        )

    async def list_entries(
        self, actor: int | None = None, action: str | None = None, limit: int = 100
    ) -> list[AuditLogOut]:
        """List audit log entries with optional filters."""
        audits_in_db = await self.audit_repository.list_entries(
            actor_id=actor, action=action, limit=limit
        )
        return [AuditLogOut.model_validate(a) for a in audits_in_db]


# Dependency provider
from fastapi import Depends

from app.db.dependencies import get_audit_repository


async def get_audit_service(
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> AuditService:
    """FastAPI dependency for AuditService."""
    return AuditService(audit_repository=audit_repository)
