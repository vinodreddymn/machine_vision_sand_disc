"""Abstract camera contract for future SDK integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class IndustrialCamera(ABC):
    """Small camera boundary suitable for USB, GigE, or simulator implementations."""

    @abstractmethod
    def connect(self) -> None:
        """Open the device connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the device connection."""

    @abstractmethod
    def grab_frame(self) -> np.ndarray:
        """Return one BGR frame."""
