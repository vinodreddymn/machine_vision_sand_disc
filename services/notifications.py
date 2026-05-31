"""Extensible notification framework for system health events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(slots=True)
class NotificationEvent:
    timestamp: str
    severity: str
    category: str
    message: str
    source: str


class NotificationChannel(Protocol):
    def send(self, event: NotificationEvent) -> None: ...


class DashboardNotificationChannel:
    def __init__(self) -> None:
        self._events: list[NotificationEvent] = []

    def send(self, event: NotificationEvent) -> None:
        self._events.insert(0, event)
        self._events = self._events[:500]

    def list_events(self, limit: int = 100) -> list[dict[str, str]]:
        return [
            {
                "timestamp": event.timestamp,
                "severity": event.severity,
                "category": event.category,
                "message": event.message,
                "source": event.source,
            }
            for event in self._events[:limit]
        ]


class LogNotificationChannel:
    def __init__(self) -> None:
        self._entries: list[str] = []

    def send(self, event: NotificationEvent) -> None:
        self._entries.append(
            f"{event.timestamp} [{event.severity}] {event.category} ({event.source}): {event.message}"
        )
        self._entries = self._entries[-1000:]

    def recent(self, limit: int = 200) -> list[str]:
        return self._entries[-limit:]


class EmailNotificationChannel:
    """Future channel stub for SMTP/SES integrations."""

    def send(self, event: NotificationEvent) -> None:
        _ = event
        return None


class TelegramNotificationChannel:
    """Future channel stub for Telegram bot integrations."""

    def send(self, event: NotificationEvent) -> None:
        _ = event
        return None


class SmsNotificationChannel:
    """Future channel stub for SMS provider integrations."""

    def send(self, event: NotificationEvent) -> None:
        _ = event
        return None


class NotificationDispatcher:
    def __init__(self, channels: list[NotificationChannel] | None = None) -> None:
        self.channels = channels or []

    def notify(self, *, severity: str, category: str, message: str, source: str) -> None:
        event = NotificationEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=severity,
            category=category,
            message=message,
            source=source,
        )
        for channel in self.channels:
            try:
                channel.send(event)
            except Exception:
                continue
