
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from app.auth.users import UserManager, get_user_manager
from app.core.security import (
    JWT_ALGORITHM,
    JWT_LIFETIME_SECONDS,
    get_jwt_secret,
)
from app.db.models import User

bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    
    return JWTStrategy(
        secret=get_jwt_secret(),
        lifetime_seconds=JWT_LIFETIME_SECONDS,
        algorithm=JWT_ALGORITHM,
    )

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
