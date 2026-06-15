"""Internal HTTP client with retry logic and error mapping."""
from __future__ import annotations

import importlib.metadata
import time
from typing import Any, Dict, Optional

import httpx

from motaby.exceptions import (
    AuthenticationError,
    AuthorizationError,
    MOTABYError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

try:
    _VERSION = importlib.metadata.version("motaby-client")
except importlib.metadata.PackageNotFoundError:
    _VERSION = "dev"


class HTTPClient:
    """Low-level HTTP client wrapping httpx. Not intended for direct use."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        # Store the key only in the headers dict — not as a separate attribute
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "X-API-Key": api_key,
                "User-Agent": f"motaby-client/{_VERSION}",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform a GET request with retry logic."""
        attempt = 0
        last_exc: Optional[Exception] = None

        while attempt < self._max_retries:
            try:
                response = self._client.get(path, params=params)
                return self._handle_response(response)
            except RateLimitError as e:
                wait = e.retry_after
                if attempt < self._max_retries - 1:
                    time.sleep(min(wait, 60))
                    attempt += 1
                    last_exc = e
                    continue
                raise
            except (ServerError, MOTABYError) as e:
                if isinstance(e, ServerError) and attempt < self._max_retries - 1:
                    time.sleep(2 ** attempt)
                    attempt += 1
                    last_exc = e
                    continue
                raise
            except httpx.TransportError as e:
                if attempt < self._max_retries - 1:
                    time.sleep(2 ** attempt)
                    attempt += 1
                    last_exc = e
                    continue
                raise MOTABYError(f"Network error: {e}") from e

        raise MOTABYError(f"Request failed after {self._max_retries} attempts") from last_exc

    def get_binary(self, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """
        Perform a GET request with the same retry logic as get(), but return
        the raw Response instead of parsing JSON. Used for file downloads.
        Raises typed exceptions on auth/not-found errors; retries on 503/network errors.
        """
        attempt = 0
        last_exc: Optional[Exception] = None

        while attempt < self._max_retries:
            try:
                response = self._client.get(path, params=params)
                if response.status_code in (200, 201):
                    return response
                if response.status_code == 401:
                    raise AuthenticationError("Invalid or expired API key")
                if response.status_code == 403:
                    raise AuthorizationError("Access denied")
                if response.status_code == 404:
                    raise NotFoundError("Resource not found")
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "30"))
                    if attempt < self._max_retries - 1:
                        time.sleep(min(retry_after, 60))
                        attempt += 1
                        continue
                    raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
                if response.status_code >= 500:
                    exc = ServerError(f"Server error: {response.status_code}")
                    if attempt < self._max_retries - 1:
                        time.sleep(2 ** attempt)
                        attempt += 1
                        last_exc = exc
                        continue
                    raise exc
                raise MOTABYError(f"Unexpected status: {response.status_code}")
            except (AuthenticationError, AuthorizationError, NotFoundError, RateLimitError, MOTABYError):
                raise
            except httpx.TransportError as e:
                if attempt < self._max_retries - 1:
                    time.sleep(2 ** attempt)
                    attempt += 1
                    last_exc = e
                    continue
                raise MOTABYError(f"Network error: {e}") from e

        raise MOTABYError(f"Request failed after {self._max_retries} attempts") from last_exc

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Map HTTP status codes to typed exceptions."""
        if response.status_code == 200 or response.status_code == 201:
            try:
                return response.json()
            except Exception as e:
                raise MOTABYError(f"Invalid JSON in response: {e}") from e
        if response.status_code == 401:
            raise AuthenticationError("Invalid or expired API key")
        if response.status_code == 403:
            raise AuthorizationError("Access denied")
        if response.status_code == 404:
            raise NotFoundError("Resource not found")
        if response.status_code == 422:
            detail = response.json().get("detail", "Validation error")
            raise ValidationError(str(detail))
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
        if response.status_code >= 500:
            raise ServerError(f"Server error: {response.status_code}")
        raise MOTABYError(f"Unexpected status: {response.status_code}")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HTTPClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
