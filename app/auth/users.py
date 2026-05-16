
import contextlib
from typing import AsyncGenerator, Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users import exceptions, schemas as fa_schemas
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role
from app.core.security import get_jwt_secret
from app.db.models import User
from app.db.session import get_async_session


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):

    def __init__(self, user_db: SQLAlchemyUserDatabase):
        super().__init__(user_db)
        
        secret = get_jwt_secret()
        self.reset_password_token_secret = secret
        self.verification_token_secret = secret

    async def create(
        self,
        user_create: fa_schemas.UC,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> User:
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise exceptions.UserAlreadyExists()

        user_dict = (
            user_create.create_update_dict()
            if safe
            else user_create.create_update_dict_superuser()
        )
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)
        user_dict["role"] = Role.AUDITOR  # forced server-side; admin promotes to reviewer/admin

        created_user = await self.user_db.create(user_dict)
        await self.on_after_register(created_user, request)
        return created_user
    

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
    ) -> None:
        
        pass


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
  
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    
    yield UserManager(user_db)
