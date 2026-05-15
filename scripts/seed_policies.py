"""
Seed the Casbin policy table with the three-role permission matrix.

Run this once before the api boots for the first time. The api's
startup check (app.auth.casbin.assert_policies_seeded, wired into
main.py's lifespan in a later file) refuses to start if the policy
table is empty.

Usage (from the project root):
    python scripts/seed_policies.py

Idempotent: running twice does not create duplicates. Casbin's
add_policy returns False (no-op) for an already-existing policy.

Permission matrix (derived from Trello cards 3, 4, 5, 6, 7):

| resource    | action  | admin | reviewer | auditor |
| ----------- | ------- | ----- | -------- | ------- |
| batches     | read    |   x   |    x     |    x    |
| batches     | create  |   x   |          |         |
| predictions | read    |   x   |    x     |    x    |
| predictions | relabel |       |    x     |         |
| audit_log   | read    |   x   |          |    x    |
| users.role  | toggle  |   x   |          |         |

The confidence < 0.7 gate on relabel is NOT enforced here. Casbin
only knows "may reviewers relabel predictions?" — yes. The service
layer (Tarek's PredictionService) decides whether THIS specific
prediction qualifies for relabeling.

If you change the matrix:
  1. Update the POLICIES list below.
  2. Update the table in this docstring.
  3. Confirm the corresponding router uses require_permission with
     the matching (resource, action) tuple.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so we can import app.*.
# This lets the script run regardless of the current working
# directory (e.g., `python scripts/seed_policies.py` from anywhere
# inside the repo).
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.auth.casbin import get_enforcer  # noqa: E402  (import after sys.path manipulation)


# Source of truth for the role → (resource, action) matrix. Each tuple
# becomes one row in the Casbin policy table.
POLICIES = [
    # batches:read — everyone reads batches
    ("admin", "batches", "read"),
    ("reviewer", "batches", "read"),
    ("auditor", "batches", "read"),

    # batches:create — admin only. HTTP document upload
    # (POST /batches/upload) is an operational action; least
    # privilege keeps reviewer/auditor read-only. SFTP ingest is
    # unauthenticated machine-to-machine and bypasses Casbin.
    ("admin", "batches", "create"),

    # predictions:read — everyone reads predictions
    ("admin", "predictions", "read"),
    ("reviewer", "predictions", "read"),
    ("auditor", "predictions", "read"),

    # predictions:relabel — reviewer only.
    # Confidence < 0.7 gate is service-layer, not Casbin. Casbin
    # answers "may reviewers relabel?"; the service answers "may
    # THIS prediction be relabeled (confidence threshold)?".
    ("reviewer", "predictions", "relabel"),

    # audit_log:read — admin and auditor only.
    # Reviewers deliberately cannot read the audit log; they should
    # not see records of their own past relabels in this UI.
    ("admin", "audit_log", "read"),
    ("auditor", "audit_log", "read"),

    # users.role:toggle — admin only.
    # The sole-admin self-demotion check is service-layer logic —
    # Casbin only knows the role can toggle, not who is toggling
    # whom.
    ("admin", "users.role", "toggle"),
]


def seed() -> None:
    """
    Insert each policy if not already present; save at the end.

    add_policy returns True if a new row was added, False if the
    policy already existed. We call save_policy once at the end so
    the SQLAlchemy adapter persists all new rows in a single round
    of writes.

    This function does NOT delete policies present in the DB but
    absent from POLICIES. Accidental removal during a seed run would
    be hard to recover from. To remove a policy, use the role-toggle
    endpoint (for grant/revoke at runtime) or a dedicated migration.
    """
    enforcer = get_enforcer()

    added = 0
    skipped = 0
    for role, resource, action in POLICIES:
        if enforcer.add_policy(role, resource, action):
            added += 1
        else:
            skipped += 1

    enforcer.save_policy()

    print(
        f"Seeded Casbin policies: "
        f"added={added}, already_present={skipped}, total={len(POLICIES)}"
    )


if __name__ == "__main__":
    seed()
