"""Compact PLC telemetry panel for industrial dashboards."""

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

from automation.plc import PLCStatus


class PLCStatusPanel(QFrame):
    """Compact operator-friendly PLC telemetry panel."""

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("plcPanel")
        self.setFixedHeight(58)

        self.run_status = self._value_label()
        self.mode = self._value_label()
        self.conveyor = self._value_label()
        self.reject = self._value_label()
        self.accept_gate = self._value_label()

        layout = QHBoxLayout(self)

        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)

        fields = [
            ("PLC", self.run_status),
            ("MODE", self.mode),
            ("CONVEYOR", self.conveyor),
            ("REJECT", self.reject),
            ("ACCEPT", self.accept_gate),
        ]

        for caption, value in fields:
            layout.addWidget(self._build_status_item(caption, value))

        layout.addStretch()

    def _build_status_item(self, caption: str, value: QLabel) -> QWidget:
        """Create compact status block."""

        widget = QWidget()
        widget.setFixedWidth(100)

        item_layout = QVBoxLayout(widget)

        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(1)

        label = QLabel(caption)
        label.setObjectName("statusCaption")
        label.setAlignment(Qt.AlignCenter)

        value.setAlignment(Qt.AlignCenter)

        item_layout.addWidget(label)
        item_layout.addWidget(value)

        return widget

    def show_status(self, status: PLCStatus) -> None:
        """Update PLC telemetry."""

        self.run_status.setText(status.run_status.value)
        self.mode.setText(status.mode.value)
        self.conveyor.setText(status.conveyor_status.value)
        self.reject.setText(status.reject_actuator.value)
        self.accept_gate.setText(status.accept_gate.value)

    @staticmethod
    def _value_label() -> QLabel:
        label = QLabel("--")
        label.setObjectName("plcValue")
        label.setSizePolicy(
            QSizePolicy.Minimum,
            QSizePolicy.Fixed,
        )
        return label
