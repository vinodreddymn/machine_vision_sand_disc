"""Structured storage models shared by database repositories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class StoredInspection:
    """One inspection record retrieved from persistent storage."""

    id: int
    physical_part_id: str
    stage: str
    serial_number: str
    inspected_at: datetime
    decision: str
    final_disposition: str
    source_name: str | None
    reject_requested: bool
    measurements: dict[str, Any]
    defects: list[str]
    overlay_path: str | None
