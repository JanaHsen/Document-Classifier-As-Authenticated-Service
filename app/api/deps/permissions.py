from fastapi import Depends, HTTPException, status

from app.api.deps.auth import current_active_user
from app.auth.casbin import get_enforcer
from app.db.models import User


def require_permission(resource: str, action: str):
    
    async def dependency(
        user: User = Depends(current_active_user),
    ) -> User:
        enforcer = get_enforcer()
        if not enforcer.enforce(user.role, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="forbidden",
            )
        return user

    return dependency
