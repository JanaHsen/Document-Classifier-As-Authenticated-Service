"""Audit Service.

Handles audit log creation with business rules.
"""

from uuid import UUID

from app.domain.audit import AuditLogCreate, AuditLogOut
from app.repositories.audit_repository import AuditRepository


class AuditService:
    """Service for audit log operations."""

    def __init__(self, audit_repository: AuditRepository) -> None:
        self.audit_repository = audit_repository

    async def create(self, actor_id: UUID, action: str, target: str) -> AuditLogOut:
        """Create a new audit log entry."""
        audit_in = AuditLogCreate(actor_id=actor_id, action=action, target=target)
        return await self.audit_repository.create(audit_in)

    async def log_role_change(
        self, actor_id: UUID, target_user_id: UUID, old_role: str, new_role: str
    ) -> AuditLogOut:
        """Log a user role change."""
        action = f"role_change: {old_role} -> {new_role}"
        target = f"user_id={target_user_id}"
        return await self.create(actor_id, action, target)

    async def log_batch_state_change(
        self, actor_id: UUID, batch_id: int, old_state: str, new_state: str
    ) -> AuditLogOut:
        """Log a batch state change."""
        action = f"batch_state_change: {old_state} -> {new_state}"
        target = f"batch_id={batch_id}"
        return await self.create(actor_id, action, target)

    async def log_relabel(
        self, actor_id: UUID, prediction_id: int, old_label: str, new_label: str
    ) -> AuditLogOut:
        """Log a prediction relabel."""
        action = f"relabel: {old_label} -> {new_label}"
        target = f"prediction_id={prediction_id}"
        return await self.create(actor_id, action, target)


# Dependency provider
from fastapi import Depends

from app.repositories.audit_repository import (
    AuditRepository,
    get_audit_repository,
)


async def get_audit_service(
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> AuditService:
    """FastAPI dependency for AuditService."""
    return AuditService(audit_repo=audit_repo)
