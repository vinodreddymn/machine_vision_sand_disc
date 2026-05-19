"""PASS/FAIL, measurement, and defect summary panel."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from vision.defect_analysis import InspectionResult


class ResultPanel(QWidget):
    """Present inspection results in a compact operator-readable layout."""

    def __init__(self, compact: bool = False) -> None:
        super().__init__()
        self.status_label = QLabel("WAITING")
        self.status_label.setObjectName("statusLabel")
        self.defects_label = QLabel("Defect Summary")
        self.defects_label.setObjectName("panelHeading")
        self.defect_list = QListWidget()
        self.defect_list.setSelectionMode(QAbstractItemView.NoSelection)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        if compact:
            self.defect_list.setMaximumHeight(90)
        layout.addWidget(self.defects_label)
        layout.addWidget(self.defect_list)

    def clear_results(self) -> None:
        """Reset the panel when a new source image is loaded."""
        self.status_label.setText("WAITING")
        self.status_label.setProperty("inspectionState", "waiting")
        self.style().unpolish(self.status_label)
        self.style().polish(self.status_label)
        self.defect_list.clear()

    def show_result(self, result: InspectionResult) -> None:
        """Populate the panel from a completed inspection."""
        self.status_label.setText("PASS" if result.passed else "FAIL")
        self.status_label.setProperty("inspectionState", "pass" if result.passed else "fail")
        self.style().unpolish(self.status_label)
        self.style().polish(self.status_label)

        self.defect_list.clear()
        if result.defects:
            self.defect_list.addItems(result.defects)
        else:
            self.defect_list.addItem("No defects detected.")

    def show_skipped(self) -> None:
        """Show that downstream inspection was intentionally bypassed."""
        self.status_label.setText("SKIPPED")
        self.status_label.setProperty("inspectionState", "waiting")
        self.style().unpolish(self.status_label)
        self.style().polish(self.status_label)
        self.defect_list.clear()
        self.defect_list.addItem("Skipped after Station 1 reject.")
