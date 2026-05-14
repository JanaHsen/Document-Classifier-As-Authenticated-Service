from fastapi import APIRouter

from app.api.deps.auth import fastapi_users
from app.api.schemas.user import UserCreate, UserRead
from app.auth.jwt import auth_backend


router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["auth"],
)
