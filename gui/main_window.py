"""Main application window for the two-station inspection workflow."""

from __future__ import annotations

import cv2
import time
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
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from automation.plc import SimulatedPLCController
from automation.workflow import FinalDisposition, StationDecision, TwoStageInspectionController
from config.settings import KIOSK_MODE, POSTGRES_DSN, load_tolerances
from vision.preprocessing import preprocess_image, create_foreground_mask
from vision.circle_detection import detect_outer_circle
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
        self.empty_frames_s1 = 0
        self.empty_frames_s2 = 0
        self.last_disc_x_s1 = -1
        self.last_disc_x_s2 = -1
        self.station_1_disc_active = False
        self.station_1_disc_inspected = False
        self.station_2_disc_active = False
        self.station_2_disc_inspected = False
        self._last_frame_time_s1 = 0.0
        self._last_frame_time_s2 = 0.0

        self.control_panel = ControlPanel()
        self.header_widget = HeaderWidget()
        self.footer_widget = FooterWidget()
        self.station_1_panel = StationPanel("Station 1 - Top Side")
        self.station_2_panel = StationPanel("Station 2 - Flipped Side")
        self.log_console = QPlainTextEdit()
        self.log_console.setObjectName("logConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumBlockCount(300)

        self.part_id_value_s1 = QLabel()
        self.part_id_value_s2 = QLabel()
        self.part_id_value = self.part_id_value_s1
        self.station_1_value = QLabel()
        self.flipper_value = QLabel("N/A")
        self.station_2_value = QLabel()
        self.final_value_s1 = QLabel()
        self.final_value_s2 = QLabel()
        self.final_value = self.final_value_s1
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
        metrics_bar = self._build_production_metrics_bar()

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
        content_layout.addWidget(metrics_bar)
        content_layout.addWidget(summary_box)
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
        self.control_panel.new_part_button_s1.clicked.connect(self.start_new_part_s1)
        self.control_panel.new_part_button_s2.clicked.connect(self.start_new_part_s2)
        self.control_panel.upload_station_1_button.clicked.connect(self.upload_station_1_image)
        self.control_panel.upload_station_2_button.clicked.connect(self.upload_station_2_image)
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
        #metricStage {
            background-color: #111827;
            border: 1px solid #334155;
            border-radius: 6px;
        }
        #metricStageTitle {
            color: #F8FAFC;
            font-size: 14px;
            font-weight: 800;
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
        #metricValue[metricTone="received"] { color: #FDE68A; }
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
        layout = QHBoxLayout(box)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(24)

        # Stage 1 Column
        s1_box = QFrame()
        s1_box.setFrameShape(QFrame.StyledPanel)
        s1_box.setStyleSheet("border: none; background: transparent;")
        s1_layout = QGridLayout(s1_box)
        s1_layout.setContentsMargins(0, 0, 0, 0)
        s1_layout.setVerticalSpacing(8)
        s1_layout.setHorizontalSpacing(12)
        
        s1_title = QLabel("STAGE 1 - TOP SIDE")
        s1_title.setObjectName("panelSubheading")
        s1_layout.addWidget(s1_title, 0, 0, 1, 2)
        
        s1_rows = [
            ("Part ID", self.part_id_value_s1),
            ("Decision", self.station_1_value),
            ("Serial Number", self.station_1_serial_value),
            ("Disposition", self.final_value_s1),
        ]
        for idx, (label, val) in enumerate(s1_rows, start=1):
            s1_layout.addWidget(self._caption(label.upper()), idx, 0)
            val.setObjectName("summaryValue")
            s1_layout.addWidget(val, idx, 1)

        # Stage 2 Column
        s2_box = QFrame()
        s2_box.setFrameShape(QFrame.StyledPanel)
        s2_box.setStyleSheet("border: none; background: transparent;")
        s2_layout = QGridLayout(s2_box)
        s2_layout.setContentsMargins(0, 0, 0, 0)
        s2_layout.setVerticalSpacing(8)
        s2_layout.setHorizontalSpacing(12)
        
        s2_title = QLabel("STAGE 2 - FLIPPED SIDE")
        s2_title.setObjectName("panelSubheading")
        s2_layout.addWidget(s2_title, 0, 0, 1, 2)
        
        s2_rows = [
            ("Part ID", self.part_id_value_s2),
            ("Decision", self.station_2_value),
            ("Serial Number", self.station_2_serial_value),
            ("Disposition", self.final_value_s2),
        ]
        for idx, (label, val) in enumerate(s2_rows, start=1):
            s2_layout.addWidget(self._caption(label.upper()), idx, 0)
            val.setObjectName("summaryValue")
            s2_layout.addWidget(val, idx, 1)

        # System Info Column
        sys_box = QFrame()
        sys_box.setFrameShape(QFrame.StyledPanel)
        sys_box.setStyleSheet("border: none; background: transparent;")
        sys_layout = QGridLayout(sys_box)
        sys_layout.setContentsMargins(0, 0, 0, 0)
        sys_layout.setVerticalSpacing(8)
        sys_layout.setHorizontalSpacing(12)
        
        sys_title = QLabel("SYSTEM STATUS")
        sys_title.setObjectName("panelSubheading")
        sys_layout.addWidget(sys_title, 0, 0, 1, 2)
        
        sys_rows = [
            ("Last PLC Action", self.plc_value),
            ("Storage Connection", self.storage_value),
        ]
        for idx, (label, val) in enumerate(sys_rows, start=1):
            sys_layout.addWidget(self._caption(label.upper()), idx, 0)
            val.setObjectName("summaryValue")
            sys_layout.addWidget(val, idx, 1)

        layout.addWidget(s1_box, 1)
        layout.addWidget(self._create_vertical_line())
        layout.addWidget(s2_box, 1)
        layout.addWidget(self._create_vertical_line())
        layout.addWidget(sys_box, 1)

        return box

    @staticmethod
    def _create_vertical_line() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #243041; max-width: 1px;")
        return line

    def _build_production_metrics_bar(self) -> QWidget:
        box = QFrame()
        box.setObjectName("metricsBar")
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(
            self._metric_stage(
                "LINE TOTAL",
                [("TOTAL PARTS DETECTED", self.total_detected_value, "total")],
            ),
            1,
        )
        layout.addWidget(
            self._metric_stage(
                "STATION 1",
                [
                    ("PASSED", self.station_1_passed_value, "pass"),
                    ("FAILED", self.station_1_rejected_value, "fail"),
                ],
            ),
            2,
        )
        layout.addWidget(
            self._metric_stage(
                "STATION 2",
                [
                    ("RECEIVED", self.station_2_received_value, "received"),
                    ("PASSED", self.station_2_passed_value, "pass"),
                    ("FAILED", self.station_2_rejected_value, "fail"),
                ],
            ),
            3,
        )
        return box

    def _metric_stage(self, title: str, metrics: list[tuple[str, QLabel, str]]) -> QWidget:
        stage = QFrame()
        stage.setObjectName("metricStage")
        layout = QVBoxLayout(stage)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("metricStageTitle")
        layout.addWidget(title_label)

        tiles = QHBoxLayout()
        tiles.setContentsMargins(0, 0, 0, 0)
        tiles.setSpacing(8)
        for label, value, tone in metrics:
            tiles.addWidget(self._metric_tile(label, value, tone), 1)
        layout.addLayout(tiles)
        return stage

    @staticmethod
    def _metric_tile(label_text: str, value: QLabel, tone: str) -> QWidget:
        tile = QFrame()
        tile.setObjectName("metricTile")
        tile.setMinimumHeight(92)

        layout = QVBoxLayout(tile)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        label = QLabel(label_text)
        label.setObjectName("metricLabel")
        label.setWordWrap(True)
        value.setObjectName("metricValue")
        value.setProperty("metricTone", tone)
        value.setMinimumWidth(76)

        layout.addWidget(label)
        layout.addWidget(value, 1)
        return tile

    def start_new_part(self) -> None:
        """Reset both stations for the next incoming product."""
        self.start_new_part_s1()
        self.start_new_part_s2()

    def start_new_part_s1(self) -> None:
        """Reset Stage 1 for the next incoming product."""
        self._stop_station_video(1)
        part = self.controller.start_new_part_s1()
        self.station_1_image = None
        self.station_1_path = None
        self.station_1_panel.clear_station()
        self.station_1_disc_active = False
        self.station_1_disc_inspected = False
        self._refresh_summary()
        self._append_log(f"Started new Stage 1 part: {part.part_id}")

    def start_new_part_s2(self) -> None:
        """Reset Stage 2 for the next incoming product."""
        self._stop_station_video(2)
        part = self.controller.start_new_part_s2()
        self.station_2_image = None
        self.station_2_path = None
        self.station_2_panel.clear_station()
        self.station_2_disc_active = False
        self.station_2_disc_inspected = False
        self._refresh_summary()
        self._append_log(f"Started new Stage 2 part: {part.part_id}")

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
            self._append_log(f"Station 1 video loaded: {path.name}")
            return
        self.station_1_image = image
        self.station_1_panel.show_uploaded_image(image, path.name)
        self._append_log(f"Station 1 image loaded: {path.name}")
        self.run_station_1_inspection()

    def upload_station_2_image(self) -> None:
        """Load the flipped-side image or video manually without sequential station gating."""
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
            self._append_log(f"Station 2 video loaded: {path.name}")
            return
        self.station_2_image = image
        self.station_2_panel.show_uploaded_image(image, path.name)
        self._append_log(f"Station 2 image loaded: {path.name}")
        self.run_station_2_inspection()

    def run_station_1_inspection(self) -> None:
        """Inspect the top side and issue station-one line action."""
        if self.station_1_image is None or self.station_1_path is None:
            QMessageBox.information(self, "No image", "Upload a Station 1 image before inspection.")
            return
        record = self.controller.inspect_station_1(self.station_1_image, self.station_1_path.name)
        self.station_1_panel.show_record(record)
        overlay_path = self._save_station_overlay(record, self.station_1_path.stem)
        self._persist_station_record("S1", record, overlay_path, physical_part_id=None)
        self._refresh_summary()
        self._append_log(f"Station 1 decision: {record.decision.value}. {self.plc.last_action}.")
        LOGGER.info("Station 1 inspection complete for %s: %s", self.station_1_path.name, record.decision.value)

    def run_station_2_inspection(self) -> None:
        """Inspect the flipped side and issue final line action."""
        if self.station_2_image is None or self.station_2_path is None:
            QMessageBox.information(self, "No image", "Upload a Station 2 image before inspection.")
            return
        record = self.controller.inspect_station_2(self.station_2_image, self.station_2_path.name)
        self.station_2_panel.show_record(record)
        overlay_path = self._save_station_overlay(record, self.station_2_path.stem)
        self._persist_station_record("S2", record, overlay_path, physical_part_id=None)
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

    def _persist_station_record(self, stage: str, record, overlay_path: str | None, physical_part_id: str | None = None) -> None:
        if not self.storage_available:
            return
        part = self.controller.current_part_s1 if stage == "S1" else self.controller.current_part_s2
        if physical_part_id is None:
            physical_part_id = part.part_id
        serial = self.storage.persist_station_record(
            physical_part_id=physical_part_id,
            stage=stage,
            record=record,
            final_disposition=part.final_disposition,
            overlay_path=overlay_path,
        )
        self._append_log(f"{record.name} persisted as {serial}")

    def _refresh_summary(self) -> None:
        part_s1 = self.controller.current_part_s1
        part_s2 = self.controller.current_part_s2
        
        self.part_id_value_s1.setText(part_s1.part_id)
        self.station_1_value.setText(part_s1.station_1.decision.value)
        self.station_1_serial_value.setText(part_s1.station_1.serial_number or "-")
        self.final_value_s1.setText(part_s1.final_disposition.value)
        
        self.part_id_value_s2.setText(part_s2.part_id)
        self.station_2_value.setText(part_s2.station_2.decision.value)
        self.station_2_serial_value.setText(part_s2.station_2.serial_number or "-")
        self.final_value_s2.setText(part_s2.final_disposition.value)
        
        self.plc_value.setText(self.plc.last_action)
        self.storage_value.setText("ONLINE" if self.storage_available else "OFFLINE")
        
        self.footer_widget.set_values(
            part_id_s1=part_s1.part_id,
            part_id_s2=part_s2.part_id,
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
        width = frame.shape[1]
        # INDUSTRIAL OPTIMIZATION: Crop to the specific camera ROI
        # This reduces CPU by >50% and ensures only one part is visible at a time.
        if width > 800:
            center_x = width // 2
            frame = frame[:, center_x - 300 : center_x + 300]
            width = 600

        now = time.time()
        if station == 1:
            self.station_1_image = frame.copy()
            self.station_1_frame_index += 1
            # Estimate FPS from inter-frame timing
            last = self._last_frame_time_s1
            fps = 0
            if last and now - last > 0.02:
                fps = int(round(1.0 / (now - last)))
            self._last_frame_time_s1 = now
            working_frame = self.station_1_image
        else:
            self.station_2_image = frame.copy()
            self.station_2_frame_index += 1
            last = self._last_frame_time_s2
            fps = 0
            if last and now - last > 0.02:
                fps = int(round(1.0 / (now - last)))
            self._last_frame_time_s2 = now
            working_frame = self.station_2_image
            
        trigger_left = width // 2 - 140
        trigger_right = width // 2 + 140
        
        cv2.line(frame, (trigger_left, 0), (trigger_left, frame.shape[0]), (0, 255, 255), 2)
        cv2.line(frame, (trigger_right, 0), (trigger_right, frame.shape[0]), (0, 255, 255), 2)
        cv2.putText(frame, "TRIGGER ZONE", (trigger_left + 40, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Draw FPS and a compact trigger-state indicator for diagnostics
        cv2.putText(frame, f"FPS: {fps}", (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 50), 2)
        source_name = f"Video: {self.station_1_path.name if station == 1 and self.station_1_path is not None else self.station_2_path.name if station == 2 and self.station_2_path is not None else 'camera feed'}"
        panel.show_live_feed(frame, source_name)

        try:
            gray, blurred = preprocess_image(working_frame)
            mask = create_foreground_mask(blurred)
            outer = detect_outer_circle(mask, blurred)
        except Exception:
            outer = None

        tolerances = load_tolerances()
        radius_limits = tolerances.get("outer_radius_px", {})
        valid_disk = bool(
            outer
            and radius_limits.get("min", 0) <= outer.radius <= radius_limits.get("max", 9999)
        )

        if station == 1:
            disc_active = self.station_1_disc_active
            inspected = self.station_1_disc_inspected
            empty_frames = self.empty_frames_s1
        else:
            disc_active = self.station_2_disc_active
            inspected = self.station_2_disc_inspected
            empty_frames = self.empty_frames_s2

        if valid_disk:
            empty_frames = 0
            disc_x = outer.center[0]
            if not disc_active:
                disc_active = True
                inspected = False

            if station == 1:
                self.last_disc_x_s1 = disc_x
            else:
                self.last_disc_x_s2 = disc_x

            # Only inspect once when the part crosses the virtual trigger zone.
            entering_trigger = not inspected and trigger_left < disc_x < trigger_right
            trigger_active = trigger_left < disc_x < trigger_right
            trigger_text = "TRIGGER: YES" if trigger_active else "TRIGGER: NO"
            trigger_color = (0, 200, 0) if trigger_active else (200, 200, 50)
            cv2.putText(frame, trigger_text, (max(10, width - 220), 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, trigger_color, 2)
            if entering_trigger:
                if station == 1:
                    record = self.controller.inspect_station_1(self.station_1_image, source_name)
                    self.station_1_panel.show_record(record)
                    overlay_path = self._save_station_overlay(
                        record,
                        Path(self.station_1_path).stem if self.station_1_path is not None else "video",
                    )
                    self._persist_station_record("S1", record, overlay_path, physical_part_id=None)
                    self._append_log(f"Auto Station 1 decision: {record.decision.value}. {self.plc.last_action}.")
                    LOGGER.info("Auto Station 1 inspection complete for %s: %s", source_name, record.decision.value)
                else:
                    record = self.controller.inspect_station_2(self.station_2_image, source_name)
                    self.station_2_panel.show_record(record)
                    overlay_path = self._save_station_overlay(
                        record,
                        Path(self.station_2_path).stem if self.station_2_path is not None else "video",
                    )
                    self._persist_station_record("S2", record, overlay_path, physical_part_id=None)
                    self._append_log(f"Auto Station 2 decision: {record.decision.value}. {self.plc.last_action}.")
                    LOGGER.info("Auto Station 2 inspection complete for %s: %s", source_name, record.decision.value)

                inspected = True
                self._refresh_summary()

            # Reset the station state when the disc leaves the field of view.
            if disc_active and (disc_x < trigger_left - 120 or disc_x > trigger_right + 120):
                disc_active = False
                inspected = False

            if station == 1:
                self.empty_frames_s1 = empty_frames
                self.station_1_disc_active = disc_active
                self.station_1_disc_inspected = inspected
            else:
                self.empty_frames_s2 = empty_frames
                self.station_2_disc_active = disc_active
                self.station_2_disc_inspected = inspected

        else:
            empty_frames += 1
            if empty_frames > 10:
                if station == 1:
                    self.station_1_disc_active = False
                    self.station_1_disc_inspected = False
                    self.empty_frames_s1 = 0
                    self.last_disc_x_s1 = -1
                else:
                    self.station_2_disc_active = False
                    self.station_2_disc_inspected = False
                    self.empty_frames_s2 = 0
                    self.last_disc_x_s2 = -1
            else:
                if station == 1:
                    self.empty_frames_s1 = empty_frames
                else:
                    self.empty_frames_s2 = empty_frames

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
