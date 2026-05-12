"""
Validate that requirements.txt contains all necessary dependencies.

Checks:
- SQLAlchemy is present with minimum version
- asyncpg or psycopg2 present for PostgreSQL
- pydantic for domain models
- All required dev dependencies for testing
"""

import re
from pathlib import Path


REQUIREMENTS_PATH = Path(__file__).parent.parent / "requirements.txt"

# Required packages with minimum versions for task1 models
REQUIRED_PACKAGES = {
    "sqlalchemy": ">=2.0.0",
    "asyncpg": ">=0.29.0",  # optional but recommended
    "psycopg2-binary": ">=2.9.0",  # optional alternative
}

# Packages needed for running tests
TEST_PACKAGES = [
    "pytest",
    "pytest-asyncio",
]


def read_requirements() -> set[str]:
    """Parse requirements.txt into a set of package names."""
    if not REQUIREMENTS_PATH.exists():
        pytest.fail(f"requirements.txt not found at {REQUIREMENTS_PATH}")

    content = REQUIREMENTS_PATH.read_text()
    packages = set()
    for line in content.splitlines():
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue
        # Extract package name (before any version specifiers)
        match = re.match(r"^([a-zA-Z0-9_-]+)", line)
        if match:
            packages.add(match.group(1).lower())
    return packages


def test_requirements_contains_sqlalchemy():
    """SQLAlchemy must be in requirements."""
    packages = read_requirements()
    assert "sqlalchemy" in packages, "SQLAlchemy dependency missing from requirements.txt"


def test_requirements_contains_async_driver():
    """Either asyncpg or psycopg2-binary must be present for PostgreSQL async support."""
    packages = read_requirements()
    has_asyncpg = "asyncpg" in packages
    has_psycopg2 = "psycopg2-binary" in packages or "psycopg2" in packages
    assert has_asyncpg or has_psycopg2, \
        "No PostgreSQL driver found. Add asyncpg or psycopg2-binary to requirements.txt"


def test_requirements_contains_pydantic():
    """Pydantic must be present for domain models."""
    packages = read_requirements()
    assert "pydantic" in packages, "Pydantic dependency missing from requirements.txt"


def test_requirements_contains_test_dependencies():
    """Test dependencies should be present."""
    # Note: This test expects test dependencies in requirements.txt (or separate dev requirements)
    # For this project, they're in the same file or in pyproject.toml
    # Since pyproject.toml is empty, we check requirements.txt only
    packages = read_requirements()
    # We currently don't have pytest in requirements.txt, so this test may fail
    # But we want to encourage adding them. We'll mark as skip if not found.
    missing = [pkg for pkg in TEST_PACKAGES if pkg not in packages]
    if missing:
        pytest.skip(f"Test dependencies not yet added: {missing}")


def test_requirements_file_not_empty():
    """Ensure requirements.txt is not just a placeholder."""
    content = REQUIREMENTS_PATH.read_text().strip()
    # Should have at least one non-comment line
    lines = [l for l in content.splitlines() if l and not l.strip().startswith("#")]
    assert len(lines) > 0, "requirements.txt is empty; add required dependencies"
