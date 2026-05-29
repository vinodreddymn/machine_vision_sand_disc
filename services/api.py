"""FastAPI backend and browser dashboard."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.settings import load_tolerances, save_tolerances, SUPPORTED_INSPECTION_MODES
from services.inspection_engine import InspectionEngine


class LabelRequest(BaseModel):
    operator_label: str
    station: str = "S1"


class StartPartRequest(BaseModel):
    station: str = "S1"


class ModeRequest(BaseModel):
    mode: str



def create_app(engine: InspectionEngine | None = None) -> FastAPI:
    engine = engine or InspectionEngine()
    app = FastAPI(title="DiskVisionInspector API")
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

    @app.get("/api/cameras")
    def cameras() -> list[dict[str, Any]]:
        return engine.camera_status()

    @app.get("/api/inspection/latest")
    def latest() -> dict[str, Any]:
        return engine.latest_inspection()

    @app.get("/api/station1")
    def station1() -> dict[str, Any]:
        return engine.station_status("S1")

    @app.get("/api/config/tolerances")
    def get_tolerances() -> dict[str, Any]:
        return load_tolerances()

    @app.post("/api/config/tolerances")
    def update_tolerances(tolerances: dict[str, Any]) -> dict[str, str]:
        try:
            save_tolerances(tolerances)
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"status": "success"}

    @app.post("/api/config/mode")
    def set_mode(request: ModeRequest) -> dict[str, str]:
        mode_val = request.mode.strip().upper()
        if mode_val not in SUPPORTED_INSPECTION_MODES:
            raise HTTPException(status_code=400, detail=f"Unsupported mode: {request.mode}")
        engine.inspection_mode = mode_val
        return {"mode": engine.inspection_mode}

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

    @app.post("/api/label")
    def label(request: LabelRequest) -> dict[str, str]:
        try:
            saved = engine.confirm_label(request.operator_label, station=request.station)
        except Exception as error:  # noqa: BLE001 - API reports operator-safe error text
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"metadata_path": str(saved.metadata_path)}

    @app.post("/api/operator-label")
    def operator_label(request: LabelRequest) -> dict[str, str]:
        return label(request)

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
    async def upload_video(station: str = "S1", file: UploadFile = File(...)) -> dict[str, Any]:
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
    def reset_camera(station: str = "S1") -> dict[str, Any]:
        from camera.sources import UsbCameraSource
        engine.stop()
        engine.camera_source = UsbCameraSource(0)
        engine.start()
        return {
            "status": "success",
            "camera_name": engine.camera_source.name,
        }

    @app.post("/api/start-inspection")
    def start_inspection() -> dict[str, bool]:
        engine.start()
        return {"running": True}

    @app.post("/api/start-part")
    def start_part(_: StartPartRequest | None = None) -> dict[str, str]:
        return {"part_id": engine.reset_part()}

    @app.post("/api/stop-inspection")
    def stop_inspection() -> dict[str, bool]:
        engine.stop()
        return {"running": False}

    @app.post("/api/reset-part")
    def reset_part() -> dict[str, str]:
        return {"part_id": engine.reset_part()}

    @app.post("/api/reset")
    def reset() -> dict[str, str]:
        return {"part_id": engine.reset_part()}

    @app.post("/api/shutdown")
    def shutdown() -> dict[str, str]:
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

    app.state.engine = engine
    return app
