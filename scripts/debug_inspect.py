from pathlib import Path
import sys
import cv2
import numpy as np

# Ensure project root is on sys.path so tests and package imports work when run as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from tests.test_pipeline import build_synthetic_disk
from vision.defect_analysis import inspect_disk
from vision.overlay_renderer import render_overlay
from vision.preprocessing import preprocess_image, create_foreground_mask
from vision.circle_detection import detect_outer_circle
from vision.hole_detection import detect_holes
from vision.surface_inspection import detect_surface_defects

img = build_synthetic_disk(with_surface_defect=True)
res = inspect_disk(img)
print('passed', res.passed)
print('outer radius', res.measurements.get('outer_radius_px'))
print('surface_defect_count', res.measurements.get('surface_defect_count'))
print('surface_defect_area_ratio', res.measurements.get('surface_defect_area_ratio'))
print('defects', res.defects)
overlay = render_overlay(img, res)
print('overlay shape', overlay.shape)

# Print intermediate diagnostics
equalized_gray, blurred = preprocess_image(img)
orig_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
mask = create_foreground_mask(blurred)
outer = detect_outer_circle(mask, blurred)
print('outer from detect_outer_circle:', None if outer is None else (outer.center, outer.radius))
holes = detect_holes(equalized_gray, outer)
print('holes detected:', len(holes), [round(h.diameter,1) for h in holes])
# Recreate surface defect pipeline steps to inspect intermediate masks (use original grayscale)
inspection_mask = np.zeros_like(orig_gray)
outer_mask = np.zeros_like(orig_gray)
cv2.circle(outer_mask, outer.center, max(int(outer.radius * 0.88), 1), 255, -1)
cv2.circle(inspection_mask, outer.center, max(int(outer.radius * 0.88), 1), 255, -1)
print('inspection_mask outer-only sample (305,230):', int(inspection_mask[230,305]))
for i, h in enumerate(holes, start=1):
    print(f'hole {i} center={h.center} diameter={h.diameter:.1f} radius_draw={round(h.diameter)}')
    hole_sample_dist = np.hypot(305 - h.center[0], 230 - h.center[1])
    print(f'  sample dist to hole {i}: {hole_sample_dist:.1f}')
    if hole_sample_dist <= round(h.diameter):
        print(f'  sample is inside hole {i} draw radius')
    if hole_sample_dist <= round(h.diameter / 2):
        print(f'  sample is inside hole {i} actual radius')
    cv2.circle(inspection_mask, h.center, round(h.diameter), 0, -1)
hole_mask = cv2.bitwise_and(outer_mask, cv2.bitwise_not(inspection_mask))
print('inspection_mask after holes sample (305,230):', int(inspection_mask[230,305]))
print('hole_mask sample (305,230):', int(hole_mask[230,305]))
valid_pixels = orig_gray[inspection_mask > 0]
print('valid_pixels count:', valid_pixels.size)
if valid_pixels.size:
    nominal_intensity = float(np.median(valid_pixels))
else:
    nominal_intensity = 0.0
print('nominal_intensity', nominal_intensity)
threshold_value = max(0, round(nominal_intensity - 12))
print('threshold_value', threshold_value)
_, dark_anomalies = cv2.threshold(orig_gray, threshold_value, 255, cv2.THRESH_BINARY_INV)
print('dark_anomalies total nonzero:', int(np.count_nonzero(dark_anomalies)))
print('dark_anomalies within mask nonzero:', int(np.count_nonzero(cv2.bitwise_and(dark_anomalies, inspection_mask))))
print('inspection_mask at sample (305,230):', int(inspection_mask[230,305]))
print('outer_mask at sample (305,230):', int(outer_mask[230,305]))
print('hole_mask at sample (305,230):', int(hole_mask[230,305]))
print('inspection_mask sum:', int(np.count_nonzero(inspection_mask)))
print('outer_mask sum:', int(np.count_nonzero(outer_mask)))
print('orig_gray min/max inside mask:', (int(np.min(valid_pixels)) if valid_pixels.size else None, int(np.max(valid_pixels)) if valid_pixels.size else None))
local_background = cv2.morphologyEx(orig_gray, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
blackhat = cv2.subtract(local_background, orig_gray)
_, thin_anomalies = cv2.threshold(blackhat, 8, 255, cv2.THRESH_BINARY)
print('thin_anomalies total nonzero:', int(np.count_nonzero(thin_anomalies)))
print('thin_anomalies within mask nonzero:', int(np.count_nonzero(cv2.bitwise_and(thin_anomalies, inspection_mask))))
anomalies = cv2.bitwise_or(dark_anomalies, thin_anomalies)
anomalies = cv2.bitwise_and(anomalies, inspection_mask)
anomalies = cv2.morphologyEx(anomalies, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
anomalies = cv2.morphologyEx(anomalies, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
contours, _ = cv2.findContours(anomalies, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print('anomaly contours found:', len(contours))
# sample pixel values at synthetic defect center
sx, sy = 305, 230
print('sample orig_gray at (305,230):', int(orig_gray[sy, sx]))
print('sample equalized_gray at (305,230):', int(equalized_gray[sy, sx]))
surface_defects = detect_surface_defects(orig_gray, outer, holes, min_area=80)
print('surface_defects (raw):', len(surface_defects))
