"""
Data models returned by the MOTABY client.
These mirror the backend export API response schemas.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class ReadoutItem:
    name: str
    layer: str
    description: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "layer": self.layer,
            "description": self.description,
            "content_type": self.content_type,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReadoutItem":
        return cls(
            name=data["name"],
            layer=data.get("layer", ""),
            description=data.get("description"),
            content_type=data.get("content_type"),
            size=data.get("size"),
        )


@dataclass
class MediaItem:
    id: uuid.UUID
    media_type: str
    content_type: Optional[str]
    content_size: Optional[int]
    original_filename: Optional[str]
    duration: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "media_type": self.media_type,
            "content_type": self.content_type,
            "content_size": self.content_size,
            "original_filename": self.original_filename,
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MediaItem":
        return cls(
            id=uuid.UUID(data["id"]),
            media_type=data["media_type"],
            content_type=data.get("content_type"),
            content_size=data.get("content_size"),
            original_filename=data.get("original_filename"),
            duration=data.get("duration"),
        )


_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


def _parse_readouts(data: Dict[str, Any]) -> "List[ReadoutItem]":
    """
    Populate readouts from the server-provided 'readouts' key (detail endpoint)
    or fall back to parsing assessment.data['readout_urls'] (list endpoint).
    Excludes QC layer and video files — mirrors the server-side filter.
    """
    if "readouts" in data:
        return [ReadoutItem.from_dict(r) for r in data["readouts"]]
    raw = (data.get("data") or {}).get("readout_urls", [])
    result = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        if (r.get("layer") or "").upper() == "QC":
            continue
        name = r.get("name", "")
        if any(name.lower().endswith(ext) for ext in _VIDEO_EXTENSIONS):
            continue
        result.append(ReadoutItem(
            name=name,
            layer=r.get("layer", ""),
            description=r.get("description"),
            content_type=r.get("content_type"),
            size=r.get("size"),
        ))
    return result


@dataclass
class Assessment:
    id: uuid.UUID
    patient_id: str
    assessment_code: str
    assessment_type: Optional[str]
    status: Optional[str]
    data: Optional[Dict[str, Any]]
    configuration: Optional[Dict[str, Any]]
    effective_datetime: Optional[datetime]
    created_at: Optional[datetime]
    notes: Optional[str]
    study: Optional[str]
    media_count: int
    media_items: List[MediaItem] = field(default_factory=list)
    readouts: List[ReadoutItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "patient_id": self.patient_id,
            "assessment_code": self.assessment_code,
            "assessment_type": self.assessment_type,
            "status": self.status,
            "data": self.data,
            "configuration": self.configuration,
            "effective_datetime": self.effective_datetime.isoformat() if self.effective_datetime else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "notes": self.notes,
            "study": self.study,
            "media_count": self.media_count,
            "media_items": [m.to_dict() for m in self.media_items],
            "readouts": [r.to_dict() for r in self.readouts],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Assessment":
        def _parse_dt(val: Optional[str]) -> Optional[datetime]:
            if not val:
                return None
            return datetime.fromisoformat(val.replace("Z", "+00:00"))

        return cls(
            id=uuid.UUID(data["id"]),
            patient_id=data["patient_id"],
            assessment_code=data["assessment_code"],
            assessment_type=data.get("assessment_type"),
            status=data.get("status"),
            data=data.get("data"),
            configuration=data.get("configuration"),
            effective_datetime=_parse_dt(data.get("effective_datetime")),
            created_at=_parse_dt(data.get("created_at")),
            notes=data.get("notes"),
            study=data.get("study"),
            media_count=data.get("media_count", 0),
            media_items=[MediaItem.from_dict(m) for m in data.get("media_items", [])],
            readouts=_parse_readouts(data),
        )


@dataclass
class Patient:
    patient_id: str
    assessment_count: int
    latest_assessment_at: Optional[datetime]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "assessment_count": self.assessment_count,
            "latest_assessment_at": (
                self.latest_assessment_at.isoformat() if self.latest_assessment_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Patient":
        lat = data.get("latest_assessment_at")
        return cls(
            patient_id=data["patient_id"],
            assessment_count=data["assessment_count"],
            latest_assessment_at=(
                datetime.fromisoformat(lat.replace("Z", "+00:00")) if lat else None
            ),
        )


@dataclass
class Battery:
    id: uuid.UUID
    name: str
    description: Optional[str]
    color: Optional[str]
    active: bool
    created_at: Optional[datetime]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Battery":
        ca = data.get("created_at")
        return cls(
            id=uuid.UUID(data["id"]),
            name=data["name"],
            description=data.get("description"),
            color=data.get("color"),
            active=data.get("active", True),
            created_at=(
                datetime.fromisoformat(ca.replace("Z", "+00:00")) if ca else None
            ),
        )


