"""Main application window for the single-station inspection workflow."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import cv2
from PySide6.QtCore import QDateTime, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from automation.plc import SimulatedPLCController
from automation.workflow import SingleStationInspectionController, StationDecision
from config.settings import KIOSK_MODE, POSTGRES_DSN, load_tolerances
from dataset.collector import DatasetCollector
from gui.control_panel import ControlPanel
from gui.footer_widget import FooterWidget
from gui.header_widget import HeaderWidget
from gui.station_panel import StationPanel
from storage.postgres import PostgresInspectionRepository
from storage.service import InspectionStorageService
from utils.file_utils import save_result_image
from utils.image_utils import load_bgr_image
from vision.circle_detection import detect_outer_circle
from vision.anomaly_scoring import anomaly_score, assisted_prediction
from vision.preprocessing import create_foreground_mask, preprocess_image

LOGGER = logging.getLogger(__name__)
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
STATION_CODE = "SINGLE"


class MainWindow(QMainWindow):
    """Desktop shell for single-station disc inspection."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DiskVisionInspector - Single Station")
        self.setMinimumSize(1280, 720)

        self.storage = InspectionStorageService(PostgresInspectionRepository(POSTGRES_DSN))
        self.storage_available = self._initialize_storage()
        self.dataset_collector = DatasetCollector()
        self.plc = SimulatedPLCController()
        part_id_factory = self.storage.next_part_id if self.storage_available else None
        self.controller = SingleStationInspectionController(self.plc, part_id_factory=part_id_factory)

        self.current_image = None
        self.current_path: Path | None = None
        self.video_capture: cv2.VideoCapture | None = None
        self.video_timer = QTimer(self)
        self.frame_index = 0
        self.empty_frames = 0
        self.last_disc_x = -1
        self.disc_active = False
        self.disc_inspected = False
        self._last_frame_time = 0.0
        self._pending_dataset_record = None
        self._pending_prediction = None
        self._pending_anomaly_score = None

        self.control_panel = ControlPanel()
        self.header_widget = HeaderWidget()
        self.footer_widget = FooterWidget()
        self.station_panel = StationPanel("Single Station - Disc Inspection")
        self.log_console = QPlainTextEdit()
        self.log_console.setObjectName("logConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumBlockCount(300)

        self.part_id_value = QLabel()
        self.decision_value = QLabel()
        self.serial_value = QLabel()
        self.final_value = QLabel()
        self.plc_value = QLabel()
        self.storage_value = QLabel()
        self.total_detected_value = QLabel()
        self.passed_value = QLabel()
        self.rejected_value = QLabel()
        self.dataset_good_value = QLabel()
        self.dataset_defect_value = QLabel()
        self.dataset_corrections_value = QLabel()
        self.dataset_accuracy_value = QLabel()
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)

        self._build_layout()
        self._apply_theme()
        self._connect_signals()
        self.video_timer.timeout.connect(self._advance_video_frame)
        self._apply_display_mode()
        self._update_clock()
        self.clock_timer.start(1000)
        self._refresh_summary()
        self._append_log("System ready. Single-station manual upload mode is active.")

    def _build_layout(self) -> None:
        summary_box = self._build_process_summary()
        metrics_bar = self._build_production_metrics_bar()

        left_column = QWidget()
        left_column.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(14)
        log_title = QLabel("System Log")
        log_title.setObjectName("panelHeading")
        left_layout.addWidget(self.control_panel)
        left_layout.addWidget(log_title)
        left_layout.addWidget(self.log_console)

        content_host = QWidget()
        content_layout = QVBoxLayout(content_host)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)
        content_layout.addWidget(metrics_bar)
        content_layout.addWidget(summary_box)
        content_layout.addWidget(self.station_panel, 1)

        splitter = QSplitter()
        splitter.addWidget(left_column)
        splitter.addWidget(content_host)
        splitter.setSizes([300, 1580])

        workspace_widget = QWidget()
        workspace_widget.setObjectName("workspaceWidget")
        workspace_layout = QVBoxLayout(workspace_widget)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.addWidget(splitter)

        body_widget = QWidget()
        body_widget.setObjectName("bodyWidget")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(14, 14, 14, 14)
        body_layout.setSpacing(14)
        body_layout.addWidget(self.header_widget)
        body_layout.addWidget(workspace_widget, 1)
        body_layout.addWidget(self.footer_widget)
        self.setCentralWidget(body_widget)

    def _connect_signals(self) -> None:
        self.control_panel.new_part_button.clicked.connect(self.start_new_part)
        self.control_panel.upload_media_button.clicked.connect(self.upload_media)
        self.control_panel.confirm_good_button.clicked.connect(lambda: self.confirm_operator_label("GOOD"))
        self.control_panel.mark_defective_button.clicked.connect(lambda: self.confirm_operator_label("DEFECTIVE"))
        self.header_widget.shutdown_button.clicked.connect(self.close)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
        QWidget {
            background-color: #0B1220;
            color: #E5E7EB;
            font-size: 13px;
            font-family: Segoe UI;
        }
        #bodyWidget { background-color: #0B1220; }
        #headerWidget, #footerWidget, #leftPanel, #summaryPanel, #stationPanel, #plcPanel, #timeBox {
            background-color: #111827;
            border: 1px solid #243041;
            border-radius: 8px;
        }
        #metricsBar {
            background-color: #0F172A;
            border: 2px solid #334155;
            border-radius: 8px;
        }
        #metricTile {
            background-color: #020617;
            border: 1px solid #243041;
            border-radius: 6px;
        }
        #metricLabel {
            color: #94A3B8;
            font-size: 11px;
            font-weight: 800;
        }
        #metricValue {
            color: #F8FAFC;
            font-size: 36px;
            font-weight: 900;
            qproperty-alignment: AlignCenter;
        }
        #metricValue[metricTone="total"] { color: #93C5FD; }
        #metricValue[metricTone="pass"] { color: #86EFAC; }
        #metricValue[metricTone="fail"] { color: #FCA5A5; }
        #workspaceWidget { background-color: transparent; }
        #logoLabel { background-color: transparent; border: none; }
        #companyTitle {
            color: white;
            font-size: 18px;
            font-weight: 700;
        }
        #systemTitle {
            color: #60A5FA;
            font-size: 14px;
            font-weight: 600;
        }
        #applicationTitle, #mutedText { color: #94A3B8; }
        #separatorLabel { color: #6B7280; }
        #statusCaption {
            color: #94A3B8;
            font-size: 10px;
            font-weight: 700;
        }
        #summaryValue, #plcValue {
            color: #F8FAFC;
            font-weight: 700;
        }
        #plcValue {
            min-height: 24px;
            padding: 2px 8px;
            border-radius: 4px;
            background-color: #0F172A;
            border: 1px solid #334155;
        }
        #clockValue {
            color: #F8FAFC;
            font-size: 13px;
            font-weight: 700;
        }
        #shutdownButton {
            background-color: #DC2626;
            color: white;
            border-radius: 17px;
            font-size: 16px;
            font-weight: bold;
        }
        #shutdownButton:hover { background-color: #EF4444; }
        #panelHeading {
            font-size: 13px;
            font-weight: bold;
            color: #CBD5E1;
        }
        #panelSubheading {
            color: #94A3B8;
            font-size: 12px;
            font-weight: bold;
        }
        QPushButton {
            border: 1px solid transparent;
            border-radius: 6px;
            min-height: 38px;
            padding: 0 12px;
            font-weight: bold;
        }
        #primaryButton {
            background-color: #2563EB;
            border-color: #3B82F6;
        }
        #primaryButton:hover { background-color: #1D4ED8; }
        QPushButton:disabled {
            background-color: #1F2937;
            border-color: #334155;
            color: #64748B;
        }
        QPlainTextEdit, QListWidget {
            background-color: #0B1220;
            border: 1px solid #334155;
            border-radius: 6px;
            selection-background-color: #1D4ED8;
        }
        #imageViewer {
            border: 1px solid #334155;
            border-radius: 6px;
            background-color: #020617;
            color: #64748B;
            font-size: 14px;
        }
        #statusLabel {
            min-height: 42px;
            border-radius: 6px;
            font-size: 20px;
            font-weight: bold;
            qproperty-alignment: AlignCenter;
            background-color: #1F2937;
            border: 1px solid #334155;
        }
        #statusLabel[inspectionState="waiting"] { color: #CBD5E1; }
        #statusLabel[inspectionState="pass"] {
            background-color: #14532D;
            border-color: #22C55E;
            color: #DCFCE7;
        }
        #statusLabel[inspectionState="fail"] {
            background-color: #7F1D1D;
            border-color: #EF4444;
            color: #FEE2E2;
        }
        QListWidget::item {
            padding: 7px 8px;
            border-bottom: 1px solid #162033;
        }
        QSplitter::handle {
            background-color: #0B1220;
            width: 10px;
        }
        """
        )

    def _apply_display_mode(self) -> None:
        """Use kiosk fullscreen or fit to the available desktop area."""
        if KIOSK_MODE:
            self.showFullScreen()
            return
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1600, 900)
            return
        geometry = screen.availableGeometry()
        self.resize(geometry.size())
        self.move(geometry.topLeft())

    def _build_process_summary(self) -> QWidget:
        box = QWidget()
        box.setObjectName("summaryPanel")
        layout = QGridLayout(box)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setVerticalSpacing(8)
        layout.setHorizontalSpacing(18)

        rows = [
            ("PART ID", self.part_id_value),
            ("DECISION", self.decision_value),
            ("SERIAL NUMBER", self.serial_value),
            ("DISPOSITION", self.final_value),
            ("LAST PLC ACTION", self.plc_value),
            ("STORAGE", self.storage_value),
            ("DATASET GOOD", self.dataset_good_value),
            ("DATASET DEFECTIVE", self.dataset_defect_value),
            ("CORRECTIONS", self.dataset_corrections_value),
            ("ACCURACY EST.", self.dataset_accuracy_value),
        ]
        for index, (caption, value) in enumerate(rows):
            row = index // 3
            col = (index % 3) * 2
            layout.addWidget(self._caption(caption), row, col)
            value.setObjectName("summaryValue")
            layout.addWidget(value, row, col + 1)
        return box

    def _build_production_metrics_bar(self) -> QWidget:
        box = QFrame()
        box.setObjectName("metricsBar")
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self._metric_tile("TOTAL DETECTED", self.total_detected_value, "total"))
        layout.addWidget(self._metric_tile("PASSED", self.passed_value, "pass"))
        layout.addWidget(self._metric_tile("FAILED", self.rejected_value, "fail"))
        return box

    @staticmethod
    def _metric_tile(label_text: str, value: QLabel, tone: str) -> QWidget:
        tile = QWidget()
        tile.setObjectName("metricTile")
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        label = QLabel(label_text)
        label.setObjectName("metricLabel")
        value.setObjectName("metricValue")
        value.setProperty("metricTone", tone)
        layout.addWidget(label)
        layout.addWidget(value)
        return tile

    def start_new_part(self) -> None:
        """Reset the inspection station for the next incoming product."""
        self._stop_video()
        part = self.controller.start_new_part()
        self.current_image = None
        self.current_path = None
        self._pending_dataset_record = None
        self._pending_prediction = None
        self._pending_anomaly_score = None
        self._set_label_buttons_enabled(False)
        self.station_panel.clear_station()
        self.disc_active = False
        self.disc_inspected = False
        self.empty_frames = 0
        self._refresh_summary()
        self._append_log(f"Started new part: {part.part_id}")

    def upload_media(self) -> None:
        """Load one image or video manually until a live camera is connected."""
        loaded = self._load_media("Select inspection image or video")
        if loaded is None:
            return
        image, path, is_video = loaded
        self.current_path = path
        self._stop_video()
        if is_video:
            self._start_video(path)
            return
        self.current_image = image
        self.station_panel.show_uploaded_image(image, path.name)
        self._append_log(f"Image loaded: {path.name}")
        self.run_inspection()

    def _start_video(self, path: Path) -> None:
        try:
            self.video_capture = self._open_video_capture(path)
        except ValueError as error:
            QMessageBox.critical(self, "Video load error", str(error))
            self._append_log(str(error))
            return
        first_frame = self._read_video_frame(self.video_capture)
        if first_frame is None:
            QMessageBox.critical(self, "Video load error", f"Unable to read frames from video: {path.name}")
            self._append_log(f"Unable to read frames from video: {path}")
            self._stop_video()
            return
        self.current_image = first_frame
        self.frame_index = 1
        self.station_panel.show_live_feed(first_frame, f"Video: {path.name}")
        self.station_panel.capture_viewer.clear_image("Video loaded. Trigger zone will inspect automatically.")
        self.station_panel.result_panel.clear_results()
        self.video_timer.start(self._video_timer_interval(self.video_capture))
        self._append_log(f"Video loaded: {path.name}")

    def run_inspection(self) -> None:
        """Inspect the current image and issue a final line action."""
        if self.current_image is None or self.current_path is None:
            QMessageBox.information(self, "No image", "Upload an image before inspection.")
            return
        record = self.controller.inspect_current_part(self.current_image, self.current_path.name)
        self.station_panel.show_record(record)
        overlay_path = self._save_station_overlay(record, self.current_path.stem)
        self._persist_station_record(record, overlay_path)
        self._prepare_label_confirmation(record)
        self._refresh_summary()
        self._append_log(self._prediction_log_line(record))
        LOGGER.info("Inspection complete for %s: %s", self.current_path.name, record.decision.value)

    def confirm_operator_label(self, operator_label: str) -> None:
        """Persist the operator-confirmed ground-truth label."""
        record = self._pending_dataset_record
        if record is None or record.raw_image is None or record.inspection_result is None:
            QMessageBox.information(self, "No pending label", "Run an inspection before confirming a label.")
            return
        result = self.dataset_collector.save_labeled_inspection(
            part_id=self.controller.current_part.part_id,
            station=STATION_CODE,
            source_name=record.source_name,
            original_image=record.raw_image,
            overlay_image=record.overlay_image,
            inspection_result=record.inspection_result,
            system_prediction=self._pending_prediction or record.decision.value,
            operator_label=operator_label,
            serial_number=record.serial_number,
            camera_source=record.source_name,
            inspected_at=record.inspected_at,
            anomaly_score=self._pending_anomaly_score,
        )
        self._append_log(f"Dataset label saved: {operator_label} -> {saved.metadata_path}")
        self._pending_dataset_record = None
        self._set_label_buttons_enabled(False)
        self._refresh_summary()

    def _save_station_overlay(self, record, stem: str) -> str | None:
        if record.overlay_image is None:
            return None
        saved = save_result_image(record.overlay_image, record.decision is StationDecision.PASS, f"single_station_{stem}")
        self._append_log(f"Overlay saved: {saved.name}")
        return str(saved)

    def _persist_station_record(self, record, overlay_path: str | None) -> None:
        if not self.storage_available:
            return
        serial = self.storage.persist_station_record(
            physical_part_id=self.controller.current_part.part_id,
            stage=STATION_CODE,
            record=record,
            final_disposition=self.controller.current_part.final_disposition,
            overlay_path=overlay_path,
        )
        self._append_log(f"Inspection persisted as {serial}")

    def _refresh_summary(self) -> None:
        part = self.controller.current_part
        record = part.station
        self.part_id_value.setText(part.part_id)
        self.decision_value.setText(record.decision.value)
        self.serial_value.setText(record.serial_number or "-")
        self.final_value.setText(part.final_disposition.value)
        self.plc_value.setText(self.plc.last_action)
        self.storage_value.setText("ONLINE" if self.storage_available else "OFFLINE")
        dataset_stats = self.dataset_collector.label_manager.stats()
        self.dataset_good_value.setText(str(dataset_stats.total_good))
        self.dataset_defect_value.setText(str(dataset_stats.total_defective))
        self.dataset_corrections_value.setText(str(dataset_stats.operator_corrections))
        self.dataset_accuracy_value.setText(f"{dataset_stats.system_accuracy_estimate:.1f}%")

        self.footer_widget.set_values(
            part_id=part.part_id,
            storage_status="ONLINE" if self.storage_available else "OFFLINE",
            mode=self.plc.read_status().mode.value,
        )
        self.header_widget.show_plc_status(self.plc.read_status())

        counters = self.controller.counters
        self.total_detected_value.setText(str(counters.total_parts_detected))
        self.passed_value.setText(str(counters.passed))
        self.rejected_value.setText(str(counters.rejected))

    def _load_media(self, title: str):
        path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "Images and Videos (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.mp4 *.mov *.avi *.mkv)",
        )
        if not path:
            return None
        path_obj = Path(path)
        if path_obj.suffix.lower() in VIDEO_EXTENSIONS:
            return None, path_obj, True
        try:
            return load_bgr_image(path), path_obj, False
        except ValueError as error:
            QMessageBox.critical(self, "Image load error", str(error))
            self._append_log(str(error))
            return None

    @staticmethod
    def _open_video_capture(path: Path) -> cv2.VideoCapture:
        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise ValueError(f"Unable to open video: {path}")
        return capture

    @staticmethod
    def _read_video_frame(capture: cv2.VideoCapture):
        ret, frame = capture.read()
        return frame if ret else None

    @staticmethod
    def _video_timer_interval(capture: cv2.VideoCapture) -> int:
        fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
        return int(max(25, min(200, round(1000.0 / fps))))

    def _stop_video(self) -> None:
        if self.video_timer.isActive():
            self.video_timer.stop()
        if self.video_capture is not None:
            self.video_capture.release()
        self.video_capture = None

    def _advance_video_frame(self) -> None:
        if self.video_capture is None:
            return
        ret, frame = self.video_capture.read()
        if not ret:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return
        width = frame.shape[1]
        if width > 800:
            center_x = width // 2
            frame = frame[:, center_x - 300 : center_x + 300]
            width = 600

        self.current_image = frame.copy()
        self.frame_index += 1
        now = time.time()
        fps = 0
        if self._last_frame_time and now - self._last_frame_time > 0.02:
            fps = int(round(1.0 / (now - self._last_frame_time)))
        self._last_frame_time = now

        trigger_left = width // 2 - 140
        trigger_right = width // 2 + 140
        cv2.line(frame, (trigger_left, 0), (trigger_left, frame.shape[0]), (0, 255, 255), 2)
        cv2.line(frame, (trigger_right, 0), (trigger_right, frame.shape[0]), (0, 255, 255), 2)
        cv2.putText(frame, "TRIGGER ZONE", (trigger_left + 40, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps}", (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 50), 2)

        source_name = f"Video: {self.current_path.name if self.current_path is not None else 'camera feed'}"
        self.station_panel.show_live_feed(frame, source_name)

        try:
            _, blurred = preprocess_image(self.current_image)
            mask = create_foreground_mask(blurred)
            outer = detect_outer_circle(mask, blurred)
        except Exception:
            outer = None

        radius_limits = load_tolerances().get("outer_radius_px", {})
        valid_disk = bool(outer and radius_limits.get("min", 0) <= outer.radius <= radius_limits.get("max", 9999))

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
            cv2.putText(frame, trigger_text, (max(10, width - 220), 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, trigger_color, 2)
            if trigger_active and not self.disc_inspected:
                record = self.controller.inspect_current_part(self.current_image, source_name)
                self.station_panel.show_record(record)
                overlay_stem = self.current_path.stem if self.current_path is not None else "video"
                overlay_path = self._save_station_overlay(record, overlay_stem)
                self._persist_station_record(record, overlay_path)
                self._prepare_label_confirmation(record)
                self._append_log(self._prediction_log_line(record, prefix="Auto"))
                LOGGER.info("Auto inspection complete for %s: %s", source_name, record.decision.value)
                self.disc_inspected = True
                self._refresh_summary()
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

    @staticmethod
    def _caption(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("statusCaption")
        return label

    def _append_log(self, message: str) -> None:
        self.log_console.appendPlainText(message)

    def _prepare_label_confirmation(self, record) -> None:
        if record.inspection_result is None:
            return
        self._pending_dataset_record = record
        self._pending_anomaly_score = anomaly_score(record.inspection_result)
        self._pending_prediction = assisted_prediction(record.inspection_result)
        self._set_label_buttons_enabled(True)

    def _prediction_log_line(self, record, prefix: str = "Decision") -> str:
        prediction = self._pending_prediction or record.decision.value
        score = self._pending_anomaly_score if self._pending_anomaly_score is not None else "-"
        return f"{prefix}: {record.decision.value}. Prediction: {prediction}. Anomaly score: {score}. {self.plc.last_action}."

    def _set_label_buttons_enabled(self, enabled: bool) -> None:
        self.control_panel.confirm_good_button.setEnabled(enabled)
        self.control_panel.mark_defective_button.setEnabled(enabled)

    def _initialize_storage(self) -> bool:
        try:
            self.storage.initialize()
        except Exception as error:  # noqa: BLE001 - operator needs GUI even if DB is offline
            LOGGER.warning("Persistent storage unavailable: %s", error)
            return False
        return True

    def _update_clock(self) -> None:
        """Refresh the operator-visible real-time clock."""
        self.header_widget.set_clock_text(QDateTime.currentDateTime().toString("dd MMM yyyy  HH:mm:ss"))
