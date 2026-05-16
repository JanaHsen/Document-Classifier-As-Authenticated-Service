import os
from functools import lru_cache

JWT_ALGORITHM = "HS256"
JWT_LIFETIME_SECONDS = 3600  # 1 hour


@lru_cache(maxsize=1)
def get_jwt_secret() -> str:
   
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "JWT signing secret not resolved. "
            "Dev: set the JWT_SECRET env var. "
            "Prod: ensure Vault is reachable and 'kv/auth/jwt_secret' exists."
        )
    return secret
