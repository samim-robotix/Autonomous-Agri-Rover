"""
Interactive Camera & Obstacle Detection Calibration Utility.
Provides OpenCV GUI trackbars to tune Ground ROI, edge thresholds, and zone splits live.
Press 's' to save the calibrated settings directly to config/rover_config.yaml!
"""

import sys
import yaml
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from src.vision.camera_stream import ThreadedCamera
from src.vision.obstacle_detector import ObstacleDetector

def nothing(x):
    pass

def main():
    config_path = ROOT / "config" / "rover_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    cam_cfg = config.get("vision", {})
    obs_cfg = cam_cfg.get("obstacle_detection", {})

    cam = ThreadedCamera(
        source=cam_cfg.get("camera_source", 0),
        width=cam_cfg.get("frame_width", 640),
        height=cam_cfg.get("frame_height", 480)
    )
    cam.start()

    window_name = "Rover Camera Calibration & Tuning (Press 's' to Save, 'q' to Quit)"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    # Initial Trackbar Values
    init_roi = int(obs_cfg.get("ground_roi_start_ratio", 0.45) * 100)
    init_canny_low = int(obs_cfg.get("canny_low", 50))
    init_canny_high = int(obs_cfg.get("canny_high", 150))
    init_threshold = int(obs_cfg.get("obstacle_density_threshold", 0.22) * 100)
    init_left_split = int(obs_cfg.get("zone_split_ratios", [0.33, 0.66])[0] * 100)
    init_right_split = int(obs_cfg.get("zone_split_ratios", [0.33, 0.66])[1] * 100)

    cv2.createTrackbar("ROI Start %", window_name, init_roi, 80, nothing)
    cv2.createTrackbar("Canny Low", window_name, init_canny_low, 255, nothing)
    cv2.createTrackbar("Canny High", window_name, init_canny_high, 255, nothing)
    cv2.createTrackbar("Obstacle Thresh %", window_name, init_threshold, 60, nothing)
    cv2.createTrackbar("Left Split %", window_name, init_left_split, 50, nothing)
    cv2.createTrackbar("Right Split %", window_name, init_right_split, 95, nothing)

    detector = ObstacleDetector(config)

    print("\n[CALIBRATION STARTED]")
    print(" - Adjust trackbar sliders to match your field conditions.")
    print(" - Press 's' to SAVE calibration directly to config file.")
    print(" - Press 'q' to QUIT.\n")

    try:
        while True:
            ret, frame = cam.read()
            if not ret or frame is None:
                continue

            # Read live trackbar values
            roi_ratio = max(0.2, cv2.getTrackbarPos("ROI Start %", window_name) / 100.0)
            c_low = max(5, cv2.getTrackbarPos("Canny Low", window_name))
            c_high = max(c_low + 5, cv2.getTrackbarPos("Canny High", window_name))
            thresh_ratio = max(0.05, cv2.getTrackbarPos("Obstacle Thresh %", window_name) / 100.0)
            left_split = max(0.1, cv2.getTrackbarPos("Left Split %", window_name) / 100.0)
            right_split = max(left_split + 0.1, cv2.getTrackbarPos("Right Split %", window_name) / 100.0)

            # Update detector parameters live
            detector.ground_roi_ratio = roi_ratio
            detector.canny_low = c_low
            detector.canny_high = c_high
            detector.density_threshold = thresh_ratio
            detector.zone_splits = [left_split, right_split]

            # Process
            result = detector.process_frame(frame)
            annotated = result["annotated_frame"]
            mask = result["debug_mask"]

            # Create side-by-side view (Annotated RGB + Obstacle Mask)
            mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            # Resize mask to fit bottom of display if needed
            h, w = frame.shape[:2]
            combined = np.hstack((annotated, cv2.resize(mask_bgr, (w, h))))

            cv2.imshow(window_name, combined)
            key = cv2.waitKey(20) & 0xFF

            if key == ord('s'):
                # Save to rover_config.yaml
                obs_cfg["ground_roi_start_ratio"] = float(round(roi_ratio, 2))
                obs_cfg["canny_low"] = int(c_low)
                obs_cfg["canny_high"] = int(c_high)
                obs_cfg["obstacle_density_threshold"] = float(round(thresh_ratio, 2))
                obs_cfg["zone_split_ratios"] = [float(round(left_split, 2)), float(round(right_split, 2))]
                
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(config, f, sort_keys=False, default_flow_style=False)
                
                print(">>> [SUCCESS] Saved calibrated settings to rover_config.yaml! <<<")
                # Visual banner
                cv2.putText(annotated, "SETTINGS SAVED!", (w // 2 - 100, h // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                cv2.imshow(window_name, np.hstack((annotated, cv2.resize(mask_bgr, (w, h)))))
                cv2.waitKey(500)

            elif key == ord('q'):
                break

    finally:
        cam.stop()
        cv2.destroyAllWindows()
        print("[INFO] Calibration utility closed.")

if __name__ == "__main__":
    main()
