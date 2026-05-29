"""Professional industrial-grade application footer with
runtime telemetry, production context, and system state.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class FooterWidget(QFrame):
    """Industrial control system footer panel."""

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("footerWidget")
        self.setFixedHeight(58)

        # =========================================================
        # VALUE LABELS
        # =========================================================
        self.part_value = QLabel("--")
        self.storage_value = QLabel("--")
        self.mode_value = QLabel("--")

        # Optional extra telemetry
        self.system_status_value = QLabel("ONLINE")

        self._build_layout()

    # =============================================================
    # PUBLIC METHODS
    # =============================================================
    def set_values(
        self,
        *,
        part_id: str,
        storage_status: str,
        mode: str,
        system_status: str = "ONLINE",
    ) -> None:
        """Update runtime footer values."""

        self.part_value.setText(part_id)
        self.storage_value.setText(storage_status)
        self.mode_value.setText(mode)
        self.system_status_value.setText(system_status)

    # =============================================================
    # UI CONSTRUCTION
    # =============================================================
    def _build_layout(self) -> None:

        self.setStyleSheet(
            """
            #footerWidget {
                background-color: #0F172A;
                border-top: 1px solid #1E293B;
            }

            #footerPanel {
                background-color: #111827;
                border: 1px solid #334155;
                border-radius: 10px;
            }

            #footerCaption {
                color: #94A3B8;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            #footerValue {
                color: #F8FAFC;
                font-size: 13px;
                font-weight: 700;
            }

            #systemName {
                color: #CBD5E1;
                font-size: 12px;
                font-weight: 600;
            }

            #onlineIndicator {
                background-color: #14532D;
                color: #DCFCE7;
                border-radius: 10px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 700;
            }
            """
        )

        # =========================================================
        # MAIN LAYOUT
        # =========================================================
        layout = QHBoxLayout(self)

        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(14)

        # =========================================================
        # STATUS PANELS
        # =========================================================
        layout.addWidget(
            self._build_panel(
                "CURRENT PART ID",
                self.part_value,
            )
        )

        layout.addWidget(
            self._build_panel(
                "LOCAL STORAGE",
                self.storage_value,
            )
        )

        layout.addWidget(
            self._build_panel(
                "OPERATING MODE",
                self.mode_value,
            )
        )

        # =========================================================
        # SYSTEM STATUS PANEL
        # =========================================================
        system_status_panel = self._build_panel(
            "SYSTEM STATUS",
            self.system_status_value,
        )

        self.system_status_value.setObjectName(
            "onlineIndicator"
        )

        layout.addWidget(system_status_panel)

        # =========================================================
        # STRETCH SPACE
        # =========================================================
        layout.addStretch()

        # =========================================================
        # SYSTEM NAME / VERSION
        # =========================================================
        system_name = QLabel(
            "DiskVisionInspector  •  "
            "Single Station Disc Inspection System"
        )

        system_name.setObjectName("systemName")
        system_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        system_name.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Preferred,
        )

        layout.addWidget(system_name)

    # =============================================================
    # PANEL CREATION
    # =============================================================
    def _build_panel(
        self,
        caption: str,
        value_label: QLabel,
    ) -> QWidget:
        """Create compact industrial footer panels."""

        panel = QFrame()
        panel.setObjectName("footerPanel")
        panel.setFixedHeight(40)

        layout = QVBoxLayout(panel)

        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(0)

        caption_label = QLabel(caption)
        caption_label.setObjectName("footerCaption")

        value_label.setObjectName("footerValue")

        layout.addWidget(caption_label)
        layout.addWidget(value_label)

        return panel