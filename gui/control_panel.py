"""Operator command panel."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ControlPanel(QWidget):
    """Expose top-level two-station workflow actions."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("controlPanel")
        self.workflow_label = QLabel("Workflow")
        self.workflow_label.setObjectName("panelHeading")
        self.new_part_button = QPushButton("Start New Part")
        self.new_part_button.setObjectName("primaryButton")
        self.upload_station_1_button = QPushButton("Upload Station 1 Image / Video")
        self.upload_station_1_button.setObjectName("primaryButton")
        self.inspect_station_1_button = QPushButton("Inspect Station 1")
        self.inspect_station_1_button.setObjectName("successButton")
        self.inspect_station_1_button.setEnabled(False)
        self.upload_station_2_button = QPushButton("Upload Station 2 Image / Video")
        self.upload_station_2_button.setObjectName("primaryButton")
        self.upload_station_2_button.setEnabled(False)
        self.inspect_station_2_button = QPushButton("Inspect Station 2")
        self.inspect_station_2_button.setObjectName("successButton")
        self.inspect_station_2_button.setEnabled(False)
        self.workflow_note = QLabel("Manual upload mode is active until cameras and conveyor triggers are connected.")
        self.workflow_note.setObjectName("mutedText")
        self.workflow_note.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.workflow_label)
        layout.addWidget(self.new_part_button)
        layout.addWidget(self.upload_station_1_button)
        layout.addWidget(self.inspect_station_1_button)
        layout.addWidget(self.upload_station_2_button)
        layout.addWidget(self.inspect_station_2_button)
        layout.addWidget(self.workflow_note)
        layout.addStretch()
