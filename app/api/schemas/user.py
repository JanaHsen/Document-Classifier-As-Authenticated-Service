from fastapi_users import schemas
from app.core.constants import Role


class UserRead(schemas.BaseUser[int]):
    role: Role


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    role: Role | None = None
