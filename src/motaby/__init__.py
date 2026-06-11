"""motaby-client: Python client for the MOTABY assessment platform."""
import importlib.metadata

try:
    __version__ = importlib.metadata.version("motaby-client")
except importlib.metadata.PackageNotFoundError:
    __version__ = "dev"

from motaby.client import MOTABYClient
from motaby.exceptions import (
    MOTABYError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from motaby.models import Assessment, Battery, MediaItem, Patient

__all__ = [
    "MOTABYClient",
    "MOTABYError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    "Assessment",
    "Battery",
    "MediaItem",
    "Patient",
]
