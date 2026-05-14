"""
Audit log routes.

One endpoint:
  GET /audit-log — list audit entries (admin + auditor only)

Reviewers do NOT have audit_log:read in the seeded policy table —
only admin and auditor do. Reviewers receive 403 here.

Optional query parameters:
  - actor:  filter entries to those by a single actor (UUID)
  - action: filter entries to those with a specific action string
Both are passed through to AuditService.list_entries. They can be
combined; passing both means the entry must match both (AND).

Thin router pattern:
  - Validate input (FastAPI on the query parameters).
  - Run the auth chain (declared in dependencies=[]).
  - Call ONE service method and return its result.
  - No DB, no cache. This endpoint reads the audit log; it does
    not itself write to it (auditing the act of reading the audit
    log would loop endlessly and add no value).

dependencies=[...] form is used because the handler does not need
the user object — only the role gate matters here.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps.permissions import require_permission
from app.api.schemas.audit import AuditLogEntry
from app.services.audit_service import AuditService, get_audit_service


router = APIRouter()


@router.get(
    "",
    response_model=list[AuditLogEntry],
    summary="List audit log entries (admin and auditor only)",
    dependencies=[Depends(require_permission("audit_log", "read"))],
)
async def list_audit_entries(
    actor: Optional[int] = Query(
        None,
        description="Filter to entries created by this actor user id.",
    ),
    action: Optional[str] = Query(
        None,
        description=(
            "Filter to entries with this exact action string "
            "(e.g., 'change_role', 'relabel_pred', 'change_state')."
        ),
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    GET /audit-log — return audit log entries, optionally filtered.

    Auth chain (resolved before this body runs):
      1. current_active_user — 401 if JWT is missing or invalid.
      2. require_permission("audit_log", "read") — 403 if the
         caller's role lacks the policy. Admin and auditor pass;
         reviewer does not.

    When both filter parameters are None (the default), every entry
    is returned. When one or both are provided, the service applies
    them as AND filters.
    """
    return await audit_service.list_entries(actor=actor, action=action)
