"""Visual overlay drawing for operator review and saved evidence images."""

from __future__ import annotations

import cv2
import numpy as np

from config.settings import load_tolerances
from vision.defect_analysis import InspectionResult
from vision.hole_detection import hole_pattern_circle_metrics


def render_overlay(image: np.ndarray, result: InspectionResult) -> np.ndarray:
    """Return a copy of the input image with inspection graphics applied."""
    overlay = image.copy()
    if result.outer_circle:
        cv2.circle(overlay, result.outer_circle.center, result.outer_circle.radius, (0, 220, 255), 2)
        cv2.drawContours(overlay, [result.outer_circle.contour], -1, (255, 180, 0), 1)

    if len(result.holes) >= 3:
        _, ellipse_axis_ratio, pattern_center = hole_pattern_circle_metrics(result.holes)
        min_axis_ratio = load_tolerances()["hole_position"]["min_pattern_ellipse_axis_ratio"]
        hole_points = np.array([hole.center for hole in result.holes], dtype=np.float32)

        if len(result.holes) >= 5 and ellipse_axis_ratio < min_axis_ratio:
            fitted_ellipse = cv2.fitEllipse(hole_points)
            cv2.ellipse(overlay, fitted_ellipse, (0, 0, 255), 2, cv2.LINE_AA)
        elif pattern_center is not None:
            center_x, center_y = pattern_center
            distances = np.linalg.norm(hole_points - np.array(pattern_center, dtype=np.float32), axis=1)
            cv2.circle(
                overlay,
                (round(center_x), round(center_y)),
                round(float(np.mean(distances))),
                (0, 220, 0),
                2,
                cv2.LINE_AA,
            )

    for index, hole in enumerate(result.holes, start=1):
        color = (0, 220, 0) if hole.circularity >= 0.78 else (0, 0, 255)
        cv2.circle(overlay, hole.center, round(hole.diameter / 2), color, 2)
        cv2.putText(
            overlay,
            str(index),
            (hole.center[0] + 4, hole.center[1] - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )

    for defect in result.surface_defects:
        cv2.drawContours(overlay, [defect.contour], -1, (0, 0, 255), 2)

    banner_color = (0, 150, 0) if result.passed else (0, 0, 190)
    cv2.rectangle(overlay, (12, 12), (190, 54), banner_color, -1)
    cv2.putText(
        overlay,
        "PASS" if result.passed else "FAIL",
        (28, 43),
        cv2.FONT_HERSHEY_DUPLEX,
        1.0,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return overlay
