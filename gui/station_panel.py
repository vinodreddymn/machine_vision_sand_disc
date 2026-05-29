"""Reusable station workspace showing feed, capture, and inspection result."""

from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from automation.workflow import StationDecision, StationRecord
from gui.image_viewer import ImageViewer
from gui.result_panel import ResultPanel


class StationPanel(QWidget):
    """Display one physical station in the inspection line."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("stationPanel")
        self.title_label = QLabel(title)
        self.title_label.setObjectName("panelHeading")
        self.source_label = QLabel("No image loaded")
        self.source_label.setObjectName("mutedText")
        self.live_label = QLabel("Live Feed")
        self.live_label.setObjectName("panelSubheading")
        self.live_viewer = ImageViewer("Waiting for camera feed")
        self.capture_label = QLabel("Captured Image")
        self.capture_label.setObjectName("panelSubheading")
        self.capture_viewer = ImageViewer("No captured image")
        self.result_panel = ResultPanel(compact=True)

        media_grid = QGridLayout()
        media_grid.setContentsMargins(0, 0, 0, 0)
        media_grid.setHorizontalSpacing(10)
        media_grid.setVerticalSpacing(6)
        media_grid.addWidget(self.live_label, 0, 0)
        media_grid.addWidget(self.capture_label, 0, 1)
        media_grid.addWidget(self.live_viewer, 1, 0)
        media_grid.addWidget(self.capture_viewer, 1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.source_label)
        layout.addLayout(media_grid)
        layout.addWidget(self.result_panel)

    def show_uploaded_image(self, image, source_name: str) -> None:
        """Use uploaded image as the current feed while hardware is absent."""
        self.source_label.setText(source_name)
        self.live_viewer.set_bgr_image(image)
        self.capture_viewer.clear_image("No captured image")
        self.result_panel.clear_results()

    def show_live_feed(self, image, source_name: str) -> None:
        """Display a single live frame from a video source."""
        self.source_label.setText(source_name)
        self.live_viewer.set_bgr_image(image)

    def show_video_inspection_preview(self, overlay, result) -> None:
        """Render the latest inspection overlay and defect summary during video playback."""
        if overlay is not None:
            self.capture_viewer.set_bgr_image(overlay)
        self.result_panel.show_result(result)

    def show_record(self, record: StationRecord) -> None:
        """Render the completed station inspection."""
        if record.source_name:
            self.source_label.setText(record.source_name)
        if record.raw_image is not None:
            self.live_viewer.set_bgr_image(record.raw_image)
        if record.overlay_image is not None:
            self.capture_viewer.set_bgr_image(record.overlay_image)
        if record.inspection_result is not None:
            self.result_panel.show_result(record.inspection_result)
        elif record.decision is StationDecision.SKIPPED:
            self.capture_viewer.clear_image("Skipped")
            self.result_panel.show_skipped()

    def clear_station(self) -> None:
        """Reset the panel for a new incoming part."""
        self.source_label.setText("No image loaded")
        self.live_viewer.clear_image("Waiting for camera feed")
        self.capture_viewer.clear_image("No captured image")
        self.result_panel.clear_results()
