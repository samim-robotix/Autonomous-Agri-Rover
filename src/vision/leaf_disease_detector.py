"""
Leaf Disease Detection Module.
Uses YOLOv8 Deep Learning object detection for identifying infected crop leaves
with OpenCV heuristic fallback for offline testing and initial deployment.
"""

import os
from typing import List, Dict, Any, Tuple
import cv2
import numpy as np

from ..core.logger import get_rover_logger

logger = get_rover_logger("DISEASE_AI")

class LeafDiseaseDetector:
    def __init__(self, config: dict):
        self.cfg = config.get("vision", {}).get("leaf_disease", {})
        self.model_path = self.cfg.get("model_path", "models/yolov8n_leaf_disease.pt")
        self.conf_threshold = self.cfg.get("confidence_threshold", 0.45)
        self.iou_threshold = self.cfg.get("iou_threshold", 0.40)
        self.device = self.cfg.get("device", "cpu")
        self.target_classes = set(self.cfg.get("target_classes", []))
        
        self.model = None
        self.is_yolo_loaded = False
        
        self._init_model()

    def _init_model(self):
        """Attempts to load YOLOv8 model weights."""
        if os.path.exists(self.model_path):
            try:
                from ultralytics import YOLO
                logger.info(f"Loading YOLOv8 weights from: {self.model_path}")
                self.model = YOLO(self.model_path)
                self.is_yolo_loaded = True
                logger.info("YOLOv8 leaf disease model loaded successfully.")
                return
            except Exception as e:
                logger.warning(f"Error loading YOLO weights ({e}). Initializing OpenCV vision fallback.")
        else:
            logger.info(f"YOLO weights not found at '{self.model_path}'. Using OpenCV heuristic disease detector fallback.")
            self.is_yolo_loaded = False

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs leaf disease detection on the input frame.
        Returns a list of detected infected regions:
        [
          {
            "class_name": "leaf_spot",
            "confidence": 0.88,
            "bbox": (x1, y1, x2, y2),
            "target_center": (center_x, center_y),
            "area": 2500
          }
        ]
        """
        if self.is_yolo_loaded and self.model is not None:
            return self._detect_yolo(frame)
        else:
            return self._detect_opencv_fallback(frame)

    def _detect_yolo(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Inference with YOLOv8."""
        detections = []
        try:
            results = self.model(frame, conf=self.conf_threshold, iou=self.iou_threshold, device=self.device, verbose=False)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    cls_name = self.model.names[cls_id]
                    conf = float(box.conf[0])
                    
                    # If target_classes filter is specified, check inclusion
                    if self.target_classes and cls_name.lower() not in [c.lower() for c in self.target_classes]:
                        continue
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    area = (x2 - x1) * (y2 - y1)

                    detections.append({
                        "class_name": cls_name,
                        "confidence": conf,
                        "bbox": (x1, y1, x2, y2),
                        "target_center": (cx, cy),
                        "area": area
                    })
        except Exception as e:
            logger.error(f"YOLO inference error: {e}")
        return detections

    def _detect_opencv_fallback(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Color/morphological detector detecting necrotic/chlorotic lesions on foliage.
        Identifies yellow/brown disease spots within green leaf contours.
        """
        detections = []
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 1. Mask foliage/leaves (Green spectrum)
        lower_green = np.array([30, 40, 40])
        upper_green = np.array([85, 255, 255])
        leaf_mask = cv2.inRange(hsv, lower_green, upper_green)

        # 2. Mask disease lesions (Yellow/Brown spots)
        lower_lesion = np.array([10, 80, 50])
        upper_lesion = np.array([30, 255, 220])
        lesion_mask = cv2.inRange(hsv, lower_lesion, upper_lesion)

        # Dilate foliage slightly to contain edge lesions
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        leaf_dilated = cv2.dilate(leaf_mask, kernel, iterations=2)

        # Find lesions on or adjacent to leaves
        valid_lesions = cv2.bitwise_and(lesion_mask, leaf_dilated)

        # Clean noise
        cleaned = cv2.morphologyEx(valid_lesions, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 120: # Filter small noise specks
                x, y, w, h = cv2.boundingRect(cnt)
                # Expand box slightly to encompass surrounding leaf
                pad = 15
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(frame.shape[1], x + w + pad)
                y2 = min(frame.shape[0], y + h + pad)

                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                detections.append({
                    "class_name": "leaf_blight_spot",
                    "confidence": min(0.95, 0.55 + (area / 1000.0)),
                    "bbox": (x1, y1, x2, y2),
                    "target_center": (cx, cy),
                    "area": (x2 - x1) * (y2 - y1)
                })

        return detections

    def annotate_frame(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """Draws bounding boxes, labels, and targeting crosshairs onto frame."""
        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            cx, cy = det["target_center"]
            cls_name = det["class_name"]
            conf = det["confidence"]

            # Red target box for disease
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Crosshair at spray target point
            cv2.drawMarker(annotated, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)

            # Label banner
            label = f"{cls_name} {conf:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - 22), (x1 + tw + 6, y1), (0, 0, 255), -1)
            cv2.putText(annotated, label, (x1 + 3, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        if detections:
            cv2.putText(annotated, f"INFECTED LEAVES DETECTED: {len(detections)}", (15, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        return annotated
