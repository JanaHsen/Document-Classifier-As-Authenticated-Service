"""Custom exceptions for the application.

Repository layer raises only these non-HTTP exceptions.
Service layer catches and translates them to appropriate HTTP errors.
"""


class RepositoryError(Exception):
    """Base exception for repository errors."""

    def __init__(self, message: str = "Repository operation failed") -> None:
        super().__init__(message)


class NotFoundError(RepositoryError):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity: str = "Entity", identifier: str | None = None) -> None:
        if identifier:
            message = f"{entity} with identifier '{identifier}' not found"
        else:
            message = f"{entity} not found"
        super().__init__(message)
        self.entity = entity
        self.identifier = identifier


class AlreadyExistsError(RepositoryError):
    """Raised when attempting to create an entity that already exists."""

    def __init__(self, entity: str = "Entity", identifier: str | None = None) -> None:
        if identifier:
            message = f"{entity} with identifier '{identifier}' already exists"
        else:
            message = f"{entity} already exists"
        super().__init__(message)
        self.entity = entity
        self.identifier = identifier


class DatabaseError(RepositoryError):
    """Raised when a database operation fails at the low level."""

    def __init__(self, message: str = "Database operation failed") -> None:
        super().__init__(message)
