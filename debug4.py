import cv2
from config.settings import load_tolerances
from vision.preprocessing import preprocess_image, create_foreground_mask
from vision.circle_detection import detect_outer_circle

def test():
    cap = cv2.VideoCapture("industrial_disk_inspection.mp4")
    if not cap.isOpened():
        print("Failed to open video")
        return
        
    tolerances = load_tolerances()
    radius_limits = tolerances.get("outer_radius_px", {})
    
    empty_frames = 0
    current_decision = "WAITING"
    inspected_count = 0
    last_x = -1
    
    frames = 0
    while cap.isOpened() and frames < 1500:
        ret, frame = cap.read()
        if not ret: break
        frames += 1
        
        gray, blurred = preprocess_image(frame)
        mask = create_foreground_mask(blurred)
        outer = detect_outer_circle(mask, blurred)
        
        within_radius = False
        if outer is not None:
            within_radius = True
            if radius_limits:
                within_radius = radius_limits.get("min", 0) <= outer.radius <= radius_limits.get("max", 9999)
                
        if within_radius:
            disc_x = outer.center[0]
            
            if last_x != -1 and disc_x < last_x - 50 and current_decision != "WAITING":
                current_decision = "WAITING"
                empty_frames = 0
                last_x = -1
                print(f"Frame {frames}: RESET part (X jump)")

            empty_frames = 0
            last_x = disc_x
            
            if current_decision == "WAITING":
                inspected_count += 1
                current_decision = "PASS" # Simulate inspection
                print(f"Frame {frames}: INSPECTED disc! Radius: {outer.radius}")
        else:
            if current_decision != "WAITING":
                empty_frames += 1
                if empty_frames > 10:
                    current_decision = "WAITING"
                    empty_frames = 0
                    last_x = -1
                    print(f"Frame {frames}: RESET part (Empty)")
                
    print(f"Total inspected: {inspected_count} in {frames} frames.")
    cap.release()

if __name__ == "__main__":
    test()
