"""Pagination helpers for MOTABY client responses."""
from __future__ import annotations

from typing import Generic, Iterator, List, Optional, Type, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

T = TypeVar("T")


class PaginationMeta:
    def __init__(self, total: int, page: int, page_size: int, total_pages: int) -> None:
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = total_pages

    @classmethod
    def from_dict(cls, data: dict) -> "PaginationMeta":
        return cls(
            total=data["total"],
            page=data["page"],
            page_size=data["page_size"],
            total_pages=data["total_pages"],
        )


class PaginatedResponse(Generic[T]):
    """A single page of results with pagination metadata."""

    def __init__(self, items: List[T], pagination: PaginationMeta) -> None:
        self.items = items
        self.pagination = pagination

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def to_dataframe(self) -> "pd.DataFrame":
        """Convert items to a pandas DataFrame. Requires pandas to be installed."""
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install with: pip install motaby-client[pandas]"
            ) from e
        return pd.DataFrame([item.to_dict() for item in self.items])
