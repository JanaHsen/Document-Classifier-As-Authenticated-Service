import uuid
from typing import AsyncGenerator, Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_jwt_secret
from app.db.models import User
from app.db.session import get_async_session


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):

    def __init__(self, user_db: SQLAlchemyUserDatabase):
        super().__init__(user_db)
        # Reset and verification tokens use the same JWT secret. We
        # could split them into separate secrets later if we ever want
        # to rotate one without affecting the other.
        secret = get_jwt_secret()
        self.reset_password_token_secret = secret
        self.verification_token_secret = secret

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
    ) -> None:
        """
        Lifecycle hook called after a user successfully registers.

        Currently a no-op placeholder. Tarek's AuditService will hook
        in here to record "user {email} registered with role {role}"
        once that service exists.

        Why we do NOT force user.role = 'reviewer' here:
          1. The UserCreate schema (app/api/schemas/user.py) omits
             the 'role' field, so clients cannot send a role on
             register. Self-promotion attack is already blocked at
             the API boundary.
          2. The SQLAlchemy User column default ('reviewer') applies
             when no role is otherwise specified.
          3. A future admin-invite flow may legitimately want to
             create a user with a non-default role. Forcing the role
             here would silently break that path.

        Defense in depth without redundancy: the two earlier layers
        handle the threat; this hook stays available for audit logging
        rather than re-doing their job.
        """
        pass


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    """
    Yields the SQLAlchemy-backed User database adapter for this
    request. The adapter wraps the request's session and the User
    ORM class — fastapi-users uses it to read and write user rows.
    """
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    """
    Yields a UserManager instance bound to this request's user_db.

    app/auth/jwt.py declares this as a dependency when constructing
    the FastAPIUsers instance, which is what mounts the auth routes
    (POST /auth/register, /auth/jwt/login, /auth/jwt/logout) onto
    the FastAPI app.
    """
    yield UserManager(user_db)
