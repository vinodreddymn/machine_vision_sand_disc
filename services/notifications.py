"""Extensible notification framework for system health events."""

from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any, Protocol

import httpx


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
    """SMTP email notifications (optional)."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password_env: str,
        use_tls: bool,
        email_from: str,
        email_to: list[str],
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password_env = password_env
        self.use_tls = use_tls
        self.email_from = email_from
        self.email_to = email_to

    def send(self, event: NotificationEvent) -> None:
        password = os.getenv(self.password_env, "")
        if not password or not self.email_to:
            return

        msg = EmailMessage()
        msg["From"] = self.email_from
        msg["To"] = ", ".join(self.email_to)
        msg["Subject"] = f"[{event.severity}] DiskVision {event.category}"
        msg.set_content(
            "\n".join(
                [
                    f"Timestamp: {event.timestamp}",
                    f"Severity: {event.severity}",
                    f"Category: {event.category}",
                    f"Source: {event.source}",
                    "",
                    event.message,
                ]
            )
        )

        with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.username:
                smtp.login(self.username, password)
            smtp.send_message(msg)


class TelegramNotificationChannel:
    """Telegram bot notifications (optional)."""

    def __init__(self, *, bot_token_env: str, chat_ids: list[str]) -> None:
        self.bot_token_env = bot_token_env
        self.chat_ids = chat_ids

    def send(self, event: NotificationEvent) -> None:
        token = os.getenv(self.bot_token_env, "")
        if not token or not self.chat_ids:
            return
        text = (
            f"*DiskVision Alert*\n"
            f"*Severity:* {event.severity}\n"
            f"*Category:* {event.category}\n"
            f"*Source:* {event.source}\n"
            f"*Time:* {event.timestamp}\n\n"
            f"{event.message}"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        with httpx.Client(timeout=8.0) as client:
            for chat_id in self.chat_ids:
                try:
                    client.post(
                        url,
                        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                    )
                except Exception:
                    continue


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

    def channel_status(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for ch in self.channels:
            out.append({"type": ch.__class__.__name__})
        return out
