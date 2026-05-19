"""Compact branded application header with PLC status and clock."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from automation.plc import PLCStatus
from gui.plc_status_panel import PLCStatusPanel

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"


class HeaderWidget(QFrame):
    """Compact industrial-grade header."""

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("headerWidget")
        self.setFixedHeight(88)

        self.plc_status_panel = PLCStatusPanel()

        self.clock_value = QLabel()
        self.clock_value.setObjectName("clockValue")

        self.shutdown_button = QPushButton("⏻")
        self.shutdown_button.setObjectName("shutdownButton")
        self.shutdown_button.setToolTip("Shutdown System")
        self.shutdown_button.setFixedSize(34, 34)

        self._build_layout()

    def show_plc_status(self, status: PLCStatus) -> None:
        """Update PLC telemetry."""
        self.plc_status_panel.show_status(status)

    def set_clock_text(self, text: str) -> None:
        """Update date/time display."""
        self.clock_value.setText(text)

    def _build_layout(self) -> None:
        layout = QHBoxLayout(self)

        # Compact margins
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(14)

        # =========================================================
        # COMPANY LOGO
        # =========================================================
        logo_label = QLabel()
        logo_label.setObjectName("logoLabel")

        logo = QPixmap(str(ASSETS_DIR / "ashtech_logo.png"))

        logo_label.setPixmap(
            logo.scaled(
                152,
                52,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

        logo_label.setFixedSize(156, 56)
        logo_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(logo_label)

        # =========================================================
        # TITLE SECTION
        # =========================================================
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)

        company_label = QLabel("ASHTECH ENGINEERING SOLUTIONS")
        company_label.setObjectName("companyTitle")

        system_row = QHBoxLayout()
        system_row.setSpacing(8)

        system_label = QLabel("DiskVisionInspector")
        system_label.setObjectName("systemTitle")

        separator = QLabel("|")
        separator.setObjectName("separatorLabel")

        application_label = QLabel(
            "Industrial Machine Vision Inspection System"
        )
        application_label.setObjectName("applicationTitle")

        system_row.addWidget(system_label)
        system_row.addWidget(separator)
        system_row.addWidget(application_label)
        system_row.addStretch()

        title_layout.addWidget(company_label)
        title_layout.addLayout(system_row)

        layout.addLayout(title_layout)

        layout.addStretch()

        # =========================================================
        # DATE / TIME PANEL
        # =========================================================
        time_box = QFrame()
        time_box.setObjectName("timeBox")
        time_box.setFixedHeight(52)

        time_layout = QVBoxLayout(time_box)
        time_layout.setContentsMargins(10, 4, 10, 4)
        time_layout.setSpacing(0)

        time_caption = QLabel("DATE / TIME")
        time_caption.setObjectName("statusCaption")

        time_layout.addWidget(
            time_caption,
            alignment=Qt.AlignCenter,
        )

        time_layout.addWidget(
            self.clock_value,
            alignment=Qt.AlignCenter,
        )

        layout.addWidget(time_box)

        # =========================================================
        # PLC STATUS PANEL
        # =========================================================
        layout.addWidget(self.plc_status_panel)

        # =========================================================
        # SHUTDOWN BUTTON
        # =========================================================
        layout.addWidget(self.shutdown_button)