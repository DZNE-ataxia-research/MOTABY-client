"""Tests for BatteriesEndpoint."""
import uuid
from unittest.mock import MagicMock

from motaby.endpoints.batteries import BatteriesEndpoint
from motaby.models import Battery

SAMPLE = {
    "id": str(uuid.uuid4()),
    "name": "Standard Battery",
    "description": "A standard set of motor assessments",
    "color": "#007AFF",
    "active": True,
    "created_at": "2025-01-15T10:00:00",
}

LIST_RESPONSE = {
    "batteries": [SAMPLE],
    "pagination": {"total": 1, "page": 1, "page_size": 50, "total_pages": 1},
}


def test_list_returns_batteries():
    http = MagicMock()
    http.get.return_value = LIST_RESPONSE
    endpoint = BatteriesEndpoint(http)
    result = endpoint.list()
    assert len(result.items) == 1
    assert result.items[0].name == "Standard Battery"
    assert result.pagination.total == 1


def test_list_passes_pagination_params():
    http = MagicMock()
    http.get.return_value = LIST_RESPONSE
    endpoint = BatteriesEndpoint(http)
    endpoint.list(page=2, page_size=25)
    params = http.get.call_args[1]["params"]
    assert params["page"] == 2
    assert params["page_size"] == 25


def test_list_all_auto_paginates():
    http = MagicMock()
    page1 = {
        "batteries": [SAMPLE],
        "pagination": {"total": 2, "page": 1, "page_size": 1, "total_pages": 2},
    }
    page2 = {
        "batteries": [dict(SAMPLE, id=str(uuid.uuid4()), name="Extra Battery")],
        "pagination": {"total": 2, "page": 2, "page_size": 1, "total_pages": 2},
    }
    http.get.side_effect = [page1, page2]
    endpoint = BatteriesEndpoint(http)
    all_items = endpoint.list_all()
    assert len(all_items) == 2
    assert http.get.call_count == 2


def test_battery_from_dict_handles_optional_fields():
    data = {"id": str(uuid.uuid4()), "name": "Minimal", "active": False, "created_at": None}
    b = Battery.from_dict(data)
    assert b.description is None
    assert b.color is None
    assert b.active is False
    assert b.created_at is None
