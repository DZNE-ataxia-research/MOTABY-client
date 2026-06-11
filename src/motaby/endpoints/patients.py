"""Patients endpoint."""
from __future__ import annotations

from typing import Any, List, TYPE_CHECKING

from motaby._http import HTTPClient
from motaby.models import Patient
from motaby.pagination import PaginatedResponse, PaginationMeta

if TYPE_CHECKING:
    import pandas as pd


class PatientsEndpoint:
    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(self, page: int = 1, page_size: int = 50) -> PaginatedResponse[Patient]:
        data = self._http.get("/api/v1/export/patients", params={"page": page, "page_size": page_size})
        items = [Patient.from_dict(p) for p in data["patients"]]
        pagination = PaginationMeta.from_dict(data["pagination"])
        return PaginatedResponse(items, pagination)

    def list_all(self) -> List[Patient]:
        results: List[Patient] = []
        page = 1
        while True:
            page_data = self.list(page=page, page_size=200)
            results.extend(page_data.items)
            if page >= page_data.pagination.total_pages:
                break
            page += 1
        return results

    def to_dataframe(self) -> "pd.DataFrame":
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError("pandas required: pip install motaby-client[pandas]") from e
        return pd.DataFrame([p.to_dict() for p in self.list_all()])
