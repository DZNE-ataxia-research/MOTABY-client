"""Tests for pagination helpers."""
from motaby.pagination import PaginatedResponse, PaginationMeta
from motaby.models import Patient


def _patient(pid: str) -> Patient:
    return Patient(patient_id=pid, assessment_count=1, latest_assessment_at=None)


def test_iter():
    meta = PaginationMeta(total=2, page=1, page_size=50, total_pages=1)
    resp = PaginatedResponse([_patient("P001"), _patient("P002")], meta)
    assert list(resp)[0].patient_id == "P001"


def test_len():
    meta = PaginationMeta(total=1, page=1, page_size=50, total_pages=1)
    assert len(PaginatedResponse([_patient("P001")], meta)) == 1


def test_from_dict():
    meta = PaginationMeta.from_dict({"total": 100, "page": 2, "page_size": 25, "total_pages": 4})
    assert meta.total_pages == 4
