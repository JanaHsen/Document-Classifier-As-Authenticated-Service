"""User Service.

Handles business logic for user management.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status

from app.db.dependencies import get_user_repository
from app.db.models import User as UserModel
from app.domain.user import UserOut, UserUpdate
from app.exceptions import NotFoundError
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService, get_audit_service
from app.services.cache_service import CacheService, get_cache_service


class UserService:
    """Service for user-related business logic."""

    def __init__(
        self,
        user_repo: UserRepository,
        cache_service: CacheService,
        audit_service: AuditService,
    ) -> None:
        self.user_repo = user_repo
        self.cache_service = cache_service
        self.audit_service = audit_service

    async def get_user(self, user_id: UUID) -> UserOut:
        """Get a user by ID."""
        try:
            user_in_db = await self.user_repo.get_by_id(user_id)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id '{user_id}' not found",
            )
        return UserOut.model_validate(user_in_db)

    async def update_role(
        self,
        actor: UserModel,
        target_uid: UUID,
        new_role: str,
    ) -> UserOut:
        """
        Update a user's role.

        Business rules:
        - Only admins can update roles (enforced at router via permission)
        - Sole admin cannot demote themselves (check)
        - Audit log is created
        - /me cache is invalidated for affected user
        """
        # Fetch target user
        try:
            target_user = await self.user_repo.get_by_id(target_uid)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id '{target_uid}' not found",
            )
        old_role = target_user.role

        # If role unchanged, no action needed (but still could audit? We'll skip)
        if new_role == old_role:
            return UserOut.model_validate(target_user)

        # Prevent sole admin demotion
        if old_role == "admin":
            other_admins = await self.user_repo.count_admins(exclude_user_id=target_uid)
            if other_admins == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot demote the sole administrator; assign another admin first",
                )

        # Perform role update
        try:
            updated_user_in_db = await self.user_repo.update_role(
                target_uid, UserUpdate(role=new_role)
            )
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id '{target_uid}' not found",
            )

        # Audit log
        await self.audit_service.log_role_change(
            actor_id=actor.id,
            target_user_id=target_user.id,
            old_role=old_role,
            new_role=new_role,
        )

        # Invalidate /me cache for affected user(s)
        await self.cache_service.invalidate_user_me()

        return UserOut.model_validate(updated_user_in_db)


# Dependency provider
async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
    cache_service: CacheService = Depends(get_cache_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> UserService:
    """FastAPI dependency for UserService."""
    return UserService(
        user_repo=user_repo,
        cache_service=cache_service,
        audit_service=audit_service,
    )
