"""Tests for PatientsEndpoint."""
from unittest.mock import MagicMock

from motaby.endpoints.patients import PatientsEndpoint
from motaby.models import Patient

SAMPLE = {
    "patient_id": "P001",
    "assessment_count": 5,
    "latest_assessment_at": "2025-06-01T09:00:00",
}

LIST_RESPONSE = {
    "patients": [SAMPLE],
    "pagination": {"total": 1, "page": 1, "page_size": 50, "total_pages": 1},
}


def test_list_returns_patients():
    http = MagicMock()
    http.get.return_value = LIST_RESPONSE
    endpoint = PatientsEndpoint(http)
    result = endpoint.list()
    assert len(result.items) == 1
    assert result.items[0].patient_id == "P001"
    assert result.items[0].assessment_count == 5


def test_list_passes_pagination_params():
    http = MagicMock()
    http.get.return_value = LIST_RESPONSE
    endpoint = PatientsEndpoint(http)
    endpoint.list(page=3, page_size=10)
    params = http.get.call_args[1]["params"]
    assert params["page"] == 3
    assert params["page_size"] == 10


def test_list_all_auto_paginates():
    http = MagicMock()
    page1 = {
        "patients": [SAMPLE],
        "pagination": {"total": 2, "page": 1, "page_size": 1, "total_pages": 2},
    }
    page2 = {
        "patients": [{"patient_id": "P002", "assessment_count": 2, "latest_assessment_at": None}],
        "pagination": {"total": 2, "page": 2, "page_size": 1, "total_pages": 2},
    }
    http.get.side_effect = [page1, page2]
    endpoint = PatientsEndpoint(http)
    all_items = endpoint.list_all()
    assert len(all_items) == 2
    assert http.get.call_count == 2


def test_patient_from_dict_handles_null_latest_assessment():
    data = {"patient_id": "P999", "assessment_count": 0, "latest_assessment_at": None}
    p = Patient.from_dict(data)
    assert p.latest_assessment_at is None
