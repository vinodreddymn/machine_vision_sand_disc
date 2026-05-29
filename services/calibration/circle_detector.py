"""Circle detection for camera calibration using a reference disc."""

from __future__ import annotations

import cv2
import numpy as np


def detect_calibration_circles(image: np.ndarray) -> dict | None:
    """Detect the outer reference disc and center hole.
    
    Returns a dictionary containing:
    - outer_diameter_px
    - hole_diameter_px
    - overlay_image (base64 encoded jpeg or just the numpy array to be encoded later)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    
    # Simple thresholding, assuming bright background and dark disc
    # For robust industrial detection, we use Canny + Hough
    edges = cv2.Canny(blurred, 50, 150)
    
    # We expect a large outer circle
    height, width = image.shape[:2]
    max_radius = min(height, width) // 2
    
    # HoughCircles for the outer disc
    outer_circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=height // 2,
        param1=100,
        param2=30,
        minRadius=max_radius // 4,
        maxRadius=max_radius
    )
    
    # HoughCircles for the inner hole
    inner_circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=height // 4,
        param1=100,
        param2=20,
        minRadius=10,
        maxRadius=max_radius // 3
    )
    
    if outer_circles is None or inner_circles is None:
        return None
        
    outer_circles = np.uint16(np.around(outer_circles))
    inner_circles = np.uint16(np.around(inner_circles))
    
    # Pick the most prominent ones
    outer = outer_circles[0, 0]
    inner = inner_circles[0, 0]
    
    ox, oy, orad = outer
    ix, iy, irad = inner
    
    overlay = image.copy()
    
    # Draw outer
    cv2.circle(overlay, (ox, oy), orad, (0, 255, 0), 2)
    cv2.circle(overlay, (ox, oy), 2, (0, 0, 255), 3)
    
    # Draw inner
    cv2.circle(overlay, (ix, iy), irad, (255, 0, 0), 2)
    cv2.circle(overlay, (ix, iy), 2, (0, 0, 255), 3)
    
    return {
        "outer_diameter_px": float(orad * 2),
        "hole_diameter_px": float(irad * 2),
        "overlay": overlay
    }
