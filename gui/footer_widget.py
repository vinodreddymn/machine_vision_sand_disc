"""Application footer with concise runtime context."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class FooterWidget(QWidget):
    """Bottom strip for current part, storage, and operating mode."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("footerWidget")
        self.part_value = QLabel()
        self.storage_value = QLabel()
        self.mode_value = QLabel()
        self._build_layout()

    def set_values(self, *, part_id: str, storage_status: str, mode: str) -> None:
        """Refresh the footer summary values."""
        self.part_value.setText(part_id)
        self.storage_value.setText(storage_status)
        self.mode_value.setText(mode)

    def _build_layout(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(18)
        layout.addWidget(self._group("CURRENT PART", self.part_value))
        layout.addWidget(self._group("STORAGE", self.storage_value))
        layout.addWidget(self._group("OPERATING MODE", self.mode_value))
        layout.addStretch()
        layout.addWidget(QLabel("Industrial Machine Vision Inspection"))

    @staticmethod
    def _group(caption: str, value: QLabel) -> QWidget:
        widget = QWidget()
        inner = QHBoxLayout(widget)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(8)
        label = QLabel(caption)
        label.setObjectName("statusCaption")
        value.setObjectName("summaryValue")
        inner.addWidget(label)
        inner.addWidget(value)
        return widget
