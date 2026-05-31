"""GUI-independent inspection workflow service."""

from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import cv2
import numpy as np

from automation.plc import PLCController, SimulatedPLCController
from automation.workflow import SingleStationInspectionController, StationRecord
from camera.sources import CameraSource, UsbCameraSource
from config.settings import MODE_DATA_COLLECTION, load_tolerances
from dataset.collector import DatasetCollector, DatasetSaveResult
from dataset.label_manager import LabelManager
from storage.service import InspectionStorageService
from vision.anomaly_scoring import anomaly_score, assisted_prediction
from vision.preprocessing import preprocess_image, create_foreground_mask
from vision.circle_detection import detect_outer_circle


@dataclass(slots=True)
class PendingLabel:
    part_id: str
    station: str
    record: StationRecord
    system_prediction: str
    anomaly_score: float


class InspectionEngine:
    """Run inspection without depending on PySide."""

    def __init__(
        self,
        *,
        plc: PLCController | None = None,
        storage: InspectionStorageService | None = None,
        dataset_collector: DatasetCollector | None = None,
        camera_source: CameraSource | None = None,
        inspection_mode: str = MODE_DATA_COLLECTION,
    ) -> None:
        self.plc = plc or SimulatedPLCController()
        self.storage = storage
        self.storage_available = False
        if self.storage is not None:
            try:
                self.storage.initialize()
                self.storage_available = True
            except Exception:
                self.storage_available = False
        self.controller = SingleStationInspectionController(
            self.plc,
            part_id_factory=self.storage.next_part_id if self.storage_available and self.storage else None,
        )
        self.dataset_collector = dataset_collector or DatasetCollector()
        self.label_manager = LabelManager(self.dataset_collector.dataset_root)
        self.camera_source = camera_source or UsbCameraSource(0)
        self.inspection_mode = inspection_mode
        self.latest_frame: np.ndarray | None = None
        self.latest_overlay: np.ndarray | None = None
        self.latest_record: StationRecord | None = None
        self.latest_station: str = "S1"
        self.pending_label: PendingLabel | None = None
        self.running = False
        self.disc_active = False
        self.disc_inspected = False
        self.empty_frames = 0
        self.last_disc_x = -1
        self.logs: list[str] = []
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self.last_frame_ts = 0.0
        self.frame_count = 0
        self.frame_drop_count = 0
        self.recovery_attempts = 0
        self.processing_sleep_seconds = 0.04
        self.cycle_times_ms: list[int] = []

    def start(self) -> None:
        if self.running:
            return
        self.camera_source.open()
        self.running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        self._log("Inspection engine started.")

    def stop(self) -> None:
        self.running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self.camera_source.close()
        self._log("Inspection engine stopped.")

    def reset_part(self) -> str:
        part = self.controller.start_new_part()
        with self._lock:
            self.pending_label = None
        self._log(f"Started new part: {part.part_id}")
        return part.part_id

    def inspect_image(self, image: np.ndarray, source_name: str = "manual", station: str = "S1") -> StationRecord:
        record = self.controller.inspect_current_part(image, source_name)
        
        # Apply calibration scaling
        if self.storage_available and self.storage is not None:
            active_cal = self.storage.get_active_calibration(self.camera_source.name)
            if active_cal and record.inspection_result and record.inspection_result.measurements:
                mm_per_pixel = active_cal["mm_per_pixel"]
                scaled = {}
                for key, val in record.inspection_result.measurements.items():
                    if isinstance(val, (int, float)):
                        scaled[key] = round(val * mm_per_pixel, 3)
                    elif isinstance(val, tuple) and len(val) == 2:
                        scaled[key] = (round(val[0] * mm_per_pixel, 3), round(val[1] * mm_per_pixel, 3))
                    else:
                        scaled[key] = val
                record.inspection_result.measurements = scaled
                
        score = anomaly_score(record.inspection_result) if record.inspection_result else 100.0
        prediction = assisted_prediction(record.inspection_result) if record.inspection_result else "DEFECT"
        if self.storage_available and self.storage is not None:
            self.storage.persist_station_record(
                physical_part_id=self.controller.current_part.part_id,
                stage="SINGLE",
                record=record,
                final_disposition=self.controller.current_part.final_disposition,
                overlay_path=None,
                inspection_mode=self.inspection_mode,
                cycle_time_ms=record.cycle_time_ms,
            )
        with self._lock:
            self.latest_frame = image.copy()
            self.latest_overlay = record.overlay_image.copy() if record.overlay_image is not None else None
            self.latest_record = record
            self.latest_station = "S1"
            self.pending_label = PendingLabel(
                part_id=self.controller.current_part.part_id,
                station="S1",
                record=record,
                system_prediction=prediction,
                anomaly_score=score,
            )
        self._log(f"Inspection complete: prediction={prediction}, score={score}, cycle_time={record.cycle_time_ms}ms")
        if record.cycle_time_ms is not None:
            self.cycle_times_ms.append(record.cycle_time_ms)
            self.cycle_times_ms = self.cycle_times_ms[-300:]
        return record

    def confirm_label(self, operator_label: str, station: str | None = None) -> DatasetSaveResult:
        with self._lock:
            pending = self.pending_label
        if pending is None:
            raise RuntimeError("No inspection is waiting for operator confirmation.")
        if station is not None and self._station_code(station) != self._station_code(pending.station):
            raise RuntimeError(f"No pending label for station {station}.")
        record = pending.record
        if record.raw_image is None or record.inspection_result is None:
            raise RuntimeError("Pending inspection does not contain image evidence.")
        result = self.dataset_collector.save_labeled_inspection(
            part_id=pending.part_id,
            station=pending.station,
            source_name=record.source_name,
            original_image=record.raw_image,
            overlay_image=record.overlay_image,
            inspection_result=record.inspection_result,
            system_prediction=pending.system_prediction,
            operator_label=operator_label,
            serial_number=record.serial_number,
            camera_source=record.source_name,
            inspected_at=record.inspected_at or datetime.now().astimezone(),
            anomaly_score=pending.anomaly_score,
            inspection_mode=self.inspection_mode,
        )
        self._log(f"Operator label saved: {operator_label}")
        with self._lock:
            self.pending_label = None
        return result

    def status(self) -> dict[str, Any]:
        pending = self.pending_label
        return {
            "running": self.running,
            "mode": self.inspection_mode,
            "part_id": self.controller.current_part.part_id,
            "plc": asdict(self.plc.read_status()),
            "storage": "ONLINE" if self.storage_available else "OFFLINE",
            "pending_label": pending is not None,
            "log_count": len(self.logs),
            "camera_name": self.camera_source.name,
        }

    def latest_inspection(self) -> dict[str, Any]:
        record = self.latest_record
        pending = self.pending_label
        return {
            "part_id": self.controller.current_part.part_id,
            "decision": record.decision.value if record else "WAITING",
            "source_name": record.source_name if record else None,
            "system_prediction": pending.system_prediction if pending else None,
            "anomaly_score": pending.anomaly_score if pending else None,
            "defects": record.inspection_result.defects if record and record.inspection_result else [],
            "measurements": record.inspection_result.measurements if record and record.inspection_result else {},
            "cycle_time_ms": record.cycle_time_ms if record else None,
            "inspection_mode": self.inspection_mode,
        }

    def station_status(self, station: str) -> dict[str, Any]:
        """Return dashboard-ready state for one station slot."""
        station_code = self._station_code(station)
        if station_code != "S1":
            raise ValueError("Only Station 1 / S1 is supported in single station mode.")
        record = self.latest_record
        pending = self.pending_label
        part = self.controller.current_part
        return {
            "station": "S1",
            "name": "Inspection Station",
            "active": True,
            "part_id": part.part_id,
            "serial_number": record.serial_number if record else None,
            "decision": record.decision.value if record else "WAITING",
            "disposition": part.final_disposition.value,
            "source_name": record.source_name if record else None,
            "system_prediction": pending.system_prediction if pending else None,
            "anomaly_score": pending.anomaly_score if pending else None,
            "pending_label": pending is not None,
            "defects": record.inspection_result.defects if record and record.inspection_result else [],
            "measurements": record.inspection_result.measurements if record and record.inspection_result else {},
            "stream_url": "/stream/station1",
            "captured_image_url": "/image/station1/overlay",
            "cycle_time_ms": record.cycle_time_ms if record else None,
        }

    def camera_status(self) -> list[dict[str, Any]]:
        return [{"name": self.camera_source.name, "running": self.running}]

    def dataset_stats(self) -> dict[str, float | int]:
        return self.label_manager.stats().as_dict()

    def metrics(self) -> dict[str, Any]:
        counters = self.controller.counters
        dataset_stats = self.dataset_stats()
        avg_cycle = (sum(self.cycle_times_ms) / len(self.cycle_times_ms)) if self.cycle_times_ms else None
        return {
            "total_parts": counters.total_parts_detected,
            "passed_parts": counters.passed,
            "rejected_parts": counters.rejected,
            "station1_passed": counters.passed,
            "station1_rejected": counters.rejected,
            "dataset": dataset_stats,
            "average_cycle_time_ms": round(avg_cycle, 2) if avg_cycle is not None else None,
        }

    def health_snapshot(self) -> dict[str, Any]:
        now = time.time()
        frame_age = (now - self.last_frame_ts) if self.last_frame_ts > 0 else None
        fps = 0.0
        if self.running and self.last_frame_ts > 0:
            fps = min(1.0 / max(self.processing_sleep_seconds, 0.001), 120.0)
        avg_cycle = (sum(self.cycle_times_ms) / len(self.cycle_times_ms)) if self.cycle_times_ms else None
        counters = self.controller.counters
        parts_total = counters.total_parts_detected
        ppm = float(parts_total) if parts_total < 60 else float(parts_total) / 2.0
        return {
            "inspection_running": self.running,
            "current_mode": self.inspection_mode,
            "parts_per_minute": round(ppm, 2),
            "average_cycle_time_ms": round(avg_cycle, 2) if avg_cycle is not None else None,
            "inspection_latency_ms": round((frame_age or 0.0) * 1000.0, 2) if frame_age is not None else None,
            "inference_time_ms": round(avg_cycle * 0.6, 2) if avg_cycle is not None else None,
            "queue_backlog": 0,
            "thread_status": "RUNNING" if self._thread and self._thread.is_alive() else "STOPPED",
            "camera_fps": round(fps, 2),
            "camera_frame_drops": self.frame_drop_count,
            "last_frame_timestamp": datetime.fromtimestamp(self.last_frame_ts).isoformat() if self.last_frame_ts else None,
            "camera_source_name": self.camera_source.name,
            "camera_recovery_attempts": self.recovery_attempts,
            "camera_connected": self.last_frame_ts > 0 and (frame_age is not None and frame_age < 5.0),
        }

    def reduce_processing_rate(self, factor: float = 1.25) -> None:
        self.processing_sleep_seconds = min(0.2, self.processing_sleep_seconds * factor)
        self._log(f"Processing rate reduced. Loop delay={self.processing_sleep_seconds:.3f}s")

    def reduce_camera_fps(self, target_fps: float = 15.0) -> bool:
        capture = getattr(self.camera_source, "_capture", None)
        if capture is None:
            return False
        try:
            capture.set(cv2.CAP_PROP_FPS, target_fps)
            self._log(f"Camera FPS reduction requested: target={target_fps}")
            return True
        except Exception:
            return False

    def safe_stop(self) -> None:
        self._log("Emergency safe stop requested.")
        self.stop()

    def save_runtime_state(self) -> dict[str, Any]:
        snapshot = {
            "running": self.running,
            "mode": self.inspection_mode,
            "part_id": self.controller.current_part.part_id,
            "last_frame_timestamp": self.last_frame_ts,
        }
        self._log("Runtime state snapshot captured.")
        return snapshot

    def recover_camera(self) -> bool:
        self.recovery_attempts += 1
        try:
            self.camera_source.close()
            self.camera_source.open()
            self._log(f"Camera recovery attempt {self.recovery_attempts} succeeded.")
            return True
        except Exception as error:
            self._log(f"Camera recovery attempt {self.recovery_attempts} failed: {error}")
            return False

    def recent_history(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.storage_available or self.storage is None:
            return []
        return [record.__dict__ for record in self.storage.recent(limit)]

    def recent_logs(self, limit: int = 100) -> list[str]:
        return self.logs[-limit:]

    def mjpeg_frames(self):
        import time
        while True:
            if self.running:
                frame = self.latest_frame
            else:
                frame = self.latest_overlay if self.latest_overlay is not None else self.latest_frame
            
            if frame is None:
                frame = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "Waiting for camera", (150, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (220, 220, 220), 2)
            ok, encoded = cv2.imencode(".jpg", frame)
            if ok:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n"
            time.sleep(0.04)

    def latest_jpeg(self, station: str, image_type: str = "overlay") -> bytes | None:
        if self._station_code(station) != "S1":
            return None
        frame = self.latest_overlay if image_type == "overlay" else self.latest_frame
        if frame is None:
            return None
        ok, encoded = cv2.imencode(".jpg", frame)
        return encoded.tobytes() if ok else None

    def _capture_loop(self) -> None:
        from pathlib import Path
        self.disc_active = False
        self.disc_inspected = False
        self.empty_frames = 0
        self.last_disc_x = -1

        while self.running:
            frame = self.camera_source.read()
            if frame is not None:
                self.frame_count += 1
                self.last_frame_ts = time.time()
                processed_frame = frame.copy()
                width = processed_frame.shape[1]
                if width > 800:
                    center_x = width // 2
                    processed_frame = processed_frame[:, center_x - 300 : center_x + 300]
                    width = 600
                
                try:
                    _, blurred = preprocess_image(processed_frame)
                    mask = create_foreground_mask(blurred)
                    outer = detect_outer_circle(mask, blurred)
                except Exception:
                    outer = None
                
                radius_limits = load_tolerances().get("outer_radius_px", {})
                valid_disk = bool(outer and radius_limits.get("min", 0) <= outer.radius <= radius_limits.get("max", 9999))
                
                trigger_left = width // 2 - 140
                trigger_right = width // 2 + 140
                
                display_frame = processed_frame.copy()
                cv2.line(display_frame, (trigger_left, 0), (trigger_left, display_frame.shape[0]), (0, 255, 255), 2)
                cv2.line(display_frame, (trigger_right, 0), (trigger_right, display_frame.shape[0]), (0, 255, 255), 2)
                cv2.putText(display_frame, "TRIGGER ZONE", (trigger_left + 40, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                if valid_disk:
                    self.empty_frames = 0
                    disc_x = outer.center[0]
                    if not self.disc_active:
                        self.disc_active = True
                        self.disc_inspected = False
                    self.last_disc_x = disc_x
                    
                    trigger_active = trigger_left < disc_x < trigger_right
                    trigger_text = "TRIGGER: YES" if trigger_active else "TRIGGER: NO"
                    trigger_color = (0, 200, 0) if trigger_active else (200, 200, 50)
                    cv2.putText(display_frame, trigger_text, (max(10, width - 220), 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, trigger_color, 2)
                    
                    # Highlight the detected disk circle on display
                    cv2.circle(display_frame, outer.center, outer.radius, (255, 0, 0), 2)
                    
                    if trigger_active and not self.disc_inspected:
                        # Determine source name
                        source_name = self.camera_source.name
                        if hasattr(self.camera_source, 'source') and isinstance(self.camera_source.source, str):
                            source_name = f"Video: {Path(self.camera_source.source).name}"
                        
                        # Inspect the clean frame (without display trigger lines)
                        self.inspect_image(processed_frame, source_name=source_name, station="S1")
                        self.disc_inspected = True
                    
                    if self.disc_active and (disc_x < trigger_left - 120 or disc_x > trigger_right + 120):
                        self.disc_active = False
                        self.disc_inspected = False
                else:
                    self.empty_frames += 1
                    if self.empty_frames > 10:
                        self.disc_active = False
                        self.disc_inspected = False
                        self.empty_frames = 0
                        self.last_disc_x = -1
                
                with self._lock:
                    self.latest_frame = display_frame
            else:
                self.frame_drop_count += 1
            threading.Event().wait(self.processing_sleep_seconds)

    def _log(self, message: str) -> None:
        self.logs.append(f"{datetime.now().isoformat(timespec='seconds')} {message}")
        self.logs = self.logs[-300:]

    @staticmethod
    def _station_code(station: str) -> str:
        value = station.strip().lower()
        if value in {"2", "s2", "station2", "station 2"}:
            return "S2"
        return "S1"
