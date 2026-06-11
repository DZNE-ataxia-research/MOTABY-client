"""Tests for MOTABYClient initialization."""
import pytest
from motaby import MOTABYClient


def test_valid_construction():
    client = MOTABYClient(base_url="http://localhost:8000", api_key="mby_abc123")
    assert client is not None
    client.close()


def test_empty_base_url_raises():
    with pytest.raises(ValueError, match="base_url"):
        MOTABYClient(base_url="", api_key="mby_abc123")


def test_invalid_api_key_prefix_raises():
    with pytest.raises(ValueError, match="mby_"):
        MOTABYClient(base_url="http://localhost:8000", api_key="invalid_key")


def test_context_manager():
    with MOTABYClient(base_url="http://localhost:8000", api_key="mby_abc123") as client:
        assert client is not None
