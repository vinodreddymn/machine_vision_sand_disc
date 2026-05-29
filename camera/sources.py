"""Camera source abstractions for GUI, headless, and future hardware adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np


class CameraSource(ABC):
    """Frame source contract used by the inspection engine."""

    name = "camera"

    @abstractmethod
    def open(self) -> None:
        """Open the source."""

    @abstractmethod
    def close(self) -> None:
        """Close the source."""

    @abstractmethod
    def read(self) -> np.ndarray | None:
        """Read one BGR frame, or None when no frame is available."""


class OpenCVCameraSource(CameraSource):
    """OpenCV-backed source for USB, video file, and future RTSP URLs."""

    def __init__(self, source: int | str, name: str | None = None, loop: bool = False) -> None:
        self.source = source
        self.name = name or f"OpenCV:{source}"
        self.loop = loop
        self._capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        self._capture = cv2.VideoCapture(self.source)
        if not self._capture.isOpened():
            raise RuntimeError(f"Unable to open camera source: {self.source}")

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None

    def read(self) -> np.ndarray | None:
        if self._capture is None:
            return None
        ok, frame = self._capture.read()
        if ok:
            return frame
        if self.loop:
            self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._capture.read()
            return frame if ok else None
        return None


class UsbCameraSource(OpenCVCameraSource):
    def __init__(self, index: int = 0) -> None:
        super().__init__(index, name=f"USB Camera {index}")


class VideoFileSource(OpenCVCameraSource):
    def __init__(self, path: str | Path, loop: bool = True) -> None:
        super().__init__(str(path), name=f"Video File: {Path(path).name}", loop=loop)


class RtspCameraSource(OpenCVCameraSource):
    def __init__(self, url: str) -> None:
        super().__init__(url, name="RTSP Camera")


class IndustrialCameraSource(CameraSource):
    """Placeholder boundary for GigE/SDK-specific camera adapters."""

    name = "Industrial Camera"

    def open(self) -> None:
        raise NotImplementedError("Industrial SDK camera adapter has not been configured.")

    def close(self) -> None:
        return None

    def read(self) -> np.ndarray | None:
        return None
