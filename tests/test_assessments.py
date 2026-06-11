"""Tests for AssessmentsEndpoint."""
import uuid
from unittest.mock import MagicMock

from motaby.endpoints.assessments import AssessmentsEndpoint
from motaby.models import Assessment

SAMPLE = {
    "id": str(uuid.uuid4()),
    "patient_id": "P001",
    "assessment_code": "spiral-drawing",
    "assessment_type": "drawing",
    "status": "final",
    "data": {"drawing_data": {}},
    "configuration": {"hand": "right"},
    "effective_datetime": None,
    "created_at": "2025-01-15T10:30:00",
    "notes": None,
    "media_count": 0,
    "media_items": [],
}

LIST_RESPONSE = {
    "assessments": [SAMPLE],
    "pagination": {"total": 1, "page": 1, "page_size": 50, "total_pages": 1},
}


def test_list_returns_assessments():
    http = MagicMock()
    http.get.return_value = LIST_RESPONSE
    endpoint = AssessmentsEndpoint(http)
    result = endpoint.list(patient_id="P001")
    assert len(result.items) == 1
    assert result.items[0].patient_id == "P001"
    assert result.pagination.total == 1


def test_list_passes_filters():
    http = MagicMock()
    http.get.return_value = LIST_RESPONSE
    endpoint = AssessmentsEndpoint(http)
    endpoint.list(patient_id="P001", code="spiral-drawing", page=2, page_size=10)
    params = http.get.call_args[1]["params"]
    assert params["patient_id"] == "P001"
    assert params["assessment_code"] == "spiral-drawing"
    assert params["page"] == 2


def test_get_returns_assessment():
    http = MagicMock()
    http.get.return_value = SAMPLE
    endpoint = AssessmentsEndpoint(http)
    a = endpoint.get(SAMPLE["id"])
    assert isinstance(a, Assessment)
    assert a.assessment_code == "spiral-drawing"


def test_list_all_auto_paginates():
    http = MagicMock()
    page1 = {"assessments": [SAMPLE], "pagination": {"total": 2, "page": 1, "page_size": 1, "total_pages": 2}}
    page2 = {"assessments": [dict(SAMPLE, id=str(uuid.uuid4()))], "pagination": {"total": 2, "page": 2, "page_size": 1, "total_pages": 2}}
    http.get.side_effect = [page1, page2]
    endpoint = AssessmentsEndpoint(http)
    all_items = endpoint.list_all()
    assert len(all_items) == 2
    assert http.get.call_count == 2
