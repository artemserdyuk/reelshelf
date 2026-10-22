class DomainError(Exception):
    """Base class for expected business errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    """Raised when a requested entity is not found."""


class ConflictError(DomainError):
    """Raised when a conflict occurs, such as a duplicate entity."""


class UnauthorizedError(DomainError):
    """Raised when an action is attempted without proper authorization."""


class BusinessRuleError(DomainError):
    """Raised when a business rule is violated."""
