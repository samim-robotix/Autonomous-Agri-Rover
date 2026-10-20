"""
Monocular Vision-Based Obstacle Avoidance for Agricultural Field Navigation.
Divides traversable ground plane into 3 spatial zones (Left, Center, Right)
and computes safe navigation headings without requiring ROS 2.
"""

from typing import Dict, Any, Tuple
import cv2
import numpy as np

from ..core.logger import get_rover_logger

logger = get_rover_logger("OBSTACLE_CV")

class ObstacleDetector:
    def __init__(self, config: dict):
        self.cfg = config.get("vision", {}).get("obstacle_detection", {})
        
        self.ground_roi_ratio = self.cfg.get("ground_roi_start_ratio", 0.45)
        self.zone_splits = self.cfg.get("zone_split_ratios", [0.33, 0.66])
        self.density_threshold = self.cfg.get("obstacle_density_threshold", 0.22)
        self.canny_low = self.cfg.get("canny_low", 50)
        self.canny_high = self.cfg.get("canny_high", 150)
        self.kernel_size = self.cfg.get("morphology_kernel_size", 5)

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Processes camera frame and extracts obstacle densities across Left, Center, Right zones.
        Returns steering recommendation and annotated visual frame.
        """
        h, w = frame.shape[:2]
        roi_start_y = int(h * self.ground_roi_ratio)
        roi = frame[roi_start_y:h, 0:w]
        roi_h, roi_w = roi.shape[:2]

        # 1. Grayscale & Blur
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 2. Edge & Gradient Detection
        edges = cv2.Canny(blurred, self.canny_low, self.canny_high)

        # 3. Morphological Dilation to connect broken obstacle edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (self.kernel_size, self.kernel_size))
        dilated = cv2.dilate(edges, kernel, iterations=1)

        # 4. Otsu Adaptive Thresholding to detect prominent terrain anomalies
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Combined obstacle representation
        obstacle_mask = cv2.bitwise_or(dilated, thresh)

        # 5. Segment into Left, Center, Right Zones
        split_left_x = int(roi_w * self.zone_splits[0])
        split_right_x = int(roi_w * self.zone_splits[1])

        left_zone = obstacle_mask[:, 0:split_left_x]
        center_zone = obstacle_mask[:, split_left_x:split_right_x]
        right_zone = obstacle_mask[:, split_right_x:roi_w]

        # 6. Compute Obstacle Occupancy Densities
        left_density = float(np.count_nonzero(left_zone)) / (left_zone.size + 1e-5)
        center_density = float(np.count_nonzero(center_zone)) / (center_zone.size + 1e-5)
        right_density = float(np.count_nonzero(right_zone)) / (right_zone.size + 1e-5)

        # 7. Navigation Decision Logic
        left_blocked = left_density > self.density_threshold
        center_blocked = center_density > self.density_threshold
        right_blocked = right_density > self.density_threshold

        if not center_blocked:
            decision = "FORWARD"
            steer_intensity = 0.0
        elif not left_blocked and (left_density <= right_density):
            decision = "STEER_LEFT"
            steer_intensity = min(1.0, (center_density - self.density_threshold) / 0.3)
        elif not right_blocked and (right_density < left_density):
            decision = "STEER_RIGHT"
            steer_intensity = min(1.0, (center_density - self.density_threshold) / 0.3)
        elif not left_blocked:
            decision = "STEER_LEFT"
            steer_intensity = 0.8
        elif not right_blocked:
            decision = "STEER_RIGHT"
            steer_intensity = 0.8
        else:
            decision = "REVERSE"
            steer_intensity = 1.0

        # 8. Visual Annotations on Output Frame
        annotated = frame.copy()
        
        # Draw ROI Boundary
        cv2.line(annotated, (0, roi_start_y), (w, roi_start_y), (0, 255, 255), 2)
        cv2.putText(annotated, "GROUND ROI", (10, roi_start_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        # Draw Zone Dividers
        cv2.line(annotated, (split_left_x, roi_start_y), (split_left_x, h), (255, 255, 0), 1)
        cv2.line(annotated, (split_right_x, roi_start_y), (split_right_x, h), (255, 255, 0), 1)

        # Color-coded Zone Indicators
        def get_zone_color(blocked: bool):
            return (0, 0, 255) if blocked else (0, 255, 0) # Red if blocked, Green if clear

        # Zone Banners
        cv2.putText(annotated, f"L: {left_density*100:.1f}%", (20, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, get_zone_color(left_blocked), 2)
        cv2.putText(annotated, f"C: {center_density*100:.1f}%", (int(roi_w * 0.42), h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, get_zone_color(center_blocked), 2)
        cv2.putText(annotated, f"R: {right_density*100:.1f}%", (int(roi_w * 0.75), h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, get_zone_color(right_blocked), 2)

        # Top Decision Header
        dec_color = (0, 255, 0) if decision == "FORWARD" else (0, 165, 255) if "STEER" in decision else (0, 0, 255)
        cv2.rectangle(annotated, (w // 2 - 120, 10), (w // 2 + 120, 45), (20, 20, 20), -1)
        cv2.putText(annotated, f"NAV: {decision}", (w // 2 - 100, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, dec_color, 2)

        return {
            "decision": decision,
            "steer_intensity": steer_intensity,
            "zone_densities": {
                "left": left_density,
                "center": center_density,
                "right": right_density
            },
            "annotated_frame": annotated,
            "debug_mask": obstacle_mask
        }
