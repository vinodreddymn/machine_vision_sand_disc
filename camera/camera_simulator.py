"""Uploaded-image-backed camera simulator for future live-workflow testing."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from camera.industrial_camera import IndustrialCamera
from utils.image_utils import load_bgr_image


class CameraSimulator(IndustrialCamera):
    """Cycle through images from a folder as though they were camera frames."""

    def __init__(self, image_folder: str | Path) -> None:
        self.image_folder = Path(image_folder)
        self._images: list[Path] = []
        self._index = 0

    def connect(self) -> None:
        self._images = sorted(
            path for path in self.image_folder.iterdir() if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}
        )
        if not self._images:
            raise RuntimeError(f"No simulator images found in {self.image_folder}")

    def disconnect(self) -> None:
        self._images = []
        self._index = 0

    def grab_frame(self) -> np.ndarray:
        if not self._images:
            raise RuntimeError("CameraSimulator is not connected.")
        image = load_bgr_image(self._images[self._index])
        self._index = (self._index + 1) % len(self._images)
        return image
