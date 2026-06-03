"""FastAPI backend and browser dashboard."""

from __future__ import annotations

import asyncio
import base64
import io
import os
import time
from pathlib import Path
from dataclasses import asdict
from typing import Any
import re

import cv2
import numpy as np
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.settings import (
    load_tolerances,
    save_tolerances,
    load_confidence_thresholds,
    save_confidence_thresholds,
    SUPPORTED_INSPECTION_MODES,
)
from config.settings import POSTGRES_DSN
from config.settings import load_security_config
from config.settings import load_notifications_config
from services.alarm_manager import AlarmManager
from services.config_manager import ConfigurationService, get_config_service
from services.health_monitor import HealthMonitorService
from services.inspection_engine import InspectionEngine
from services.notifications import (
    DashboardNotificationChannel,
    LogNotificationChannel,
    NotificationDispatcher,
    EmailNotificationChannel,
    TelegramNotificationChannel,
)
from dataset.exporter import DatasetExporter
from disk_vision_inspector.config_service.settings import RuntimeSettings
from services.calibration.validation import validate_calibration
from services.security import (
    ROLE_ADMIN,
    ROLE_OPERATOR,
    ROLE_SUPERVISOR,
    decode_jwt,
    encode_jwt,
    hash_password,
    load_jwt_config,
    role_allows,
    verify_password,
)
from storage.postgres import PostgresInspectionRepository
from storage.service import InspectionStorageService


class LabelRequest(BaseModel):
    operator_label: str
    station: str = "S1"


class OverrideLabelRequest(BaseModel):
    operator_label: str
    station: str = "S1"
    override_reason: str | None = None


class StartPartRequest(BaseModel):
    station: str = "S1"


class ModeRequest(BaseModel):
    mode: str


class CalibrationSaveRequest(BaseModel):
    camera_id: str = "CAM01"
    outer_diameter_px: float
    reference_od_mm: float
    reference_hole_mm: float


class CalibrationValidateRequest(BaseModel):
    camera_id: str = "CAM01"
    reference_od_mm: float
    tolerance: float = 0.10


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = ROLE_OPERATOR
    active: bool = True


class RuntimeCommandRequest(BaseModel):
    requested_by: str | None = None


class ModelRegistryRequest(BaseModel):
    version: str
    training_date: str | None = None
    dataset_size: int | None = None
    accuracy: float | None = None
    active: bool = False
    notes: str | None = None
    model_path: str


class DatasetExportRequest(BaseModel):
    export_root: str | None = None


class ConfidenceThresholdRequest(BaseModel):
    high_confidence: float
    medium_confidence: float
    low_confidence: float = 0.0


def _build_default_engine() -> InspectionEngine:
    storage: InspectionStorageService | None = None
    try:
        storage = InspectionStorageService(PostgresInspectionRepository(POSTGRES_DSN))
    except Exception:
        storage = None
    return InspectionEngine(storage=storage)


def create_app(engine: InspectionEngine | None = None) -> FastAPI:
    engine = engine or _build_default_engine()
    security_cfg = load_security_config()
    auth_enabled = bool(security_cfg.get("auth_enabled", False))
    jwt_cfg = load_jwt_config(security_cfg)
    dashboard_notifications = DashboardNotificationChannel()
    log_notifications = LogNotificationChannel()
    notif_cfg = load_notifications_config()
    channels = [dashboard_notifications, log_notifications]
    if bool(notif_cfg.get("email_enabled", False)):
        channels.append(
            EmailNotificationChannel(
                host=str(notif_cfg.get("smtp_host", "")),
                port=int(notif_cfg.get("smtp_port", 587)),
                username=str(notif_cfg.get("smtp_username", "")),
                password_env=str(notif_cfg.get("smtp_password_env", "DISK_VISION_SMTP_PASSWORD")),
                use_tls=bool(notif_cfg.get("smtp_use_tls", True)),
                email_from=str(notif_cfg.get("email_from", "")),
                email_to=[str(x) for x in (notif_cfg.get("email_to", []) or [])],
            )
        )
    if bool(notif_cfg.get("telegram_enabled", False)):
        channels.append(
            TelegramNotificationChannel(
                bot_token_env=str(notif_cfg.get("telegram_bot_token_env", "DISK_VISION_TELEGRAM_BOT_TOKEN")),
                chat_ids=[str(x) for x in (notif_cfg.get("telegram_chat_ids", []) or [])],
            )
        )
    dispatcher = NotificationDispatcher(channels=channels)
    alarm_manager = AlarmManager(
        storage=engine.storage if engine.storage_available else None,
        notification_dispatcher=dispatcher,
    )
    health_monitor = HealthMonitorService(
        engine=engine,
        alarm_manager=alarm_manager,
        storage=engine.storage if engine.storage_available else None,
        poll_interval_seconds=10,
    )
    modular_settings = RuntimeSettings()
    app = FastAPI(title="DiskVisionInspector API")

    if bool(security_cfg.get("rate_limit_enabled", False)):
        per_minute = int(security_cfg.get("rate_limit_per_minute", 120))
        buckets: dict[str, tuple[int, int]] = {}

        @app.middleware("http")
        async def _rate_limit(request: Request, call_next):
            key = f"{request.client.host}:{request.url.path}"
            now_min = int(time.time() // 60)
            count, last_min = buckets.get(key, (0, now_min))
            if last_min != now_min:
                count = 0
                last_min = now_min
            count += 1
            buckets[key] = (count, last_min)
            if count > per_minute:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            return await call_next(request)
    web_dist = Path(__file__).resolve().parents[1] / "web" / "dist"
    assets_dir = web_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def dashboard():
        index_path = web_dist / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return Response("Web dashboard has not been built. Run npm install && npm run build in web/.", media_type="text/plain")

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        return engine.status()

    def _current_user(token: str | None) -> dict[str, Any] | None:
        if not token:
            return None
        payload = decode_jwt(token, cfg=jwt_cfg)
        return payload

    def _require_role(required_role: str):
        def _dep(authorization: str | None = Header(default=None, alias="Authorization")):
            if not auth_enabled:
                return {"role": ROLE_ADMIN, "sub": "disabled"}
            if not authorization or not authorization.lower().startswith("bearer "):
                raise HTTPException(status_code=401, detail="Missing token")
            token = authorization.split(" ", 1)[1].strip()
            payload = _current_user(token)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token")
            role = str(payload.get("role", ""))
            if not role_allows(role, required_role):
                raise HTTPException(status_code=403, detail="Insufficient role")
            return payload
        return _dep

    @app.get("/api/auth/config")
    def auth_config() -> dict[str, Any]:
        return {"auth_enabled": auth_enabled}

    @app.post("/api/auth/login")
    def login(request: LoginRequest) -> dict[str, Any]:
        if not auth_enabled:
            return {"token": None, "auth_enabled": False}
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline")
        # Ensure a default admin exists for first-time deployments.
        default_admin_user = os.getenv("DISK_VISION_DEFAULT_ADMIN_USER", "admin")
        default_admin_pass = os.getenv("DISK_VISION_DEFAULT_ADMIN_PASS", "")
        if default_admin_pass:
            engine.storage.ensure_default_admin(
                username=default_admin_user,
                password_hash=hash_password(default_admin_pass),
            )
        user = engine.storage.get_user_by_username(request.username)
        if not user or not bool(user.get("active", False)):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not verify_password(request.password, str(user.get("password_hash", ""))):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = encode_jwt({"sub": user["username"], "role": user["role"]}, cfg=jwt_cfg)
        try:
            engine.storage.write_audit_log(
                actor=str(user["username"]),
                action="LOGIN",
                resource="auth",
                message="User login",
                details={"role": user["role"]},
            )
        except Exception:
            pass
        return {"token": token, "auth_enabled": True, "role": user["role"]}

    @app.get("/api/admin/users")
    def list_users(_: dict[str, Any] = Depends(_require_role(ROLE_ADMIN)), limit: int = 200) -> list[dict[str, Any]]:
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline")
        users = engine.storage.list_users(limit=limit)
        normalized: list[dict[str, Any]] = []
        for row in users:
            created_at = row.get("created_at")
            normalized.append(
                {
                    "id": int(row.get("id", 0)),
                    "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
                    "username": str(row.get("username", "")),
                    "role": str(row.get("role", "")),
                    "active": bool(row.get("active", False)),
                }
            )
        return normalized

    @app.post("/api/admin/users")
    def create_user(req: CreateUserRequest, _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> dict[str, Any]:
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline")
        if not re.fullmatch(r"[a-zA-Z0-9_.-]{3,32}", req.username.strip()):
            raise HTTPException(status_code=400, detail="Invalid username (3-32 chars: a-z,0-9,._-)")
        if len(req.password) < 6:
            raise HTTPException(status_code=400, detail="Password too short (min 6)")
        role = req.role.strip().upper()
        if role not in {ROLE_OPERATOR, ROLE_SUPERVISOR, ROLE_ADMIN}:
            raise HTTPException(status_code=400, detail="Invalid role")
        user_id = engine.storage.create_user(username=req.username, password_hash=hash_password(req.password), role=role)
        try:
            engine.storage.write_audit_log(
                actor="admin",
                action="CREATE_USER",
                resource="app_users",
                message=f"Created user {req.username}",
                details={"username": req.username, "role": role},
            )
        except Exception:
            pass
        return {"status": "success", "id": user_id}

    @app.get("/api/admin/audit-logs")
    def audit_logs(_: dict[str, Any] = Depends(_require_role(ROLE_ADMIN)), limit: int = 200) -> list[dict[str, Any]]:
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline")
        rows = engine.storage.list_audit_logs(limit=limit)
        out: list[dict[str, Any]] = []
        for row in rows:
            created_at = row.get("created_at")
            out.append(
                {
                    "id": int(row.get("id", 0)),
                    "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
                    "actor": row.get("actor"),
                    "action": row.get("action"),
                    "resource": row.get("resource"),
                    "message": row.get("message"),
                    "details": row.get("details"),
                }
            )
        return out

    @app.get("/api/audit/events")
    def unified_audit_events(
        limit: int = 200,
        _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN)),
    ) -> list[dict[str, Any]]:
        """Return a merged audit timeline across configuration, models, labels, and system actions."""
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline")
        system_rows = engine.storage.list_audit_logs(limit=limit)
        config_rows = config_service.get_audit_log(limit=limit)
        events: list[dict[str, Any]] = []
        for row in system_rows:
            created_at = row.get("created_at")
            events.append(
                {
                    "source": "SYSTEM",
                    "timestamp": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
                    "actor": row.get("actor"),
                    "action": row.get("action"),
                    "resource": row.get("resource"),
                    "message": row.get("message"),
                    "details": row.get("details"),
                }
            )
        for row in config_rows:
            changed_at = row.get("changed_at")
            events.append(
                {
                    "source": "CONFIG",
                    "timestamp": changed_at.isoformat() if hasattr(changed_at, "isoformat") else str(changed_at),
                    "actor": row.get("changed_by"),
                    "action": row.get("action"),
                    "resource": row.get("config_key"),
                    "message": row.get("reason") or f"{row.get('action')} {row.get('config_key')}",
                    "details": {
                        "version_number": row.get("version_number"),
                        "old_value": row.get("old_value"),
                        "new_value": row.get("new_value"),
                        "ip_address": row.get("ip_address"),
                    },
                }
            )
        events.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
        return events[:limit]

    @app.get("/api/cameras")
    def cameras() -> list[dict[str, Any]]:
        return engine.camera_status()

    @app.get("/api/inspection/latest")
    def latest() -> dict[str, Any]:
        return engine.latest_inspection()

    @app.get("/api/station1")
    def station1() -> dict[str, Any]:
        return engine.station_status("S1")

    @app.get("/api/runtime/state")
    def runtime_state() -> dict[str, Any]:
        return engine.runtime_controller.as_dict()

    @app.post("/api/runtime/start")
    def runtime_start(request: RuntimeCommandRequest | None = None) -> dict[str, Any]:
        payload = request or RuntimeCommandRequest()
        engine.runtime_controller.start(requested_by=payload.requested_by or "API")
        engine.start()
        return engine.runtime_controller.as_dict()

    @app.post("/api/runtime/stop")
    def runtime_stop(request: RuntimeCommandRequest | None = None) -> dict[str, Any]:
        payload = request or RuntimeCommandRequest()
        engine.runtime_controller.stop(requested_by=payload.requested_by or "API")
        engine.stop()
        return engine.runtime_controller.as_dict()

    @app.post("/api/runtime/reset")
    def runtime_reset(request: RuntimeCommandRequest | None = None) -> dict[str, Any]:
        payload = request or RuntimeCommandRequest()
        engine.runtime_controller.reset(requested_by=payload.requested_by or "API")
        engine.reset_part()
        return engine.runtime_controller.as_dict()

    @app.get("/api/plc/status")
    def plc_status() -> dict[str, Any]:
        return asdict(engine.plc.read_status())

    @app.post("/api/plc/command/{command}")
    def plc_command(command: str, request: RuntimeCommandRequest | None = None) -> dict[str, Any]:
        payload = request or RuntimeCommandRequest()
        command_name = command.strip().lower()
        if command_name not in {
            "start_request",
            "stop_request",
            "reset_request",
            "reload_config_request",
            "confirm_label_request",
            "override_label_request",
        }:
            raise HTTPException(status_code=404, detail=f"Unknown PLC command: {command}")
        handler = getattr(engine.plc, command_name, None)
        if not callable(handler):
            raise HTTPException(status_code=501, detail=f"PLC command not supported: {command}")
        handler()
        if command_name == "reload_config_request":
            engine.runtime_controller.request_reload_config(requested_by=payload.requested_by or "API")
        elif command_name == "start_request":
            engine.runtime_controller.ready(requested_by=payload.requested_by or "API")
        elif command_name == "stop_request":
            engine.runtime_controller.stop(requested_by=payload.requested_by or "API")
        elif command_name == "reset_request":
            engine.runtime_controller.reset(requested_by=payload.requested_by or "API")
        return {"status": "success", "command": command_name, "plc": asdict(engine.plc.read_status())}

    @app.get("/api/config/tolerances")
    def get_tolerances() -> dict[str, Any]:
        return load_tolerances()

    @app.post("/api/config/tolerances")
    def update_tolerances(tolerances: dict[str, Any], _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> dict[str, str]:
        try:
            save_tolerances(tolerances)
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"status": "success"}

    @app.get("/api/config/confidence-thresholds")
    def get_confidence_thresholds() -> dict[str, Any]:
        return load_confidence_thresholds()

    @app.post("/api/config/confidence-thresholds")
    def update_confidence_thresholds(
        thresholds: ConfidenceThresholdRequest,
        _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN)),
    ) -> dict[str, Any]:
        if not (0.0 <= thresholds.low_confidence <= thresholds.medium_confidence <= thresholds.high_confidence <= 1.0):
            raise HTTPException(status_code=400, detail="Confidence thresholds must satisfy low <= medium <= high and stay within 0..1")
        payload = thresholds.model_dump()
        save_confidence_thresholds(payload)
        engine.confidence_thresholds = payload
        return {"status": "success", "thresholds": payload}

    @app.post("/api/config/mode")
    def set_mode(request: ModeRequest, _: dict[str, Any] = Depends(_require_role(ROLE_SUPERVISOR))) -> dict[str, str]:
        mode_val = request.mode.strip().upper()
        if mode_val not in SUPPORTED_INSPECTION_MODES:
            raise HTTPException(status_code=400, detail=f"Unsupported mode: {request.mode}")
        engine.inspection_mode = mode_val
        return {"mode": engine.inspection_mode}

    # Configuration Management Endpoints (Industry 4.0 compliant)
    config_service = get_config_service()

    @app.get("/api/config/all")
    def get_all_configs() -> list[dict[str, Any]]:
        """Get all active configurations with metadata."""
        try:
            return config_service.list_all_configs()
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @app.post("/api/config/reload")
    def reload_config(config_key: str | None = None) -> dict[str, Any]:
        """Reload configuration data from the database without restarting the process."""
        try:
            reloaded = config_service.reload_config(config_key)
            if config_key:
                try:
                    engine.storage.write_audit_log(
                        actor="system",
                        action="CONFIG_RELOAD",
                        resource="config_store",
                        message=f"Reloaded configuration {config_key}",
                        details={"config_key": config_key, "version": config_service.get_config_version(config_key)},
                    )
                except Exception:
                    pass
                engine.runtime_controller.acknowledge_reload_config(requested_by="API")
                engine.runtime_controller.set_config_version(config_service.get_config_version(config_key))
                return {
                    "config_key": config_key,
                    "version": config_service.get_config_version(config_key),
                    "data": reloaded,
                }
            return {"configs": reloaded}
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @app.get("/api/config/{config_key}/version")
    def get_config_version(config_key: str) -> dict[str, Any]:
        """Return the latest stored version number for one configuration."""
        try:
            return {"config_key": config_key, "version": config_service.get_config_version(config_key)}
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @app.get("/api/models")
    def list_models(limit: int = 200, _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> list[dict[str, Any]]:
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline")
        return engine.storage.list_models(limit=limit)

    @app.post("/api/models")
    def create_model(request: ModelRegistryRequest, _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> dict[str, Any]:
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline")
        model_id = engine.storage.create_model(payload=request.model_dump())
        try:
            engine.storage.write_audit_log(
                actor="admin",
                action="MODEL_CREATE",
                resource="model_registry",
                message=f"Created model {request.version}",
                details=request.model_dump(),
            )
        except Exception:
            pass
        return {"status": "success", "id": model_id}

    @app.post("/api/models/{version}/activate")
    def activate_model(version: str, _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> dict[str, Any]:
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline")
        if not engine.storage.activate_model(version):
            raise HTTPException(status_code=404, detail="Model not found")
        try:
            engine.storage.write_audit_log(
                actor="admin",
                action="MODEL_ACTIVATE",
                resource="model_registry",
                message=f"Activated model {version}",
                details={"version": version},
            )
        except Exception:
            pass
        return {"status": "success", "version": version, "active": True}

    @app.post("/api/models/{version}/deactivate")
    def deactivate_model(version: str, _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> dict[str, Any]:
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline")
        if not engine.storage.deactivate_model(version):
            raise HTTPException(status_code=404, detail="Model not found")
        try:
            engine.storage.write_audit_log(
                actor="admin",
                action="MODEL_DEACTIVATE",
                resource="model_registry",
                message=f"Deactivated model {version}",
                details={"version": version},
            )
        except Exception:
            pass
        return {"status": "success", "version": version, "active": False}

    @app.post("/api/models/{version}/rollback")
    def rollback_model(version: str, _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> dict[str, Any]:
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline")
        if not engine.storage.rollback_model(version):
            raise HTTPException(status_code=404, detail="Model not found")
        try:
            engine.storage.write_audit_log(
                actor="admin",
                action="MODEL_ROLLBACK",
                resource="model_registry",
                message=f"Rolled back active model to {version}",
                details={"version": version},
            )
        except Exception:
            pass
        return {"status": "success", "version": version}

    @app.post("/api/dataset/export")
    def export_dataset(request: DatasetExportRequest | None = None, _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> dict[str, Any]:
        exporter = DatasetExporter(export_root=Path(request.export_root) if request and request.export_root else Path("dataset_export"))
        root = exporter.export_generic()
        return {"status": "success", "export_root": str(root)}


    @app.get("/api/config/audit-log")
    def get_config_audit_log(
        config_key: str | None = None,
        limit: int = 100,
        _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))
    ) -> list[dict[str, Any]]:
        """Get configuration audit log for compliance and traceability."""
        try:
            logs = config_service.get_audit_log(config_key=config_key, limit=limit)
            # Convert datetime objects to ISO format strings
            for log in logs:
                if hasattr(log.get("changed_at"), "isoformat"):
                    log["changed_at"] = log["changed_at"].isoformat()
            return logs
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error


    @app.get("/api/config/{config_key}")
    def get_config(config_key: str) -> dict[str, Any]:
        """Get a specific configuration by key."""
        try:
            config_data = config_service.load_config(config_key)

            if not config_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Configuration not found: {config_key}"
                )

            return config_data

        except HTTPException:
            raise

        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=str(error)
            ) from error

    @app.post("/api/config/{config_key}")
    def save_config(
        config_key: str,
        payload: dict[str, Any],
        description: str | None = None,
        reason: str | None = None,
        _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))
    ) -> dict[str, Any]:
        """Save a configuration with automatic versioning and audit trail."""
        try:
            user = _
            updated_by = user.get("sub", "system") if user else "system"
            config_data = {key: value for key, value in payload.items() if key not in {"description", "reason"}}
            description = description or str(payload.get("description") or "") or None
            reason = reason or str(payload.get("reason") or "") or None
            saved = config_service.save_config(
                config_key,
                config_data,
                updated_by=updated_by,
                description=description,
                reason=reason
            )
            engine.runtime_controller.set_config_version(int(saved.get("version", 0)))
            try:
                engine.storage.write_audit_log(
                    actor=updated_by,
                    action="CONFIG_SAVE",
                    resource="config_store",
                    message=f"Saved configuration {config_key}",
                    details={"config_key": config_key, "version": saved.get("version"), "description": description, "reason": reason},
                )
            except Exception:
                pass
            return saved
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/api/config/{config_key}/versions")
    def get_config_versions(config_key: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get version history for a configuration."""
        try:
            return config_service.list_config_versions(config_key, limit=limit)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @app.post("/api/config/{config_key}/rollback/{version}")
    def rollback_config(
        config_key: str,
        version: int,
        payload: dict[str, Any] | None = None,
        reason: str | None = None,
        _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))
    ) -> dict[str, Any]:
        """Rollback a configuration to a previous version."""
        try:
            user = _
            rolled_back_by = user.get("sub", "system") if user else "system"
            if payload:
                reason = reason or str(payload.get("reason") or "") or None
            rolled_back = config_service.rollback_config(
                config_key,
                version,
                rolled_back_by=rolled_back_by,
                reason=reason
            )
            engine.runtime_controller.set_config_version(int(rolled_back.get("version", 0)))
            try:
                engine.storage.write_audit_log(
                    actor=rolled_back_by,
                    action="CONFIG_ROLLBACK",
                    resource="config_store",
                    message=f"Rolled back configuration {config_key} to v{version}",
                    details={"config_key": config_key, "target_version": version, "new_version": rolled_back.get("version"), "reason": reason},
                )
            except Exception:
                pass
            return rolled_back
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error


    @app.get("/api/metrics")
    def metrics() -> dict[str, Any]:
        return engine.metrics()

    @app.get("/api/dataset/stats")
    def dataset_stats() -> dict[str, float | int]:
        return engine.dataset_stats()

    @app.get("/api/history")
    def history() -> list[dict[str, Any]]:
        return engine.recent_history()

    @app.get("/api/logs")
    def logs() -> list[str]:
        return engine.recent_logs()

    @app.get("/api/system/health")
    def system_health() -> dict[str, Any]:
        snapshot = health_monitor.latest_snapshot()
        return {
            "cpu_usage": snapshot.get("cpu_usage"),
            "memory_usage": snapshot.get("memory_usage"),
            "temperature": snapshot.get("temperature"),
            "disk_usage": snapshot.get("disk_usage"),
            "uptime": snapshot.get("uptime"),
            "cpu_frequency_mhz": snapshot.get("cpu_frequency_mhz"),
            "load_average": snapshot.get("load_average"),
            "free_disk_gb": snapshot.get("free_disk_gb"),
            "network_online": snapshot.get("network_online"),
            "lan_ip": snapshot.get("lan_ip"),
            "wifi_online": snapshot.get("wifi_online"),
            "camera_online": snapshot.get("camera_online"),
            "camera_fps": snapshot.get("camera_fps"),
            "camera_frame_drops": snapshot.get("camera_frame_drops"),
            "last_frame_timestamp": snapshot.get("last_frame_timestamp"),
            "camera_source_name": snapshot.get("camera_source_name"),
            "camera_recovery_attempts": snapshot.get("camera_recovery_attempts"),
            "inspection_running": snapshot.get("inspection_running"),
            "current_mode": snapshot.get("current_mode"),
            "parts_per_minute": snapshot.get("parts_per_minute"),
            "average_cycle_time_ms": snapshot.get("average_cycle_time_ms"),
            "inspection_latency_ms": snapshot.get("inspection_latency_ms"),
            "inference_time_ms": snapshot.get("inference_time_ms"),
            "queue_backlog": snapshot.get("queue_backlog"),
            "thread_status": snapshot.get("thread_status"),
            "plc_online": snapshot.get("plc_online"),
            "plc_latency_ms": snapshot.get("plc_latency_ms"),
            "plc_heartbeat_ok": snapshot.get("plc_heartbeat_ok"),
            "plc_last_success": snapshot.get("plc_last_success"),
            "plc_error_count": snapshot.get("plc_error_count"),
            "database_online": snapshot.get("database_online"),
            "database_connection": snapshot.get("database_connection"),
            "database_last_success": snapshot.get("database_last_success"),
            "database_size_bytes": snapshot.get("database_size_bytes"),
            "database_write_failures": snapshot.get("database_write_failures"),
            "storage_status": "ONLINE" if engine.storage_available else "OFFLINE",
            "timestamp": snapshot.get("timestamp"),
        }

    @app.get("/api/system/diagnostics")
    def system_diagnostics() -> dict[str, Any]:
        model_rows = []
        try:
            if engine.storage_available and engine.storage is not None:
                model_rows = engine.storage.list_models(limit=1)
        except Exception:
            model_rows = []
        latest_model = model_rows[0] if model_rows else None
        return {
            "database": "ONLINE" if engine.storage_available and engine.storage and engine.storage.health_query() else "OFFLINE",
            "camera": engine.camera_source.name if engine.camera_source is not None else "UNKNOWN",
            "plc": "ONLINE" if engine.plc is not None else "OFFLINE",
            "storage": "ONLINE" if engine.storage_available else "OFFLINE",
            "model": "ONLINE" if latest_model else "NO_ACTIVE_MODEL",
            "model_version": latest_model.get("version") if latest_model else None,
            "config_version": engine.runtime_controller.as_dict().get("config_version"),
            "inspection_runtime": engine.runtime_controller.as_dict(),
        }

    @app.get("/api/system/devices")
    def system_devices() -> dict[str, str]:
        return health_monitor.device_status()

    @app.get("/api/system/alarms")
    def system_alarms() -> list[dict[str, Any]]:
        return alarm_manager.active_alarms()

    @app.get("/api/system/alarm-history")
    def system_alarm_history() -> list[dict[str, Any]]:
        return alarm_manager.alarm_history()

    @app.get("/api/system/notifications")
    def system_notifications() -> dict[str, Any]:
        return {
            "dashboard": dashboard_notifications.list_events(200),
            "logs": log_notifications.recent(200),
            "channels": dispatcher.channel_status(),
        }

    @app.post("/api/admin/notification-test")
    def notification_test(
        severity: str = "INFO",
        category: str = "TEST",
        message: str = "Notification test event",
        _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN)),
    ) -> dict[str, Any]:
        dispatcher.notify(severity=severity, category=category, message=message, source="admin_test")
        return {"status": "sent", "channels": dispatcher.channel_status()}

    @app.post("/api/admin/backup/create")
    def admin_backup_create(_: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> dict[str, Any]:
        """Create a backup bundle via the local backup service (if available)."""
        import httpx
        try:
            res = httpx.post("http://127.0.0.1:8115/backup/create", timeout=600.0)
            res.raise_for_status()
            return res.json()
        except Exception as error:
            raise HTTPException(status_code=503, detail=f"Backup service unavailable: {error}")

    @app.get("/api/system/services")
    def system_services() -> dict[str, Any]:
        """Return modular service health snapshots when running watchdog-based deployment."""
        def probe(port: int) -> dict[str, Any]:
            import http.client
            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1.0)
                conn.request("GET", "/health")
                resp = conn.getresponse()
                data = resp.read()
                conn.close()
                if 200 <= resp.status < 300:
                    import json
                    try:
                        return json.loads(data.decode("utf-8"))
                    except Exception:
                        return {"status": "ONLINE"}
                return {"status": "OFFLINE"}
            except Exception:
                return {"status": "OFFLINE"}

        return {
            "dashboard_service": probe(modular_settings.dashboard_port),
            "health_service": probe(modular_settings.health_port),
            "camera_service": probe(modular_settings.camera_port),
            "ai_service": probe(modular_settings.ai_port),
            "database_service": probe(modular_settings.database_port),
            "notification_service": probe(modular_settings.notifications_port),
        }

    @app.post("/api/system/alarm/{alarm_id}/ack")
    def acknowledge_alarm(alarm_id: int) -> dict[str, Any]:
        updated = alarm_manager.acknowledge(alarm_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Alarm not found.")
        return {"status": "acknowledged", "id": alarm_id}

    @app.get("/api/system/history")
    def system_history(hours: int = 24, limit: int = 500) -> list[dict[str, Any]]:
        return health_monitor.history(hours=hours, limit=limit)

    @app.post("/api/label")
    def label(request: LabelRequest) -> dict[str, str]:
        try:
            saved = engine.confirm_label(request.operator_label, station=request.station, label_source="WEB_CONFIRM")
        except Exception as error:  # noqa: BLE001 - API reports operator-safe error text
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"metadata_path": str(saved.metadata_path)}

    @app.post("/api/operator-label")
    def operator_label(request: LabelRequest) -> dict[str, str]:
        return label(request)

    @app.post("/api/label/override")
    def label_override(request: OverrideLabelRequest) -> dict[str, str]:
        try:
            saved = engine.override_label(
                request.operator_label,
                station=request.station,
                override_reason=request.override_reason,
            )
        except Exception as error:  # noqa: BLE001 - API reports operator-safe error text
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"metadata_path": str(saved.metadata_path)}

    @app.post("/api/upload")
    async def upload_inspection(station: str = "S1", file: UploadFile = File(...)) -> dict[str, Any]:
        payload = await file.read()
        image_array = np.frombuffer(payload, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="Uploaded file is not a readable image.")
        record = engine.inspect_image(image, file.filename or "uploaded-image", station=station)
        return {
            "station": station,
            "decision": record.decision.value,
            "serial_number": record.serial_number,
            "latest": engine.station_status(station),
        }

    @app.post("/api/upload-video")
    async def upload_video(station: str = "S1", file: UploadFile = File(...), _: dict[str, Any] = Depends(_require_role(ROLE_OPERATOR))) -> dict[str, Any]:
        import os
        ext = Path(file.filename or "video.mp4").suffix or ".mp4"
        os.makedirs("outputs", exist_ok=True)
        video_path = Path("outputs") / f"uploaded_video_{station}{ext}"
        try:
            with open(video_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):
                    buffer.write(chunk)
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Failed to save video: {error}")
        from camera.sources import VideoFileSource
        engine.stop()
        engine.camera_source = VideoFileSource(video_path, loop=True)
        engine.start()
        return {
            "status": "success",
            "camera_name": engine.camera_source.name,
            "filename": file.filename,
        }

    @app.post("/api/reset-camera")
    def reset_camera(station: str = "S1", _: dict[str, Any] = Depends(_require_role(ROLE_SUPERVISOR))) -> dict[str, Any]:
        from camera.sources import UsbCameraSource
        engine.stop()
        engine.camera_source = UsbCameraSource(0)
        engine.start()
        return {
            "status": "success",
            "camera_name": engine.camera_source.name,
        }

    @app.post("/api/start-inspection")
    def start_inspection(_: dict[str, Any] = Depends(_require_role(ROLE_OPERATOR))) -> dict[str, bool]:
        engine.start()
        return {"running": True}

    @app.post("/api/start-part")
    def start_part(__: StartPartRequest | None = None, _: dict[str, Any] = Depends(_require_role(ROLE_OPERATOR))) -> dict[str, str]:
        return {"part_id": engine.reset_part()}

    @app.post("/api/stop-inspection")
    def stop_inspection(_: dict[str, Any] = Depends(_require_role(ROLE_OPERATOR))) -> dict[str, bool]:
        engine.stop()
        return {"running": False}

    @app.post("/api/reset-part")
    def reset_part(_: dict[str, Any] = Depends(_require_role(ROLE_OPERATOR))) -> dict[str, str]:
        return {"part_id": engine.reset_part()}

    @app.post("/api/reset")
    def reset(_: dict[str, Any] = Depends(_require_role(ROLE_OPERATOR))) -> dict[str, str]:
        return {"part_id": engine.reset_part()}

    @app.post("/api/shutdown")
    def shutdown(_: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> dict[str, str]:
        engine.stop()
        return {"status": "shutdown_requested"}

    @app.get("/stream/station1")
    def stream_station1() -> StreamingResponse:
        return StreamingResponse(engine.mjpeg_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

    @app.get("/image/station1/{image_type}")
    def image_station1(image_type: str) -> Response:
        image = engine.latest_jpeg("S1", image_type=image_type)
        if image is None:
            raise HTTPException(status_code=404, detail="No station image available.")
        return Response(content=image, media_type="image/jpeg")

    # ─── Calibration Endpoints ────────────────────────────────────────────────

    @app.get("/api/calibration/status")
    def calibration_status(camera_id: str = "CAM01") -> dict[str, Any]:
        """Return current calibration status for a camera."""
        if not engine.storage_available or engine.storage is None:
            return {"calibrated": False, "storage": "OFFLINE"}
        cal = engine.storage.get_active_calibration(camera_id)
        if cal:
            cal_date = cal["calibration_date"]
            if hasattr(cal_date, "isoformat"):
                cal_date = cal_date.isoformat()
            return {
                "calibrated": True,
                "camera_id": cal["camera_id"],
                "calibration_date": cal_date,
                "mm_per_pixel": cal["mm_per_pixel"],
                "reference_od_mm": cal["reference_od_mm"],
                "reference_hole_mm": cal["reference_hole_mm"],
            }
        return {"calibrated": False}

    @app.post("/api/calibration/capture")
    async def calibration_capture(file: UploadFile = File(...)) -> dict[str, Any]:
        """Upload an image for calibration circle detection. Returns pixel measurements + overlay image."""
        from services.calibration.circle_detector import detect_calibration_circles
        payload = await file.read()
        image_array = np.frombuffer(payload, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            # Try to grab current live frame from engine
            if engine.latest_frame is not None:
                image = engine.latest_frame.copy()
            else:
                raise HTTPException(status_code=400, detail="Could not decode image.")

        result = detect_calibration_circles(image)
        if result is None:
            raise HTTPException(status_code=422, detail="Could not detect calibration circles in image. Ensure disc is well-lit and centered.")

        ok, encoded = cv2.imencode(".jpg", result["overlay"])
        if not ok:
            raise HTTPException(status_code=500, detail="Could not encode overlay image.")
        overlay_b64 = base64.b64encode(encoded.tobytes()).decode()

        return {
            "outer_diameter_px": result["outer_diameter_px"],
            "hole_diameter_px": result["hole_diameter_px"],
            "overlay_image": f"data:image/jpeg;base64,{overlay_b64}",
        }

    @app.post("/api/calibration/capture-live")
    def calibration_capture_live() -> dict[str, Any]:
        """Capture the current live camera frame and run circle detection."""
        from services.calibration.circle_detector import detect_calibration_circles
        if engine.latest_frame is None:
            raise HTTPException(status_code=503, detail="No live frame available. Start the inspection engine first.")
        image = engine.latest_frame.copy()
        result = detect_calibration_circles(image)
        if result is None:
            raise HTTPException(status_code=422, detail="Could not detect calibration circles. Ensure disc is well-lit and centered.")
        ok, encoded = cv2.imencode(".jpg", result["overlay"])
        if not ok:
            raise HTTPException(status_code=500, detail="Could not encode overlay image.")
        overlay_b64 = base64.b64encode(encoded.tobytes()).decode()
        return {
            "outer_diameter_px": result["outer_diameter_px"],
            "hole_diameter_px": result["hole_diameter_px"],
            "overlay_image": f"data:image/jpeg;base64,{overlay_b64}",
        }

    @app.post("/api/calibration/save")
    def calibration_save(request: CalibrationSaveRequest) -> dict[str, Any]:
        """Calculate mm_per_pixel and persist the calibration."""
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline. Cannot save calibration.")
        mm_per_pixel = request.reference_od_mm / request.outer_diameter_px
        record_id = engine.storage.repository.save_calibration(
            camera_id=request.camera_id,
            mm_per_pixel=mm_per_pixel,
            reference_od_mm=request.reference_od_mm,
            reference_hole_mm=request.reference_hole_mm,
        )
        return {
            "status": "success",
            "record_id": record_id,
            "mm_per_pixel": round(mm_per_pixel, 6),
            "camera_id": request.camera_id,
        }

    @app.get("/api/calibration/history")
    def calibration_history(camera_id: str = "CAM01") -> list[dict[str, Any]]:
        """Return all calibration records for a camera."""
        if not engine.storage_available or engine.storage is None:
            return []
        records = engine.storage.repository.get_calibration_history(camera_id)
        for rec in records:
            if hasattr(rec.get("calibration_date"), "isoformat"):
                rec["calibration_date"] = rec["calibration_date"].isoformat()
        return records

    @app.delete("/api/calibration/{record_id}")
    def calibration_delete(record_id: int) -> dict[str, str]:
        """Deactivate a calibration record."""
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline.")
        with engine.storage.repository._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE camera_calibration SET active = FALSE WHERE id = %s", (record_id,))
        return {"status": "deleted", "record_id": str(record_id)}

    @app.post("/api/calibration/validate")
    def calibration_validate(request: CalibrationValidateRequest) -> dict[str, Any]:
        """Validate the active calibration against a known reference disc."""
        from services.calibration.circle_detector import detect_calibration_circles
        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline.")
        cal = engine.storage.get_active_calibration(request.camera_id)
        if not cal:
            raise HTTPException(status_code=404, detail="No active calibration found.")
        if engine.latest_frame is None:
            raise HTTPException(status_code=503, detail="No live frame available.")
        result = detect_calibration_circles(engine.latest_frame.copy())
        if result is None:
            raise HTTPException(status_code=422, detail="Could not detect circles in live frame.")
        validation = validate_calibration(
            measured_px=result["outer_diameter_px"],
            active_mm_per_pixel=cal["mm_per_pixel"],
            expected_mm=request.reference_od_mm,
            tolerance=request.tolerance,
        )
        ok, encoded = cv2.imencode(".jpg", result["overlay"])
        if ok:
            validation["overlay_image"] = f"data:image/jpeg;base64,{base64.b64encode(encoded.tobytes()).decode()}"
        return validation

    @app.get("/api/calibration/report")
    def calibration_report(camera_id: str = "CAM01") -> Response:
        """Generate and download a PDF calibration report."""
        try:
            from fpdf import FPDF
        except ImportError:
            raise HTTPException(status_code=501, detail="PDF library not available. Install fpdf2.")

        if not engine.storage_available or engine.storage is None:
            raise HTTPException(status_code=503, detail="Storage is offline.")
        records = engine.storage.repository.get_calibration_history(camera_id)
        active_cal = engine.storage.get_active_calibration(camera_id)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_fill_color(20, 25, 40)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 12, "Camera Calibration Report", new_x="LMARGIN", new_y="NEXT", fill=True, align="C")
        pdf.ln(4)

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, f"Camera ID: {camera_id}", new_x="LMARGIN", new_y="NEXT")

        if active_cal:
            cal_date = active_cal["calibration_date"]
            if hasattr(cal_date, "isoformat"):
                cal_date = cal_date.isoformat()
            pdf.set_fill_color(220, 255, 220)
            pdf.cell(0, 8, f"Status: CALIBRATED", new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.cell(0, 8, f"Last Calibration: {cal_date}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"Scale Factor: {active_cal['mm_per_pixel']:.6f} mm/pixel", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"Reference OD: {active_cal['reference_od_mm']} mm", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"Reference Hole: {active_cal['reference_hole_mm']} mm", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_fill_color(255, 200, 200)
            pdf.cell(0, 8, "Status: NOT CALIBRATED", new_x="LMARGIN", new_y="NEXT", fill=True)

        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Calibration History", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(200, 200, 200)
        col_w = [10, 45, 35, 30, 30, 20]
        headers = ["ID", "Date", "mm/pixel", "Ref OD (mm)", "Ref Hole (mm)", "Active"]
        for h, w in zip(headers, col_w):
            pdf.cell(w, 7, h, border=1, fill=True)
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for rec in records:
            cd = rec.get("calibration_date", "")
            if hasattr(cd, "isoformat"):
                cd = cd.isoformat()[:19]
            row = [
                str(rec.get("id", "")),
                str(cd),
                f"{rec.get('mm_per_pixel', 0):.6f}",
                str(rec.get("reference_od_mm", "")),
                str(rec.get("reference_hole_mm", "")),
                "YES" if rec.get("active") else "no",
            ]
            for val, w in zip(row, col_w):
                pdf.cell(w, 7, val, border=1)
            pdf.ln()

        buf = io.BytesIO()
        pdf.output(buf)
        buf.seek(0)
        return Response(
            content=buf.read(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=calibration_report_{camera_id}.pdf"},
        )

    # ─── AI Data Cleanup ───────────────────────────────────────────────────────

    @app.get("/api/admin/cleanup/status")
    def cleanup_status(_: dict[str, Any] = Depends(_require_role(ROLE_ADMIN))) -> dict[str, Any]:
        """Get current dataset size and inspection record count."""
        from config.settings import DATASET_DIR, OUTPUT_DIR
        from pathlib import Path

        def count_items(path: Path) -> int:
            if not path.exists():
                return 0
            return sum(1 for _ in path.rglob("*") if _.is_file())

        def get_size_mb(path: Path) -> float:
            if not path.exists():
                return 0.0
            total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            return total / (1024 * 1024)

        good_count = count_items(DATASET_DIR / "good")
        defect_count = count_items(DATASET_DIR / "defect")
        passed_count = count_items(OUTPUT_DIR / "passed")
        failed_count = count_items(OUTPUT_DIR / "failed")

        dataset_size = get_size_mb(DATASET_DIR / "good") + get_size_mb(DATASET_DIR / "defect")
        outputs_size = get_size_mb(OUTPUT_DIR / "passed") + get_size_mb(OUTPUT_DIR / "failed")

        inspection_count = 0
        if engine.storage_available and engine.storage is not None:
            try:
                with engine.storage.repository._connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM inspection_records")
                        row = cur.fetchone()
                        inspection_count = row[0] if row else 0
            except Exception:
                pass

        return {
            "training_data": {
                "good_images": good_count,
                "defect_images": defect_count,
                "total_images": good_count + defect_count,
                "size_mb": round(dataset_size, 2),
            },
            "inspection_outputs": {
                "passed_images": passed_count,
                "failed_images": failed_count,
                "total_images": passed_count + failed_count,
                "size_mb": round(outputs_size, 2),
            },
            "database": {
                "inspection_records": inspection_count,
            },
        }

    class CleanupRequest(BaseModel):
        clean_dataset: bool = True
        clean_outputs: bool = False
        clean_database: bool = False

    @app.post("/api/admin/cleanup/execute")
    def cleanup_execute(
        request: CleanupRequest,
        _: dict[str, Any] = Depends(_require_role(ROLE_ADMIN)),
    ) -> dict[str, Any]:
        """Execute cleanup of AI training data and optionally inspection history."""
        import subprocess
        from config.settings import PROJECT_ROOT

        # Build cleanup command
        cleanup_script = PROJECT_ROOT / "scripts" / "cleanup_ai_data.py"
        cmd = ["python", str(cleanup_script)]

        if request.clean_dataset:
            cmd.append("--dataset-only")
        elif request.clean_outputs:
            cmd.append("--outputs-only")
        elif request.clean_database:
            cmd.extend(["--full", "--keep-database"])

        if request.clean_dataset and request.clean_outputs and request.clean_database:
            cmd = ["python", str(cleanup_script), "--full"]
        elif request.clean_dataset and request.clean_outputs:
            cmd = ["python", str(cleanup_script)]
            # Run both (dataset already in cmd)

        cmd.append("--confirm")  # Skip confirmation prompts

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300.0,
                cwd=str(PROJECT_ROOT),
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0

            return {
                "status": "success" if success else "error",
                "output": output,
                "return_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "output": "Cleanup operation timed out (>5 minutes)",
                "return_code": 124,
            }
        except Exception as e:
            return {
                "status": "error",
                "output": str(e),
                "return_code": 1,
            }

    # ─── WebSocket ────────────────────────────────────────────────────────────

    @app.websocket("/ws/logs")
    async def websocket_logs(websocket: WebSocket) -> None:
        await websocket.accept()
        last_index = 0
        try:
            while True:
                logs_snapshot = engine.recent_logs(300)
                new_logs = logs_snapshot[last_index:]
                if new_logs:
                    for entry in new_logs:
                        await websocket.send_json({"message": entry})
                    last_index = len(logs_snapshot)
                await asyncio.sleep(0.5)
        except (WebSocketDisconnect, asyncio.CancelledError):
            return

    @app.on_event("startup")
    async def _startup() -> None:
        health_monitor.start()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        health_monitor.stop()

    app.state.engine = engine
    app.state.alarm_manager = alarm_manager
    app.state.health_monitor = health_monitor
    return app
