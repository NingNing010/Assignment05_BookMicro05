"""
Base exceptions for the product-service.
"""


class DomainError(Exception):
    """Raised when a domain invariant is violated."""
    pass


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""
    pass


class ValidationError(DomainError):
    """Raised when entity validation fails."""
    pass
