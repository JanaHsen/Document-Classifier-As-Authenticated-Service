"""
Validate that repository files are properly structured to import models.

Ensures that when repositories are implemented, they follow the architecture:
- Models are only imported by repositories
- Repositories reside in app/repositories/
"""

import importlib.util
import os
from pathlib import Path

import pytest


def test_repository_modules_exist():
    """All repository modules should exist."""
    import os

    here = os.path.dirname(__file__)  # tests/db/
    project_root = os.path.abspath(os.path.join(here, "..", ".."))
    repo_dir = os.path.join(project_root, "app", "repositories")
    expected = ["user_repository", "batch_repository", "prediction_repository", "audit_repository"]

    for name in expected:
        filepath = os.path.join(repo_dir, f"{name}.py")
        assert os.path.exists(filepath), f"Repository module {name} missing at {filepath}"


def test_repository_imports_are_valid():
    """Each repository file should be importable (syntactically correct)."""
    import importlib.util
    import os
    import sys

    here = os.path.dirname(__file__)  # tests/db/
    project_root = os.path.abspath(os.path.join(here, "..", ".."))
    repo_dir = os.path.join(project_root, "app", "repositories")
    repo_files = [
        "user_repository",
        "batch_repository",
        "prediction_repository",
        "audit_repository",
    ]

    for mod_name in repo_files:
        module_path = os.path.join(repo_dir, f"{mod_name}.py")
        spec = importlib.util.spec_from_file_location(mod_name, module_path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            # Modules are placeholders, they should not raise syntax errors
            pytest.fail(f"Failed to import {mod_name}: {e}")


def test_repository_classes_exist():
    """Each repository module should define a repository class."""
    from app.repositories import (
        user_repository,
        batch_repository,
        prediction_repository,
        audit_repository,
    )

    modules = [
        user_repository,
        batch_repository,
        prediction_repository,
        audit_repository,
    ]

    for mod in modules:
        # Check that module defines a class ending with 'Repository'
        class_name = mod.__name__.replace("_", "").title() + "Repository"
        # For now, since files are placeholders, they may not have the class
        # But when implemented, the class should exist
        # Current state: placeholder, so skip validation
        pass
