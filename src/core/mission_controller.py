"""
Master Mission Controller for Autonomous Agriculture Rover.
Coordinates vision-based navigation, 0-180° pan servo search sweep,
and targeted fertilizer spraying when leaf disease is detected.
"""

import time
import cv2
import numpy as np
from typing import Optional, Union

from .logger import get_rover_logger
from ..hardware.serial_interface import SerialInterface
from ..hardware.mock_hardware import MockSerialInterface
from ..hardware.motor_controller import MotorController
from ..hardware.pan_spray_controller import PanSprayController
from ..vision.camera_stream import ThreadedCamera
from ..vision.obstacle_detector import ObstacleDetector
from ..vision.leaf_disease_detector import LeafDiseaseDetector
from ..navigation.autonomous_navigator import AutonomousNavigator

logger = get_rover_logger("MISSION")

class MissionController:
    def __init__(self, config: dict, use_mock_hardware: bool = False, camera_source: Optional[Union[int, str]] = None):
        self.config = config
        self.use_mock = use_mock_hardware
        self.running = False

        # 1. Initialize Hardware Interface
        ser_cfg = config.get("serial", {})
        if self.use_mock:
            logger.info("Initializing in MOCK HARDWARE mode.")
            self.serial = MockSerialInterface()
        else:
            self.serial = SerialInterface(
                port=ser_cfg.get("port", "COM3"),
                baud_rate=ser_cfg.get("baud_rate", 115200),
                timeout=ser_cfg.get("timeout_seconds", 1.0),
                auto_detect=ser_cfg.get("auto_detect", True)
            )
            connected = self.serial.connect()
            if not connected:
                logger.warning("Could not establish real hardware connection. Falling back to MOCK mode.")
                self.serial = MockSerialInterface()
                self.use_mock = True

        # 2. Hardware Subsystems
        self.motors = MotorController(self.serial, self.config)
        self.pan_spray = PanSprayController(self.serial, self.config)

        # 3. Vision Subsystems
        cam_cfg = config.get("vision", {})
        cam_src = camera_source if camera_source is not None else cam_cfg.get("camera_source", 0)
        self.camera = ThreadedCamera(
            source=cam_src,
            width=cam_cfg.get("frame_width", 640),
            height=cam_cfg.get("frame_height", 480),
            fps=cam_cfg.get("fps", 30)
        )
        self.obstacle_detector = ObstacleDetector(self.config)
        self.disease_detector = LeafDiseaseDetector(self.config)

        # 4. Navigation Subsystem
        self.navigator = AutonomousNavigator(self.motors, self.config)

        # Telemetry Cache
        self.latest_telemetry = self.serial.telemetry
        self.serial.register_telemetry_callback(self._on_telemetry)

        # Performance & HUD Stats
        self.fps = 0.0
        self.total_sprays = 0

    def _on_telemetry(self, telem: dict):
        self.latest_telemetry = telem

    def start(self):
        """Launches rover mission loop."""
        self.running = True
        logger.info("Starting Agriculture Rover Autonomous Mission...")

        # Start Camera
        self.camera.start()
        time.sleep(1.0) # Warm up camera

        # Start continuous 0-180 degree search sweep
        self.pan_spray.start_scanning()

        # Main Mission Loop
        prev_time = time.time()
        try:
            while self.running:
                loop_start = time.time()

                # 1. Acquire Camera Frame
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    time.sleep(0.01)
                    continue

                # 2. Vision Obstacle Detection
                obstacle_result = self.obstacle_detector.process_frame(frame)

                # 3. Leaf Disease Detection
                disease_detections = self.disease_detector.detect(frame)

                # 4. Check for Leaf Disease & Targeted Spray Routine
                if disease_detections:
                    self._handle_disease_action(disease_detections, frame)
                else:
                    # 5. Autonomous Navigation Step
                    current_dist = self.latest_telemetry.get("distance_cm", 999.0)
                    self.navigator.update_step(obstacle_result, current_dist)

                # 6. Composite Debug / Monitoring HUD
                debug_frame = self._render_hud(obstacle_result["annotated_frame"], disease_detections)
                
                # Show window
                if self.config.get("mission", {}).get("debug_display", True):
                    cv2.imshow("Agriculture Rover - Autonomous Vision HUD", debug_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        logger.info("User requested shutdown ('q' key pressed).")
                        break
                    elif key == ord('s'):
                        logger.info("Manual spray triggered by user ('s' key).")
                        self.pan_spray.spray(1.0)
                    elif key == ord('p'):
                        self.motors.stop()
                        logger.info("Mission paused by user.")

                # Calculate Loop FPS
                elapsed = time.time() - loop_start
                self.fps = 1.0 / (time.time() - prev_time + 1e-6)
                prev_time = time.time()

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received.")
        finally:
            self.stop()

    def _handle_disease_action(self, detections: list, frame: np.ndarray):
        """
        Executes targeted spraying sequence:
        1. Halt Rover
        2. Pause pan sweep
        3. Aim pan servo directly at detected leaf center
        4. Trigger spray pump relay
        5. Resume pan sweep and navigation
        """
        best_target = max(detections, key=lambda d: d.get("confidence", 0.0))
        target_center_x, target_center_y = best_target["target_center"]
        cls_name = best_target["class_name"]
        conf = best_target["confidence"]

        logger.info(f"🎯 TARGET IDENTIFIED: {cls_name} ({conf*100:.1f}%) at (x={target_center_x}, y={target_center_y})")

        # 1. Stop rover immediately
        self.navigator.pause_for_spray()

        # 2. Pause scanning sweep
        self.pan_spray.stop_scanning()

        # 3. Aim pan servo directly toward infected leaf
        frame_width = frame.shape[1]
        self.pan_spray.aim_at_pixel_target(target_center_x, frame_width=frame_width)

        # 4. Trigger Fertilizer Spray Pump
        sprayed = self.pan_spray.spray()
        if sprayed:
            self.total_sprays += 1

        # 5. Resume search sweep and navigation
        self.pan_spray.start_scanning()
        self.navigator.resume_from_spray()

    def _render_hud(self, base_frame: np.ndarray, detections: list) -> np.ndarray:
        """Combines obstacle avoidance annotations, leaf disease boxes, and telemetry HUD."""
        hud = self.disease_detector.annotate_frame(base_frame, detections)
        h, w = hud.shape[:2]

        # Bottom Telemetry Bar
        cv2.rectangle(hud, (0, h - 35), (w, h), (15, 15, 15), -1)

        dist = self.latest_telemetry.get("distance_cm", 0.0)
        servo = self.latest_telemetry.get("servo_angle", 0)
        pump = "ACTIVE" if self.latest_telemetry.get("pump_active", False) else "IDLE"
        l_spd = self.latest_telemetry.get("left_speed", 0)
        r_spd = self.latest_telemetry.get("right_speed", 0)

        telem_str = f"US: {dist:.1f}cm | SERVO: {servo}° | PUMP: {pump} | MOTORS: L{l_spd}/R{r_spd} | SPRAYS: {self.total_sprays} | {self.fps:.1f}FPS"
        cv2.putText(hud, telem_str, (10, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        return hud

    def stop(self):
        """Clean shutdown of all rover actuators and streams."""
        logger.info("Executing safe rover shutdown...")
        self.running = False
        if hasattr(self, 'navigator'):
            self.navigator.pause_for_spray()
        if hasattr(self, 'pan_spray'):
            self.pan_spray.stop_scanning()
        if hasattr(self, 'motors'):
            self.motors.stop()
        if hasattr(self, 'camera'):
            self.camera.stop()
        if hasattr(self, 'serial'):
            self.serial.close()
        cv2.destroyAllWindows()
        logger.info("Agriculture Rover safely deactivated.")
