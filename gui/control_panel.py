"""Operator command panel."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ControlPanel(QWidget):
    """Expose top-level single-station workflow actions."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("controlPanel")

        self.workflow_label = QLabel("Workflow Controls")
        self.workflow_label.setObjectName("panelHeading")

        self.station_label = QLabel("SINGLE INSPECTION STATION")
        self.station_label.setObjectName("panelSubheading")
        self.new_part_button = QPushButton("Start New Part")
        self.new_part_button.setObjectName("primaryButton")
        self.upload_media_button = QPushButton("Upload Image/Video")
        self.upload_media_button.setObjectName("primaryButton")
        self.confirm_good_button = QPushButton("Confirm Good")
        self.confirm_good_button.setObjectName("primaryButton")
        self.mark_defective_button = QPushButton("Mark Defective")
        self.mark_defective_button.setObjectName("primaryButton")
        self.confirm_good_button.setEnabled(False)
        self.mark_defective_button.setEnabled(False)

        self.workflow_note = QLabel(
            "Single-station mode inspects one side of each disc and sends a final accept or reject command."
        )
        self.workflow_note.setObjectName("mutedText")
        self.workflow_note.setWordWrap(True)

        # Compatibility aliases used by older window code and tests.
        self.new_part_button_s1 = self.new_part_button
        self.upload_station_1_button = self.upload_media_button

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.workflow_label)
        layout.addWidget(self.station_label)
        layout.addWidget(self.new_part_button)
        layout.addWidget(self.upload_media_button)
        layout.addWidget(QLabel("Operator Label"))
        layout.addWidget(self.confirm_good_button)
        layout.addWidget(self.mark_defective_button)
        layout.addWidget(self.workflow_note)
        layout.addStretch()
