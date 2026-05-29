"""Modern industrial-grade application header with branding, PLC health,
system status, live clock, and operator actions.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from automation.plc import PLCStatus
from gui.plc_status_panel import PLCStatusPanel

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"


class HeaderWidget(QFrame):
    """Professional industrial control system header."""

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("headerWidget")
        self.setFixedHeight(104)

        # =========================================================
        # EXTERNAL PANELS
        # =========================================================
        self.plc_status_panel = PLCStatusPanel()

        # =========================================================
        # CLOCK LABEL
        # =========================================================
        self.clock_value = QLabel("--:--:--")
        self.clock_value.setObjectName("clockValue")
        self.clock_value.setAlignment(Qt.AlignCenter)

        # =========================================================
        # SHUTDOWN BUTTON
        # =========================================================
        self.shutdown_button = QPushButton("⏻")
        self.shutdown_button.setObjectName("shutdownButton")
        self.shutdown_button.setToolTip("Shutdown System")
        self.shutdown_button.setCursor(Qt.PointingHandCursor)
        self.shutdown_button.setFixedSize(42, 42)

        self._build_layout()

    # =============================================================
    # PUBLIC METHODS
    # =============================================================
    def show_plc_status(self, status: PLCStatus) -> None:
        """Update PLC telemetry panel."""
        self.plc_status_panel.show_status(status)

    def set_clock_text(self, text: str) -> None:
        """Update date/time text."""
        self.clock_value.setText(text)

    # =============================================================
    # UI BUILD
    # =============================================================
    def _build_layout(self) -> None:
        self.setStyleSheet(
            """
            #headerWidget {
                background-color: #0F172A;
                border-bottom: 2px solid #1E293B;
            }

            #logoContainer {
                background-color: transparent;
                border-radius: 12px;
            }

            #companyTitle {
                color: #F8FAFC;
                font-size: 20px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            #systemTitle {
                color: #38BDF8;
                font-size: 14px;
                font-weight: 600;
            }

            #applicationTitle {
                color: #CBD5E1;
                font-size: 13px;
                font-weight: 500;
            }

            #separatorLabel {
                color: #64748B;
                font-size: 13px;
                font-weight: 700;
            }

            #statusTag {
                background-color: #14532D;
                color: #DCFCE7;
                padding: 4px 10px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 700;
            }

            #timeBox {
                background-color: #111827;
                border: 1px solid #334155;
                border-radius: 14px;
            }

            #timeCaption {
                color: #94A3B8;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            #clockValue {
                color: #F8FAFC;
                font-size: 15px;
                font-weight: 700;
            }

            #shutdownButton {
                background-color: #7F1D1D;
                color: white;
                border: none;
                border-radius: 21px;
                font-size: 18px;
                font-weight: bold;
            }

            #shutdownButton:hover {
                background-color: #B91C1C;
            }

            #shutdownButton:pressed {
                background-color: #991B1B;
            }
            """
        )

        # =========================================================
        # MAIN LAYOUT
        # =========================================================
        layout = QHBoxLayout(self)

        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(18)

        # =========================================================
        # LOGO SECTION
        # =========================================================
        logo_container = QFrame()
        logo_container.setObjectName("logoContainer")

        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)

        logo = QPixmap(str(ASSETS_DIR / "ashtech_logo.png"))

        logo_label.setPixmap(
            logo.scaled(
                170,
                60,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

        logo_label.setFixedSize(180, 64)

        logo_layout.addWidget(logo_label)

        layout.addWidget(logo_container)

        # =========================================================
        # TITLE / SYSTEM INFORMATION
        # =========================================================
        title_container = QWidget()

        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        # COMPANY TITLE
        company_label = QLabel(
            "ASHTECH ENGINEERING SOLUTIONS"
        )
        company_label.setObjectName("companyTitle")

        title_layout.addWidget(company_label)

        # SECOND ROW
        second_row = QHBoxLayout()
        second_row.setSpacing(10)

        system_label = QLabel("DiskVisionInspector")
        system_label.setObjectName("systemTitle")

        separator = QLabel("•")
        separator.setObjectName("separatorLabel")

        application_label = QLabel(
            "Single Station Disc Inspection System"
        )
        application_label.setObjectName("applicationTitle")

        status_tag = QLabel("SYSTEM ONLINE")
        status_tag.setObjectName("statusTag")
        status_tag.setAlignment(Qt.AlignCenter)
        status_tag.setFixedHeight(24)

        second_row.addWidget(system_label)
        second_row.addWidget(separator)
        second_row.addWidget(application_label)
        second_row.addSpacing(12)
        second_row.addWidget(status_tag)
        second_row.addStretch()

        title_layout.addLayout(second_row)

        title_container.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        layout.addWidget(title_container)

        # =========================================================
        # DATE / TIME PANEL
        # =========================================================
        time_box = QFrame()
        time_box.setObjectName("timeBox")
        time_box.setFixedSize(210, 62)

        time_layout = QVBoxLayout(time_box)
        time_layout.setContentsMargins(12, 6, 12, 6)
        time_layout.setSpacing(2)

        time_caption = QLabel("SYSTEM DATE & TIME")
        time_caption.setObjectName("timeCaption")
        time_caption.setAlignment(Qt.AlignCenter)

        time_layout.addWidget(time_caption)
        time_layout.addWidget(self.clock_value)

        layout.addWidget(time_box)

        # =========================================================
        # PLC STATUS PANEL
        # =========================================================
        layout.addWidget(self.plc_status_panel)

        # =========================================================
        # SHUTDOWN BUTTON
        # =========================================================
        layout.addWidget(
            self.shutdown_button,
            alignment=Qt.AlignVCenter,
        )