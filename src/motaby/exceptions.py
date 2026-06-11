"""Typed exceptions for motaby-client."""


class MOTABYError(Exception):
    """Base exception for all motaby-client errors."""


class AuthenticationError(MOTABYError):
    """Raised on 401: invalid or expired API key."""


class AuthorizationError(MOTABYError):
    """Raised on 403: insufficient permissions."""


class NotFoundError(MOTABYError):
    """Raised on 404: resource not found."""


class RateLimitError(MOTABYError):
    """Raised on 429: rate limit exceeded."""

    def __init__(self, message: str, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ServerError(MOTABYError):
    """Raised on 5xx: server-side error."""


class ValidationError(MOTABYError):
    """Raised on 422: request validation error."""
