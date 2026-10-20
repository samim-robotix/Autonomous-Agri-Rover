"""
Standalone Vision Pipeline Diagnostic Tool.
Runs live camera capture, obstacle avoidance segmentation, and leaf disease inference
with real-time side-by-side visualization.
"""

import sys
import time
import yaml
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from src.vision.camera_stream import ThreadedCamera
from src.vision.obstacle_detector import ObstacleDetector
from src.vision.leaf_disease_detector import LeafDiseaseDetector

def main():
    config_path = ROOT / "config" / "rover_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    cam_cfg = config.get("vision", {})
    cam = ThreadedCamera(
        source=cam_cfg.get("camera_source", 0),
        width=cam_cfg.get("frame_width", 640),
        height=cam_cfg.get("frame_height", 480)
    )
    cam.start()

    obs_detector = ObstacleDetector(config)
    disease_detector = LeafDiseaseDetector(config)

    print("\n[VISION PIPELINE TEST STARTED]")
    print(" - Press 'q' to exit")
    print(" - Press 's' to save current snapshot\n")

    prev_time = time.time()
    try:
        while True:
            ret, frame = cam.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # 1. Obstacle Detection
            obs_res = obs_detector.process_frame(frame)
            nav_frame = obs_res["annotated_frame"]
            mask = obs_res["debug_mask"]

            # 2. Leaf Disease Detection
            diseases = disease_detector.detect(frame)
            combined_hud = disease_detector.annotate_frame(nav_frame, diseases)

            # 3. Calculate FPS
            fps = 1.0 / (time.time() - prev_time + 1e-6)
            prev_time = time.time()

            cv2.putText(combined_hud, f"FPS: {fps:.1f}", (frame.shape[1] - 110, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("Agriculture Rover Vision Pipeline Diagnostics", combined_hud)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('s'):
                snap_path = ROOT / f"snapshot_{int(time.time())}.jpg"
                cv2.imwrite(str(snap_path), combined_hud)
                print(f"[SAVED] Screenshot saved to: {snap_path}")

    finally:
        cam.stop()
        cv2.destroyAllWindows()
        print("[INFO] Vision test utility terminated.")

if __name__ == "__main__":
    main()
