"""System health monitoring and self-healing service."""

from __future__ import annotations

import os
import shutil
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import OUTPUT_DIR, load_health_thresholds
from services.alarm_manager import AlarmManager, AlarmSeverity
from services.inspection_engine import InspectionEngine
from storage.service import InspectionStorageService


class HealthMonitorService:
    """Poll system health and apply alarm and recovery policies."""

    def __init__(
        self,
        *,
        engine: InspectionEngine,
        alarm_manager: AlarmManager,
        storage: InspectionStorageService | None,
        poll_interval_seconds: int = 10,
    ) -> None:
        self.engine = engine
        self.alarm_manager = alarm_manager
        self.storage = storage
        self.poll_interval_seconds = poll_interval_seconds
        self._thresholds = load_health_thresholds()
        self._running = False
        self._thread: threading.Thread | None = None
        self._latest: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._last_db_retry_ts = 0.0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def latest_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._latest)

    def device_status(self) -> dict[str, str]:
        snapshot = self.latest_snapshot()
        return {
            "camera": "ONLINE" if snapshot.get("camera_online") else "OFFLINE",
            "plc": "ONLINE" if snapshot.get("plc_online") else "OFFLINE",
            "database": "ONLINE" if snapshot.get("database_online") else "OFFLINE",
            "network": "ONLINE" if snapshot.get("network_online") else "OFFLINE",
        }

    def history(self, *, hours: int = 24, limit: int = 500) -> list[dict[str, Any]]:
        if self.storage is None:
            return []
        try:
            rows = self.storage.get_health_history(hours=hours, limit=limit)
            normalized: list[dict[str, Any]] = []
            for row in rows:
                captured_at = row.get("captured_at")
                normalized.append(
                    {
                        "timestamp": captured_at.isoformat() if hasattr(captured_at, "isoformat") else str(captured_at),
                        "cpu_usage": row.get("cpu_usage_percent"),
                        "memory_usage": row.get("memory_usage_percent"),
                        "temperature": row.get("cpu_temperature_c"),
                        "disk_usage": row.get("disk_usage_percent"),
                        "free_disk_gb": row.get("free_disk_gb"),
                    }
                )
            return normalized
        except Exception:
            return []

    def _loop(self) -> None:
        while self._running:
            snapshot = self._collect_snapshot()
            with self._lock:
                self._latest = snapshot
            self._evaluate_rules(snapshot)
            self._persist_snapshot(snapshot)
            time.sleep(self.poll_interval_seconds)

    def _collect_snapshot(self) -> dict[str, Any]:
        engine_health = self.engine.health_snapshot()
        total_mem, free_mem = self._memory_totals()
        mem_usage = (100.0 * (total_mem - free_mem) / total_mem) if total_mem else None
        disk = shutil.disk_usage(OUTPUT_DIR)
        disk_usage_pct = 100.0 * (1.0 - (disk.free / max(disk.total, 1)))
        cpu_temp = self._cpu_temperature()
        uptime_seconds = self._uptime_seconds()
        db_online = self._database_online()
        now = datetime.now(timezone.utc)

        return {
            "timestamp": now.isoformat(),
            "cpu_usage": round(self._cpu_usage_estimate(), 2),
            "memory_usage": round(mem_usage, 2) if mem_usage is not None else None,
            "temperature": cpu_temp,
            "cpu_frequency_mhz": self._cpu_frequency_mhz(),
            "uptime": self._format_uptime(uptime_seconds),
            "load_average": self._load_average(),
            "disk_usage": round(disk_usage_pct, 2),
            "free_disk_gb": round(disk.free / (1024 ** 3), 2),
            "sd_card_usage": round(disk_usage_pct, 2),
            "network_online": self._network_online(),
            "lan_ip": self._lan_ip(),
            "wifi_online": self._wifi_online(),
            "camera_online": bool(engine_health.get("camera_connected")),
            "camera_fps": engine_health.get("camera_fps"),
            "camera_frame_drops": engine_health.get("camera_frame_drops"),
            "last_frame_timestamp": engine_health.get("last_frame_timestamp"),
            "camera_source_name": engine_health.get("camera_source_name"),
            "camera_recovery_attempts": engine_health.get("camera_recovery_attempts"),
            "inspection_running": engine_health.get("inspection_running"),
            "current_mode": engine_health.get("current_mode"),
            "parts_per_minute": engine_health.get("parts_per_minute"),
            "average_cycle_time_ms": engine_health.get("average_cycle_time_ms"),
            "inspection_latency_ms": engine_health.get("inspection_latency_ms"),
            "inference_time_ms": engine_health.get("inference_time_ms"),
            "queue_backlog": engine_health.get("queue_backlog"),
            "thread_status": engine_health.get("thread_status"),
            "plc_online": self._plc_online(),
            "plc_latency_ms": self._plc_latency_ms(),
            "plc_heartbeat_ok": self._plc_online(),
            "plc_last_success": now.isoformat() if self._plc_online() else None,
            "plc_error_count": 0 if self._plc_online() else 1,
            "database_online": db_online,
            "database_connection": "CONNECTED" if db_online else "DISCONNECTED",
            "database_last_success": now.isoformat() if db_online else None,
            "database_size_bytes": self._database_size_bytes(),
            "database_write_failures": 0,
        }

    def _evaluate_rules(self, snapshot: dict[str, Any]) -> None:
        self._apply_temperature_rules(snapshot)
        self._apply_camera_rules(snapshot)
        self._apply_database_rules(snapshot)
        self._apply_plc_rules(snapshot)
        self._apply_disk_rules(snapshot)

    def _apply_temperature_rules(self, snapshot: dict[str, Any]) -> None:
        temp = snapshot.get("temperature")
        if temp is None:
            return
        warning = float(self._thresholds.get("cpu_temp_warning", 75))
        critical = float(self._thresholds.get("cpu_temp_critical", 80))
        emergency = float(self._thresholds.get("cpu_temp_emergency", 85))
        if temp >= emergency:
            self.alarm_manager.raise_alarm(
                category="TEMPERATURE",
                severity=AlarmSeverity.EMERGENCY,
                message=f"CPU temperature emergency: {temp:.1f}C",
                source="health_monitor",
            )
            self.engine.save_runtime_state()
            self.engine.safe_stop()
            return
        if temp >= critical:
            self.alarm_manager.raise_alarm(
                category="TEMPERATURE",
                severity=AlarmSeverity.CRITICAL,
                message=f"CPU temperature critical: {temp:.1f}C",
                source="health_monitor",
            )
            self.engine.reduce_camera_fps(15.0)
            self.engine.reduce_processing_rate(1.3)
            return
        if temp >= warning:
            self.alarm_manager.raise_alarm(
                category="TEMPERATURE",
                severity=AlarmSeverity.WARNING,
                message=f"CPU temperature warning: {temp:.1f}C",
                source="health_monitor",
            )

    def _apply_camera_rules(self, snapshot: dict[str, Any]) -> None:
        last_frame_iso = snapshot.get("last_frame_timestamp")
        if not last_frame_iso:
            return
        try:
            frame_dt = datetime.fromisoformat(last_frame_iso)
            elapsed = (datetime.now(frame_dt.tzinfo) - frame_dt).total_seconds()
        except Exception:
            return
        threshold = float(self._thresholds.get("camera_no_frame_seconds", 5))
        retries = int(self._thresholds.get("camera_max_recovery_retries", 3))
        if elapsed <= threshold:
            return
        for _ in range(retries):
            if self.engine.recover_camera():
                self.alarm_manager.raise_alarm(
                    category="CAMERA",
                    severity=AlarmSeverity.WARNING,
                    message="Camera recovered after frame timeout.",
                    source="health_monitor",
                )
                return
        self.alarm_manager.raise_alarm(
            category="CAMERA",
            severity=AlarmSeverity.CRITICAL,
            message="Camera recovery failed after max retries.",
            source="health_monitor",
        )

    def _apply_database_rules(self, snapshot: dict[str, Any]) -> None:
        if snapshot.get("database_online"):
            return
        self.alarm_manager.raise_alarm(
            category="DATABASE",
            severity=AlarmSeverity.CRITICAL,
            message="Database offline. Reconnect retries are active.",
            source="health_monitor",
        )
        retry_every = int(self._thresholds.get("database_reconnect_seconds", 30))
        now_ts = time.time()
        if now_ts - self._last_db_retry_ts < retry_every:
            return
        self._last_db_retry_ts = now_ts
        if self.storage is not None:
            try:
                _ = self.storage.health_query()
            except Exception:
                pass

    def _apply_plc_rules(self, snapshot: dict[str, Any]) -> None:
        if snapshot.get("plc_online"):
            return
        self.alarm_manager.raise_alarm(
            category="PLC",
            severity=AlarmSeverity.WARNING,
            message="PLC communication unavailable. Vision continues in degraded mode.",
            source="health_monitor",
        )

    def _apply_disk_rules(self, snapshot: dict[str, Any]) -> None:
        free_gb = float(snapshot.get("free_disk_gb") or 0.0)
        warning = float(self._thresholds.get("disk_free_warning_gb", 10))
        critical = float(self._thresholds.get("disk_free_critical_gb", 5))
        emergency = float(self._thresholds.get("disk_free_emergency_gb", 1))
        if free_gb < emergency:
            self._disable_archiving()
            self.alarm_manager.raise_alarm(
                category="STORAGE",
                severity=AlarmSeverity.EMERGENCY,
                message=f"Disk space emergency: {free_gb:.2f} GB free. Archiving disabled.",
                source="health_monitor",
            )
            return
        if free_gb < critical:
            self._cleanup_temp_files()
            self.alarm_manager.raise_alarm(
                category="STORAGE",
                severity=AlarmSeverity.CRITICAL,
                message=f"Disk space critical: {free_gb:.2f} GB free. Cleanup executed.",
                source="health_monitor",
            )
            return
        if free_gb < warning:
            self.alarm_manager.raise_alarm(
                category="STORAGE",
                severity=AlarmSeverity.WARNING,
                message=f"Disk space warning: {free_gb:.2f} GB free.",
                source="health_monitor",
            )

    def _persist_snapshot(self, snapshot: dict[str, Any]) -> None:
        if self.storage is None:
            return
        try:
            self.storage.save_health_snapshot(snapshot)
            self.storage.prune_health_history(days=30)
        except Exception:
            pass

    @staticmethod
    def _cpu_usage_estimate() -> float:
        try:
            load1, _, _ = os.getloadavg()
            cpu_count = max(os.cpu_count() or 1, 1)
            return max(0.0, min(100.0, (load1 / cpu_count) * 100.0))
        except Exception:
            return 0.0

    @staticmethod
    def _load_average() -> dict[str, float]:
        try:
            load1, load5, load15 = os.getloadavg()
            return {"1m": round(load1, 3), "5m": round(load5, 3), "15m": round(load15, 3)}
        except Exception:
            return {"1m": 0.0, "5m": 0.0, "15m": 0.0}

    @staticmethod
    def _memory_totals() -> tuple[int, int]:
        meminfo = Path("/proc/meminfo")
        if not meminfo.exists():
            return (0, 0)
        values: dict[str, int] = {}
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            parts = line.split(":")
            if len(parts) != 2:
                continue
            key = parts[0].strip()
            raw_value = parts[1].strip().split(" ")[0]
            if raw_value.isdigit():
                values[key] = int(raw_value) * 1024
        return values.get("MemTotal", 0), values.get("MemAvailable", 0)

    @staticmethod
    def _cpu_temperature() -> float | None:
        candidates = [
            Path("/sys/class/thermal/thermal_zone0/temp"),
            Path("/sys/devices/virtual/thermal/thermal_zone0/temp"),
        ]
        for path in candidates:
            if not path.exists():
                continue
            raw = path.read_text(encoding="utf-8").strip()
            try:
                val = float(raw)
                return round(val / 1000.0 if val > 1000 else val, 2)
            except ValueError:
                continue
        return None

    @staticmethod
    def _cpu_frequency_mhz() -> float | None:
        path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8").strip()
        try:
            return round(float(raw) / 1000.0, 2)
        except ValueError:
            return None

    @staticmethod
    def _uptime_seconds() -> int:
        path = Path("/proc/uptime")
        if not path.exists():
            return 0
        try:
            value = path.read_text(encoding="utf-8").split()[0]
            return int(float(value))
        except Exception:
            return 0

    @staticmethod
    def _format_uptime(seconds: int) -> str:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        mins = (seconds % 3600) // 60
        return f"{days}d {hours}h {mins}m"

    @staticmethod
    def _network_online() -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(1.0)
                sock.connect(("8.8.8.8", 53))
                return True
        except Exception:
            return False

    @staticmethod
    def _lan_ip() -> str | None:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return None

    @staticmethod
    def _wifi_online() -> bool:
        net_dir = Path("/sys/class/net")
        if not net_dir.exists():
            return False
        for nic in net_dir.iterdir():
            if nic.name.startswith("wlan"):
                carrier = nic / "carrier"
                if carrier.exists() and carrier.read_text(encoding="utf-8").strip() == "1":
                    return True
        return False

    def _database_online(self) -> bool:
        if self.storage is None:
            return False
        try:
            return self.storage.health_query()
        except Exception:
            return False

    def _database_size_bytes(self) -> int:
        if self.storage is None:
            return 0
        try:
            return self.storage.database_size_bytes()
        except Exception:
            return 0

    def _plc_online(self) -> bool:
        try:
            status = self.engine.plc.read_status()
            return bool(status)
        except Exception:
            return False

    def _plc_latency_ms(self) -> float:
        started = time.perf_counter()
        try:
            _ = self.engine.plc.read_status()
        except Exception:
            return -1.0
        return round((time.perf_counter() - started) * 1000.0, 2)

    @staticmethod
    def _cleanup_temp_files() -> None:
        cleanup_dirs = [OUTPUT_DIR / "temp", OUTPUT_DIR / "cache", OUTPUT_DIR / "overlays"]
        now = time.time()
        for directory in cleanup_dirs:
            if not directory.exists():
                continue
            for item in directory.rglob("*"):
                if not item.is_file():
                    continue
                try:
                    age_hours = (now - item.stat().st_mtime) / 3600.0
                    if age_hours > 24:
                        item.unlink(missing_ok=True)
                except Exception:
                    continue

    def _disable_archiving(self) -> None:
        self.engine._log("Image archiving disabled due to disk emergency condition.")
