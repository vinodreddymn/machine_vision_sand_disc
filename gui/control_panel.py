"""Operator command panel."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ControlPanel(QWidget):
    """Expose top-level two-station workflow actions."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("controlPanel")
        
        self.workflow_label = QLabel("Workflow Controls")
        self.workflow_label.setObjectName("panelHeading")

        # Stage 1 Controls
        self.s1_label = QLabel("STAGE 1 - TOP SIDE")
        self.s1_label.setObjectName("panelSubheading")
        self.new_part_button_s1 = QPushButton("Start New S1 Part")
        self.new_part_button_s1.setObjectName("primaryButton")
        self.upload_station_1_button = QPushButton("Upload S1 Image/Video")
        self.upload_station_1_button.setObjectName("primaryButton")

        # Stage 2 Controls
        self.s2_label = QLabel("STAGE 2 - FLIPPED SIDE")
        self.s2_label.setObjectName("panelSubheading")
        self.new_part_button_s2 = QPushButton("Start New S2 Part")
        self.new_part_button_s2.setObjectName("primaryButton")
        self.upload_station_2_button = QPushButton("Upload S2 Image/Video")
        self.upload_station_2_button.setObjectName("primaryButton")

        # Keep legacy alias for simple backwards compatibility
        self.new_part_button = self.new_part_button_s1

        self.workflow_note = QLabel(
            "Stage 1 and Stage 2 operate completely independently. Parts passed at Stage 1 are collected and manually fed to Stage 2."
        )
        self.workflow_note.setObjectName("mutedText")
        self.workflow_note.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.workflow_label)
        layout.addWidget(self.s1_label)
        layout.addWidget(self.new_part_button_s1)
        layout.addWidget(self.upload_station_1_button)
        
        layout.addWidget(self._create_separator())
        
        layout.addWidget(self.s2_label)
        layout.addWidget(self.new_part_button_s2)
        layout.addWidget(self.upload_station_2_button)
        
        layout.addWidget(self._create_separator())
        layout.addWidget(self.workflow_note)
        layout.addStretch()

    @staticmethod
    def _create_separator() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #243041; max-height: 1px;")
        return line
