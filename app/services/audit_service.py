"""Audit Service.

Handles audit log creation with business rules.
"""

from app.domain.audit import AuditLogCreate, AuditLogOut
from app.repositories.audit_repository import AuditRepository


class AuditService:
    """Service for audit log operations."""

    def __init__(self, audit_repository: AuditRepository) -> None:
        self.audit_repository = audit_repository

    async def create(
        self, actor_id: int, action: str, target_type: str, target_id: int
    ) -> AuditLogOut:
        """Create a new audit log entry."""
        audit_in = AuditLogCreate(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
        )
        return await self.audit_repository.create(audit_in)

    async def log_role_change(
        self, actor_id: int, target_user_id: int, old_role: str, new_role: str
    ) -> AuditLogOut:
        """Log a user role change."""
        action = f"role_change: {old_role} -> {new_role}"
        return await self.create(
            actor_id=actor_id, action=action, target_type="user", target_id=target_user_id
        )

    async def log_batch_state_change(
        self, actor_id: int, batch_id: int, old_state: str, new_state: str
    ) -> AuditLogOut:
        """Log a batch state change."""
        action = f"batch_state_change: {old_state} -> {new_state}"
        return await self.create(
            actor_id=actor_id, action=action, target_type="batch", target_id=batch_id
        )

    async def log_relabel(
        self, actor_id: int, prediction_id: int, old_label: str, new_label: str
    ) -> AuditLogOut:
        """Log a prediction relabel."""
        action = f"relabel: {old_label} -> {new_label}"
        return await self.create(
            actor_id=actor_id,
            action=action,
            target_type="prediction",
            target_id=prediction_id,
        )


# Dependency provider
from fastapi import Depends

from app.db.dependencies import get_audit_repository


async def get_audit_service(
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> AuditService:
    """FastAPI dependency for AuditService."""
    return AuditService(audit_repo=audit_repo)
