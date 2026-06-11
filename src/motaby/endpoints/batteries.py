"""Batteries endpoint."""
from __future__ import annotations

from typing import List, TYPE_CHECKING

from motaby._http import HTTPClient
from motaby.models import Battery
from motaby.pagination import PaginatedResponse, PaginationMeta

if TYPE_CHECKING:
    import pandas as pd


class BatteriesEndpoint:
    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(self, page: int = 1, page_size: int = 50) -> PaginatedResponse[Battery]:
        data = self._http.get("/api/v1/export/batteries", params={"page": page, "page_size": page_size})
        items = [Battery.from_dict(b) for b in data["batteries"]]
        pagination = PaginationMeta.from_dict(data["pagination"])
        return PaginatedResponse(items, pagination)

    def list_all(self) -> List[Battery]:
        results: List[Battery] = []
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
        return pd.DataFrame([b.to_dict() for b in self.list_all()])
