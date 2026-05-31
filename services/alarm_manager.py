"""Alarm lifecycle management for industrial health monitoring."""

from __future__ import annotations

import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from storage.service import InspectionStorageService
from services.notifications import NotificationDispatcher


class AlarmSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


@dataclass(slots=True)
class AlarmRecord:
    id: int
    timestamp: str
    category: str
    severity: str
    message: str
    source: str
    acknowledged: bool = False


class AlarmManager:
    """Manage alarm creation, acknowledgement, and persistence."""

    def __init__(
        self,
        storage: InspectionStorageService | None = None,
        notification_dispatcher: NotificationDispatcher | None = None,
    ) -> None:
        self.storage = storage
        self.notification_dispatcher = notification_dispatcher
        self._lock = threading.Lock()
        self._active: list[AlarmRecord] = []
        self._history: list[AlarmRecord] = []
        self._next_id = 1
        self._last_emitted: dict[tuple[str, str], datetime] = {}

    def raise_alarm(
        self,
        *,
        category: str,
        severity: AlarmSeverity,
        message: str,
        source: str,
        dedupe_seconds: int = 60,
    ) -> AlarmRecord:
        now = datetime.now(timezone.utc)
        dedupe_key = (category, message)
        with self._lock:
            last = self._last_emitted.get(dedupe_key)
            if last and (now - last).total_seconds() < dedupe_seconds:
                existing = self._find_latest(category=category, message=message)
                if existing is not None:
                    return existing
            alarm_id = self._persist_alarm(
                category=category,
                severity=severity.value,
                message=message,
                source=source,
            )
            alarm = AlarmRecord(
                id=alarm_id,
                timestamp=now.isoformat(),
                category=category,
                severity=severity.value,
                message=message,
                source=source,
                acknowledged=False,
            )
            self._active.insert(0, alarm)
            self._history.insert(0, alarm)
            self._active = self._active[:500]
            self._history = self._history[:2000]
            self._last_emitted[dedupe_key] = now
            if self.notification_dispatcher is not None:
                self.notification_dispatcher.notify(
                    severity=severity.value,
                    category=category,
                    message=message,
                    source=source,
                )
            return alarm

    def active_alarms(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            if self.storage is not None:
                try:
                    rows = self.storage.list_alarms(active_only=True, limit=limit)
                    return [self._row_to_alarm(row) for row in rows]
                except Exception:
                    pass
            return [asdict(item) for item in self._active[:limit]]

    def alarm_history(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock:
            if self.storage is not None:
                try:
                    rows = self.storage.list_alarms(active_only=False, limit=limit)
                    return [self._row_to_alarm(row) for row in rows]
                except Exception:
                    pass
            return [asdict(item) for item in self._history[:limit]]

    def acknowledge(self, alarm_id: int) -> bool:
        with self._lock:
            updated = False
            for alarm in self._active:
                if alarm.id == alarm_id:
                    alarm.acknowledged = True
                    updated = True
            self._active = [item for item in self._active if not item.acknowledged]
            for alarm in self._history:
                if alarm.id == alarm_id:
                    alarm.acknowledged = True
            if self.storage is not None:
                try:
                    persisted = self.storage.acknowledge_alarm(alarm_id)
                    updated = updated or persisted
                except Exception:
                    pass
            return updated

    def _persist_alarm(self, *, category: str, severity: str, message: str, source: str) -> int:
        if self.storage is not None:
            try:
                return self.storage.save_alarm(
                    category=category,
                    severity=severity,
                    message=message,
                    source=source,
                    acknowledged=False,
                )
            except Exception:
                pass
        fallback = self._next_id
        self._next_id += 1
        return fallback

    def _find_latest(self, *, category: str, message: str) -> AlarmRecord | None:
        for item in self._history:
            if item.category == category and item.message == message:
                return item
        return None

    @staticmethod
    def _row_to_alarm(row: dict[str, Any]) -> dict[str, Any]:
        created_at = row.get("created_at")
        timestamp = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
        return {
            "id": int(row.get("id", 0)),
            "timestamp": timestamp,
            "category": str(row.get("category", "")),
            "severity": str(row.get("severity", "")),
            "message": str(row.get("message", "")),
            "source": str(row.get("source", "")),
            "acknowledged": bool(row.get("acknowledged", False)),
        }
