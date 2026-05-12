"""
Test that SQLAlchemy models are imported ONLY in app/repositories/ as per task1.md.

task1.md requirement: "Models live only in app/db/models.py, imported only by repositories"
"""

import os
import pathlib


# Directories that are ALLOWED to import from app.db.models
ALLOWED_IMPORT_PATHS = [
    "app/repositories/",
    "app/db/",
    "tests/",
    "scripts/",
]

# Directories that are FORBIDDEN from importing models
FORBIDDEN_IMPORT_PATHS = [
    "app/services/",
    "app/api/",
    "app/workers/",
    "app/classifier/",
    "app/auth/",
    "app/infra/",
    "app/domain/",
    "app/core/",
]


def test_models_imported_only_in_repositories():
    """Verify no file outside allowed paths imports from app.db.models."""
    project_root = pathlib.Path(__file__).parent.parent
    models_import = "from app.db.models import"
    models_import_alt = "from app.db import models"

    violations = []

    for dirpath, dirnames, filenames in os.walk(project_root / "app"):
        dirname = os.path.relpath(dirpath, project_root)

        # Skip __pycache__
        if "__pycache__" in dirname:
            continue

        # Check if this directory is forbidden
        is_forbidden = any(
            dirname.startswith(fb) or dirname == fb.rstrip("/")
            for fb in FORBIDDEN_IMPORT_PATHS
        )

        if not is_forbidden:
            continue  # Only scan forbidden directories

        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    content = f.read()
                except UnicodeDecodeError:
                    continue

            if models_import in content or models_import_alt in content:
                rel_path = os.path.relpath(filepath, project_root)
                violations.append(rel_path)

    assert not violations, (
        f"Models imported in forbidden locations. Files:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_repo_files_are_placeholders():
    """Repositories should currently be placeholders (no implementation yet)."""
    import os

    # Path: go up from tests/ to project root, then into app/repositories
    here = os.path.dirname(__file__)  # tests/
    project_root = os.path.abspath(os.path.join(here, ".."))
    repo_dir = os.path.join(project_root, "app", "repositories")

    for filename in os.listdir(repo_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            filepath = os.path.join(repo_dir, filename)
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
            # Placeholder files contain only ownership comment
            stripped = content.strip()
            assert stripped.startswith("#") or stripped == "", \
                f"Repository {filename} should be placeholder but contains code"


def test_service_files_are_placeholders():
    """Services should currently be placeholders (no implementation yet)."""
    import os

    here = os.path.dirname(__file__)  # tests/
    project_root = os.path.abspath(os.path.join(here, ".."))
    service_dir = os.path.join(project_root, "app", "services")

    for filename in os.listdir(service_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            filepath = os.path.join(service_dir, filename)
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
            stripped = content.strip()
            assert stripped.startswith("#") or stripped == "", \
                f"Service {filename} should be placeholder but contains code"
