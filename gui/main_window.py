"""Main application window for the two-station inspection workflow."""

from __future__ import annotations

import cv2
import logging
from pathlib import Path

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
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from automation.plc import SimulatedPLCController
from automation.workflow import FinalDisposition, StationDecision, TwoStageInspectionController
from config.settings import KIOSK_MODE, POSTGRES_DSN
from gui.control_panel import ControlPanel
from gui.footer_widget import FooterWidget
from gui.header_widget import HeaderWidget
from gui.station_panel import StationPanel
from storage.postgres import PostgresInspectionRepository
from storage.service import InspectionStorageService
from utils.file_utils import save_result_image
from utils.image_utils import load_bgr_image

LOGGER = logging.getLogger(__name__)
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


class MainWindow(QMainWindow):
    """Desktop shell for manual two-station inspection and future live capture."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DiskVisionInspector")
        self.setMinimumSize(1280, 720)
        self.storage = InspectionStorageService(PostgresInspectionRepository(POSTGRES_DSN))
        self.storage_available = self._initialize_storage()
        self.plc = SimulatedPLCController()
        part_id_factory = self.storage.next_part_id if self.storage_available else None
        self.controller = TwoStageInspectionController(self.plc, part_id_factory=part_id_factory)
        self.station_1_image = None
        self.station_2_image = None
        self.station_1_path: Path | None = None
        self.station_2_path: Path | None = None
        self.station_1_video_capture: cv2.VideoCapture | None = None
        self.station_2_video_capture: cv2.VideoCapture | None = None
        self.station_1_video_timer = QTimer(self)
        self.station_2_video_timer = QTimer(self)
        self.station_1_frame_index = 0
        self.station_2_frame_index = 0

        self.control_panel = ControlPanel()
        self.header_widget = HeaderWidget()
        self.footer_widget = FooterWidget()
        self.station_1_panel = StationPanel("Station 1 - Top Side")
        self.station_2_panel = StationPanel("Station 2 - Flipped Side")
        self.log_console = QPlainTextEdit()
        self.log_console.setObjectName("logConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumBlockCount(300)

        self.part_id_value = QLabel()
        self.station_1_value = QLabel()
        self.flipper_value = QLabel()
        self.station_2_value = QLabel()
        self.final_value = QLabel()
        self.plc_value = QLabel()
        self.storage_value = QLabel()
        self.total_detected_value = QLabel()
        self.station_1_passed_value = QLabel()
        self.station_1_rejected_value = QLabel()
        self.station_2_received_value = QLabel()
        self.station_2_passed_value = QLabel()
        self.station_2_rejected_value = QLabel()
        self.station_1_serial_value = QLabel()
        self.station_2_serial_value = QLabel()
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)

        self._build_layout()
        self._apply_theme()
        self._connect_signals()
        self.station_1_video_timer.timeout.connect(self._advance_station_1_video_frame)
        self.station_2_video_timer.timeout.connect(self._advance_station_2_video_frame)
        self._apply_display_mode()
        self._update_clock()
        self.clock_timer.start(1000)
        self._refresh_summary()
        self._append_log("System ready. Manual upload mode is active.")

    def _build_layout(self) -> None:
        summary_box = self._build_process_summary()
        counters_box = self._build_counter_summary()

        workspace_widget = QWidget()
        workspace_widget.setObjectName("workspaceWidget")
        workspace_layout = QVBoxLayout(workspace_widget)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(14)

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

        stations_host = QWidget()
        stations_host.setObjectName("stationsHost")
        stations_layout = QHBoxLayout(stations_host)
        stations_layout.setContentsMargins(0, 0, 0, 0)
        stations_layout.setSpacing(14)
        stations_layout.addWidget(self.station_1_panel)
        stations_layout.addWidget(self.station_2_panel)

        content_host = QWidget()
        content_layout = QVBoxLayout(content_host)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)
        summary_row = QWidget()
        summary_row_layout = QHBoxLayout(summary_row)
        summary_row_layout.setContentsMargins(0, 0, 0, 0)
        summary_row_layout.setSpacing(14)
        summary_row_layout.addWidget(summary_box, 1)
        summary_row_layout.addWidget(counters_box, 1)
        content_layout.addWidget(summary_row)
        content_layout.addWidget(stations_host, 1)

        splitter = QSplitter()
        splitter.addWidget(left_column)
        splitter.addWidget(content_host)
        splitter.setSizes([300, 1580])
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
        self.control_panel.upload_station_1_button.clicked.connect(self.upload_station_1_image)
        self.control_panel.inspect_station_1_button.clicked.connect(self.run_station_1_inspection)
        self.control_panel.upload_station_2_button.clicked.connect(self.upload_station_2_image)
        self.control_panel.inspect_station_2_button.clicked.connect(self.run_station_2_inspection)
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
        #workspaceWidget, #stationsHost { background-color: transparent; }
        #logoLabel { background-color: transparent; border: none; }
        #companyTitle {
            font-size: 22px;
            font-weight: bold;
            color: #F8FAFC;
        }
        #systemTitle {
            color: #F8FAFC;
            font-size: 18px;
            font-weight: bold;
        }
        #applicationTitle, #mutedText { color: #94A3B8; }
        #statusCaption {
            color: #64748B;
            font-size: 11px;
            font-weight: bold;
        }
        #statusValue, #summaryValue, #plcValue {
            color: #CBD5E1;
            font-weight: bold;
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
            font-size: 16px;
            font-weight: bold;
        }
        #shutdownButton {
            background-color: #7F1D1D;
            border-color: #EF4444;
            color: #FEE2E2;
            font-size: 22px;
            padding: 0;
        }
        #shutdownButton:hover {
            background-color: #991B1B;
        }
        #onlineStatus {
            background-color: #14532D;
            border: 1px solid #22C55E;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: bold;
            color: white;
        }
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
        #successButton {
            background-color: #166534;
            border-color: #22C55E;
        }
        #successButton:hover { background-color: #15803D; }
        QPushButton:disabled {
            background-color: #1F2937;
            border-color: #334155;
            color: #64748B;
        }
        QPlainTextEdit, QTableWidget, QListWidget {
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
        QHeaderView::section {
            background-color: #162033;
            color: #CBD5E1;
            padding: 8px;
            border: none;
        }
        QTableWidget {
            alternate-background-color: #101827;
            gridline-color: #243041;
        }
        QListWidget::item {
            padding: 7px 8px;
            border-bottom: 1px solid #162033;
        }
        QSplitter::handle {
            background-color: #0B1220;
            width: 10px;
        }

        #headerWidget {
            background-color: #111827;
            border-bottom: 2px solid #1f2937;
        }

        #companyTitle {
            color: white;
            font-size: 18px;
            font-weight: 700;
        }

        #systemTitle {
            color: #60a5fa;
            font-size: 14px;
            font-weight: 600;
        }

        #applicationTitle {
            color: #cbd5e1;
            font-size: 12px;
        }

        #separatorLabel {
            color: #6b7280;
            font-size: 13px;
        }

        #timeBox {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
        }

        #statusCaption {
            color: #94a3b8;
            font-size: 10px;
            font-weight: 600;
        }

        #clockValue {
            color: white;
            font-size: 13px;
            font-weight: 700;
        }

        #shutdownButton {
            background-color: #dc2626;
            color: white;
            border-radius: 17px;
            font-size: 16px;
            font-weight: bold;
        }

        #shutdownButton:hover {
            background-color: #ef4444;
        }

        #plcPanel {
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 10px;
        }

        #statusCaption {
            color: #94a3b8;
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        #plcValue {
            color: #f8fafc;
            font-size: 12px;
            font-weight: 700;
            padding-left: 2px;
            padding-right: 2px;
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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)
        rows = [
            ("Part ID", self.part_id_value),
            ("Station 1", self.station_1_value),
            ("Station 1 Serial", self.station_1_serial_value),
            ("Flipper", self.flipper_value),
            ("Station 2", self.station_2_value),
            ("Station 2 Serial", self.station_2_serial_value),
            ("Final Disposition", self.final_value),
            ("Last PLC Action", self.plc_value),
            ("Storage", self.storage_value),
        ]
        for row, (label, value) in enumerate(rows):
            layout.addWidget(self._caption(label.upper()), row, 0)
            value.setObjectName("summaryValue")
            layout.addWidget(value, row, 1)
        return box

    def _build_counter_summary(self) -> QWidget:
        box = QWidget()
        box.setObjectName("summaryPanel")
        layout = QGridLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)
        rows = [
            ("Total Parts Detected", self.total_detected_value),
            ("Passed at Station 1", self.station_1_passed_value),
            ("Rejected at Station 1", self.station_1_rejected_value),
            ("Received at Station 2", self.station_2_received_value),
            ("Passed at Station 2", self.station_2_passed_value),
            ("Rejected at Station 2", self.station_2_rejected_value),
        ]
        for row, (label, value) in enumerate(rows):
            layout.addWidget(self._caption(label.upper()), row, 0)
            value.setObjectName("summaryValue")
            layout.addWidget(value, row, 1)
        return box

    def start_new_part(self) -> None:
        """Reset both stations for the next incoming product."""
        self._stop_station_video(1)
        self._stop_station_video(2)
        part = self.controller.start_new_part()
        self.station_1_image = None
        self.station_2_image = None
        self.station_1_path = None
        self.station_2_path = None
        self.station_1_panel.clear_station()
        self.station_2_panel.clear_station()
        self.control_panel.inspect_station_1_button.setEnabled(False)
        self.control_panel.upload_station_2_button.setEnabled(False)
        self.control_panel.inspect_station_2_button.setEnabled(False)
        self._refresh_summary()
        self._append_log(f"Started new part: {part.part_id}")

    def upload_station_1_image(self) -> None:
        """Load the first-side image or video manually until a live camera is connected."""
        loaded = self._load_media("Select Station 1 image or video")
        if loaded is None:
            return
        image, path, is_video = loaded
        self.station_1_path = path
        self._stop_station_video(1)
        if is_video:
            try:
                self.station_1_video_capture = self._open_video_capture(path)
            except ValueError as error:
                QMessageBox.critical(self, "Video load error", str(error))
                self._append_log(str(error))
                return
            first_frame = self._read_video_frame(self.station_1_video_capture)
            if first_frame is None:
                QMessageBox.critical(self, "Video load error", f"Unable to read frames from video: {path.name}")
                self._append_log(f"Unable to read frames from video: {path}")
                self._stop_station_video(1)
                return
            self.station_1_image = first_frame
            self.station_1_frame_index = 1
            self.station_1_panel.show_live_feed(first_frame, f"Video: {path.name}")
            self.station_1_panel.capture_viewer.clear_image("Video loaded. Inspect to analyze current frame.")
            self.station_1_panel.result_panel.clear_results()
            interval = self._video_timer_interval(self.station_1_video_capture)
            self.station_1_video_timer.start(interval)
            self.control_panel.inspect_station_1_button.setEnabled(True)
            self._append_log(f"Station 1 video loaded: {path.name}")
            return
        self.station_1_image = image
        self.station_1_panel.show_uploaded_image(image, path.name)
        self.control_panel.inspect_station_1_button.setEnabled(True)
        self._append_log(f"Station 1 image loaded: {path.name}")

    def upload_station_2_image(self) -> None:
        """Load the flipped-side image or video manually after a station-one pass."""
        if self.controller.current_part.station_1.decision is not StationDecision.PASS:
            QMessageBox.information(self, "Station 2 locked", "Station 1 must pass before Station 2 can be inspected.")
            return
        loaded = self._load_media("Select Station 2 image or video")
        if loaded is None:
            return
        image, path, is_video = loaded
        self.station_2_path = path
        self._stop_station_video(2)
        if is_video:
            try:
                self.station_2_video_capture = self._open_video_capture(path)
            except ValueError as error:
                QMessageBox.critical(self, "Video load error", str(error))
                self._append_log(str(error))
                return
            first_frame = self._read_video_frame(self.station_2_video_capture)
            if first_frame is None:
                QMessageBox.critical(self, "Video load error", f"Unable to read frames from video: {path.name}")
                self._append_log(f"Unable to read frames from video: {path}")
                self._stop_station_video(2)
                return
            self.station_2_image = first_frame
            self.station_2_frame_index = 1
            self.station_2_panel.show_live_feed(first_frame, f"Video: {path.name}")
            self.station_2_panel.capture_viewer.clear_image("Video loaded. Inspect to analyze current frame.")
            self.station_2_panel.result_panel.clear_results()
            interval = self._video_timer_interval(self.station_2_video_capture)
            self.station_2_video_timer.start(interval)
            self.control_panel.inspect_station_2_button.setEnabled(True)
            self._append_log(f"Station 2 video loaded: {path.name}")
            return
        self.station_2_image = image
        self.station_2_panel.show_uploaded_image(image, path.name)
        self.control_panel.inspect_station_2_button.setEnabled(True)
        self._append_log(f"Station 2 image loaded: {path.name}")

    def run_station_1_inspection(self) -> None:
        """Inspect the top side and issue station-one line action."""
        if self.station_1_image is None or self.station_1_path is None:
            QMessageBox.information(self, "No image", "Upload a Station 1 image before inspection.")
            return
        record = self.controller.inspect_station_1(self.station_1_image, self.station_1_path.name)
        self.station_1_panel.show_record(record)
        overlay_path = self._save_station_overlay(record, self.station_1_path.stem)
        self._persist_station_record("S1", record, overlay_path)
        if record.decision is StationDecision.FAIL:
            self.station_2_panel.show_record(self.controller.current_part.station_2)
            self.control_panel.upload_station_2_button.setEnabled(False)
            self.control_panel.inspect_station_2_button.setEnabled(False)
        else:
            self.control_panel.upload_station_2_button.setEnabled(True)
        self._refresh_summary()
        self._append_log(f"Station 1 decision: {record.decision.value}. {self.plc.last_action}.")
        LOGGER.info("Station 1 inspection complete for %s: %s", self.station_1_path.name, record.decision.value)

    def run_station_2_inspection(self) -> None:
        """Inspect the flipped side and issue final line action."""
        if self.station_2_image is None or self.station_2_path is None:
            QMessageBox.information(self, "No image", "Upload a Station 2 image before inspection.")
            return
        try:
            record = self.controller.inspect_station_2(self.station_2_image, self.station_2_path.name)
        except RuntimeError as error:
            QMessageBox.information(self, "Station 2 locked", str(error))
            return
        self.station_2_panel.show_record(record)
        overlay_path = self._save_station_overlay(record, self.station_2_path.stem)
        self._persist_station_record("S2", record, overlay_path)
        self._refresh_summary()
        self._append_log(f"Station 2 decision: {record.decision.value}. {self.plc.last_action}.")
        LOGGER.info("Station 2 inspection complete for %s: %s", self.station_2_path.name, record.decision.value)

    def _save_station_overlay(self, record, stem: str) -> str | None:
        if record.overlay_image is None:
            return None
        suffix = record.name.lower().replace(" ", "_")
        saved = save_result_image(record.overlay_image, record.decision is StationDecision.PASS, f"{suffix}_{stem}")
        self._append_log(f"{record.name} overlay saved: {saved.name}")
        return str(saved)

    def _persist_station_record(self, stage: str, record, overlay_path: str | None) -> None:
        if not self.storage_available:
            return
        serial = self.storage.persist_station_record(
            physical_part_id=self.controller.current_part.part_id,
            stage=stage,
            record=record,
            final_disposition=self.controller.current_part.final_disposition,
            overlay_path=overlay_path,
        )
        self._append_log(f"{record.name} persisted as {serial}")

    def _refresh_summary(self) -> None:
        part = self.controller.current_part
        self.part_id_value.setText(part.part_id)
        self.station_1_value.setText(part.station_1.decision.value)
        self.station_1_serial_value.setText(part.station_1.serial_number or "-")
        self.flipper_value.setText("READY TO FLIP" if part.flipper_ready else "WAITING")
        self.station_2_value.setText(part.station_2.decision.value)
        self.station_2_serial_value.setText(part.station_2.serial_number or "-")
        self.final_value.setText(part.final_disposition.value)
        self.plc_value.setText(self.plc.last_action)
        self.storage_value.setText("ONLINE" if self.storage_available else "OFFLINE")
        self.footer_widget.set_values(
            part_id=part.part_id,
            storage_status="ONLINE" if self.storage_available else "OFFLINE",
            mode=self.plc.read_status().mode.value,
        )
        self.header_widget.show_plc_status(self.plc.read_status())
        counters = self.controller.counters
        self.total_detected_value.setText(str(counters.total_parts_detected))
        self.station_1_passed_value.setText(str(counters.station_1_passed))
        self.station_1_rejected_value.setText(str(counters.station_1_rejected))
        self.station_2_received_value.setText(str(counters.station_2_received))
        self.station_2_passed_value.setText(str(counters.station_2_passed))
        self.station_2_rejected_value.setText(str(counters.station_2_rejected))

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

    def _open_video_capture(self, path: Path) -> cv2.VideoCapture:
        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise ValueError(f"Unable to open video: {path}")
        return capture

    def _read_video_frame(self, capture: cv2.VideoCapture):
        if capture is None:
            return None
        ret, frame = capture.read()
        return frame if ret else None

    @staticmethod
    def _video_timer_interval(capture: cv2.VideoCapture) -> int:
        fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
        interval = int(max(25, min(200, round(1000.0 / fps))))
        return interval

    def _stop_station_video(self, station: int) -> None:
        if station == 1:
            if self.station_1_video_timer.isActive():
                self.station_1_video_timer.stop()
            if self.station_1_video_capture is not None:
                self.station_1_video_capture.release()
            self.station_1_video_capture = None
        else:
            if self.station_2_video_timer.isActive():
                self.station_2_video_timer.stop()
            if self.station_2_video_capture is not None:
                self.station_2_video_capture.release()
            self.station_2_video_capture = None

    def _advance_station_1_video_frame(self) -> None:
        self._advance_video_frame(1)

    def _advance_station_2_video_frame(self) -> None:
        self._advance_video_frame(2)

    def _advance_video_frame(self, station: int) -> None:
        capture = self.station_1_video_capture if station == 1 else self.station_2_video_capture
        panel = self.station_1_panel if station == 1 else self.station_2_panel
        frame_index = self.station_1_frame_index if station == 1 else self.station_2_frame_index
        if capture is None:
            return
        ret, frame = capture.read()
        if not ret:
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return
        if station == 1:
            self.station_1_image = frame.copy()
            self.station_1_frame_index += 1
        else:
            self.station_2_image = frame.copy()
            self.station_2_frame_index += 1
        panel.show_live_feed(frame, f"Video: {self.station_1_path.name if station == 1 else self.station_2_path.name}")

    @staticmethod
    def _caption(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("statusCaption")
        return label

    @staticmethod
    def _value(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("statusValue")
        return label

    def _append_log(self, message: str) -> None:
        self.log_console.appendPlainText(message)

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
