"""Reusable image display widget with resize-aware scaling."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

from utils.image_utils import bgr_to_qimage


class ImageViewer(QLabel):
    """Display BGR images while preserving aspect ratio."""

    def __init__(self, placeholder: str = "Upload an image to begin inspection") -> None:
        super().__init__(placeholder)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(220, 150)
        self.setObjectName("imageViewer")
        self._pixmap: QPixmap | None = None
        self._placeholder = placeholder

    def set_bgr_image(self, image: np.ndarray) -> None:
        """Set a new image and refresh the scaled view."""
        self._pixmap = QPixmap.fromImage(bgr_to_qimage(image))
        self._refresh_pixmap()

    def clear_image(self, placeholder: str | None = None) -> None:
        """Clear the current image and restore the standby label."""
        self._pixmap = None
        self.clear()
        if placeholder is not None:
            self._placeholder = placeholder
        self.setText(self._placeholder)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt naming convention
        super().resizeEvent(event)
        self._refresh_pixmap()

    def _refresh_pixmap(self) -> None:
        if self._pixmap is None:
            return
        scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled)
