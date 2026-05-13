from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps.permissions import require_permission
from app.api.schemas.auth import RoleToggleRequest
from app.api.schemas.user import UserRead
from app.db.models import User
from app.services.user_service import UserService, get_user_service


router = APIRouter()


@router.patch(
    "/{uid}/role",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Change a user's role (admin only)",
    description=(
        "Change the target user's role. Admin-only via Casbin "
        "policy users.role:toggle. The Casbin policy table is "
        "updated immediately, so the affected user's NEXT request "
        "reflects the new permissions without requiring a logout. "
        "Self-demotion by the sole admin returns 400."
    ),
)
async def update_user_role(
    uid: UUID,
    body: RoleToggleRequest,
    actor: User = Depends(require_permission("users.role", "toggle")),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """
    PATCH /users/{uid}/role — change a user's role.

    The auth chain (resolved by FastAPI before this body runs):
      1. current_active_user — extracts and validates the JWT.
         Returns 401 if missing, expired, or malformed.
      2. require_permission("users.role", "toggle") — Casbin check.
         Returns 403 if the caller's role lacks the policy.

    By the time we enter the body, the caller is an authenticated
    admin (per the seeded policy table, only the 'admin' role has
    users.role:toggle). All remaining business rules — including
    the sole-admin self-demotion check, the DB update, the Casbin
    policy mutation, and the audit log entry — live in
    UserService.update_role.

    body.role is a Role enum (Pydantic guarantees it's one of the
    three valid values); we pass .value to the service so it
    receives the plain string.

    Returns the updated User; FastAPI serializes it through
    response_model=UserRead, which excludes hashed_password and
    other sensitive fields.
    """
    return await user_service.update_role(
        actor=actor,
        target_uid=uid,
        new_role=body.role.value,
    )
