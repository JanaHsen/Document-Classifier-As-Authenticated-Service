"""Audit Repository.

Handles all database operations for audit logs.
No business logic, no HTTP exceptions, no cache invalidation.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog
from app.domain.audit import AuditLogInDB, AuditLogCreate
from app.exceptions import NotFoundError


class AuditRepository:
    """Repository for audit log-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: AuditLogCreate) -> AuditLogInDB:
        """Create a new audit log entry."""
        audit_log = AuditLog(
            actor_id=data.actor_id,
            action=data.action,
            target_type=data.target_type,
            target_id=data.target_id,
            old_value=data.old_value,
            new_value=data.new_value,
        )
        self.session.add(audit_log)
        await self.session.flush()
        await self.session.refresh(audit_log)
        return AuditLogInDB.model_validate(audit_log)

    async def get_by_id(self, audit_id: int) -> AuditLogInDB:
        """Get a single audit log by ID."""
        result = await self.session.execute(
            select(AuditLog).where(AuditLog.id == audit_id)
        )
        audit = result.scalar_one_or_none()
        if audit is None:
            raise NotFoundError(entity="AuditLog", identifier=str(audit_id))
        return AuditLogInDB.model_validate(audit)

    async def list_by_actor(self, actor_id: int, limit: int = 100) -> Sequence[AuditLogInDB]:
        """Get audit logs for a specific actor."""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.actor_id == actor_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        audits = result.scalars().all()
        return [AuditLogInDB.model_validate(a) for a in audits]

    async def list_entries(
        self, actor_id: int | None = None, action: str | None = None, limit: int = 100
    ) -> Sequence[AuditLogInDB]:
        """Get audit logs with optional filters."""
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)

        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)

        result = await self.session.execute(stmt)
        audits = result.scalars().all()
        return [AuditLogInDB.model_validate(a) for a in audits]

