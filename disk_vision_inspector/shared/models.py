from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ServiceHealth:
    name: str
    status: str
    version: str | None = None

