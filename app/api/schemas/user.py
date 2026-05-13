from enum import Enum
from uuid import UUID

from fastapi_users import schemas

class Role(str, Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"

class UserRead(schemas.BaseUser[UUID]):
    role: Role

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass
