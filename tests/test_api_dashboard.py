"""API contract tests for the LAN dashboard backend."""

from __future__ import annotations

import cv2
from fastapi.testclient import TestClient

from dataset.collector import DatasetCollector
from services.api import create_app
from services.inspection_engine import InspectionEngine
from tests.test_pipeline import build_synthetic_disk


def _client(tmp_path) -> TestClient:
    engine = InspectionEngine(dataset_collector=DatasetCollector(tmp_path))
    return TestClient(create_app(engine))


def test_dashboard_api_exposes_status_station_metrics_and_logs(tmp_path) -> None:
    client = _client(tmp_path)

    assert client.get("/api/status").status_code == 200
    station = client.get("/api/station1").json()
    metrics = client.get("/api/metrics").json()
    logs = client.get("/api/logs").json()

    assert station["station"] == "S1"
    assert station["decision"] == "WAITING"
    assert metrics["total_parts"] == 0
    assert isinstance(logs, list)


def test_upload_image_then_operator_label_updates_dataset_stats(tmp_path) -> None:
    client = _client(tmp_path)
    ok, encoded = cv2.imencode(".png", build_synthetic_disk())
    assert ok

    upload = client.post(
        "/api/upload?station=S1",
        files={"file": ("good.png", encoded.tobytes(), "image/png")},
    )
    assert upload.status_code == 200
    assert upload.json()["decision"] == "PASS"

    station = client.get("/api/station1").json()
    assert station["system_prediction"] == "GOOD"
    assert station["pending_label"] is True

    label = client.post("/api/operator-label", json={"station": "S1", "operator_label": "GOOD"})
    assert label.status_code == 200
    stats = client.get("/api/dataset/stats").json()
    assert stats["total_good"] == 1


def test_config_endpoints(tmp_path) -> None:
    client = _client(tmp_path)
    
    # Verify getting tolerances
    tols_res = client.get("/api/config/tolerances")
    assert tols_res.status_code == 200
    tols = tols_res.json()
    assert "expected_hole_count" in tols
    
    # Verify setting mode
    mode_res = client.post("/api/config/mode", json={"mode": "PRODUCTION"})
    assert mode_res.status_code == 200
    assert mode_res.json()["mode"] == "PRODUCTION"

    # Verify invalid mode fails
    mode_res_invalid = client.post("/api/config/mode", json={"mode": "INVALID_MODE"})
    assert mode_res_invalid.status_code == 400


def test_video_upload_and_camera_reset(tmp_path) -> None:
    client = _client(tmp_path)
    
    fake_video_data = b"fake video data content"
    from unittest.mock import MagicMock, patch
    with patch("cv2.VideoCapture") as mock_video_capture:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_instance.read.return_value = (False, None)
        mock_video_capture.return_value = mock_instance
        
        upload = client.post(
            "/api/upload-video?station=S1",
            files={"file": ("test_video.mp4", fake_video_data, "video/mp4")},
        )
        assert upload.status_code == 200
        res = upload.json()
        assert res["status"] == "success"
        assert "Video File: uploaded_video_S1.mp4" in res["camera_name"]
        
        status = client.get("/api/status").json()
        assert "Video File: uploaded_video_S1.mp4" in status["camera_name"]
        
        reset = client.post("/api/reset-camera?station=S1")
        assert reset.status_code == 200
        assert "USB Camera 0" in reset.json()["camera_name"]
        
        status_reverted = client.get("/api/status").json()
        assert "USB Camera 0" in status_reverted["camera_name"]


def test_system_health_alarm_endpoints(tmp_path) -> None:
    client = _client(tmp_path)

    health = client.get("/api/system/health")
    assert health.status_code == 200
    body = health.json()
    assert "cpu_usage" in body
    assert "uptime" in body

    devices = client.get("/api/system/devices")
    assert devices.status_code == 200
    assert set(devices.json().keys()) == {"camera", "plc", "database", "network"}

    alarms = client.get("/api/system/alarms")
    assert alarms.status_code == 200
    assert isinstance(alarms.json(), list)

    alarm_history = client.get("/api/system/alarm-history")
    assert alarm_history.status_code == 200
    assert isinstance(alarm_history.json(), list)

    trends = client.get("/api/system/history")
    assert trends.status_code == 200
    assert isinstance(trends.json(), list)
