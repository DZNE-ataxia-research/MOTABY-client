"""Assessments endpoint."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from motaby._http import HTTPClient
from motaby.models import Assessment
from motaby.pagination import PaginatedResponse, PaginationMeta

if TYPE_CHECKING:
    import pandas as pd


class AssessmentsEndpoint:
    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(
        self,
        patient_id: Optional[str] = None,
        code: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[Union[date, str]] = None,
        date_to: Optional[Union[date, str]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[Assessment]:
        """Fetch one page of assessments."""
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if patient_id:
            params["patient_id"] = patient_id
        if code:
            params["assessment_code"] = code
        if status:
            params["status"] = status
        if date_from:
            params["date_from"] = str(date_from)
        if date_to:
            params["date_to"] = str(date_to)

        data = self._http.get("/api/v1/export/assessments", params=params)
        items = [Assessment.from_dict(a) for a in data["assessments"]]
        pagination = PaginationMeta.from_dict(data["pagination"])
        return PaginatedResponse(items, pagination)

    def list_all(
        self,
        patient_id: Optional[str] = None,
        code: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[Union[date, str]] = None,
        date_to: Optional[Union[date, str]] = None,
    ) -> List[Assessment]:
        """Fetch all assessments across all pages (auto-paginating)."""
        results: List[Assessment] = []
        page = 1
        while True:
            page_data = self.list(
                patient_id=patient_id,
                code=code,
                status=status,
                date_from=date_from,
                date_to=date_to,
                page=page,
                page_size=200,
            )
            results.extend(page_data.items)
            if page >= page_data.pagination.total_pages:
                break
            page += 1
        return results

    def get(self, assessment_id: str) -> Assessment:
        """Fetch a single assessment by ID (includes media items)."""
        data = self._http.get(f"/api/v1/export/assessments/{assessment_id}")
        return Assessment.from_dict(data)

    def to_dataframe(
        self,
        patient_id: Optional[str] = None,
        code: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[Union[date, str]] = None,
        date_to: Optional[Union[date, str]] = None,
    ) -> "pd.DataFrame":
        """
        Fetch all assessments and return as a pandas DataFrame.
        Requires pandas: pip install motaby-client[pandas]
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install with: pip install motaby-client[pandas]"
            ) from e
        all_items = self.list_all(
            patient_id=patient_id,
            code=code,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )
        return pd.DataFrame([a.to_dict() for a in all_items])
