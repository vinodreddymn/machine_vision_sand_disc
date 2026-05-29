"""FastAPI backend and browser dashboard."""

from __future__ import annotations

import asyncio
import base64
import io
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
from services.calibration.validation import validate_calibration


class LabelRequest(BaseModel):
    operator_label: str
    station: str = "S1"


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

    app.state.engine = engine
    return app

