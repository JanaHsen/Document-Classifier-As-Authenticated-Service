"""User Repository.

Handles all database operations for users.
No business logic, no HTTP exceptions, no cache invalidation.
"""

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.domain.user import UserInDB, UserUpdate
from app.exceptions import NotFoundError, AlreadyExistsError


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> UserInDB:
        """Get a single user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError(entity="User", identifier=str(user_id))
        return UserInDB.model_validate(user)

    async def get_by_email(self, email: str) -> UserInDB:
        """Get a single user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError(entity="User", identifier=email)
        return UserInDB.model_validate(user)

    async def update_role(self, user_id: int, data: UserUpdate) -> UserInDB:
        """Update a user's role."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(role=data.role)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        if result.rowcount == 0:
            raise NotFoundError(entity="User", identifier=str(user_id))
        await self.session.flush()
        return await self.get_by_id(user_id)

    async def count_admins(self, exclude_user_id: int | None = None) -> int:
        """Count how many users have the admin role."""
        from app.core.constants import Role

        stmt = select(func.count()).select_from(User).where(User.role == Role.ADMIN)
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

