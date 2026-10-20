"""
Pan-Tilt Servo Scanner and Fertilizer Spray Pump Controller.
Manages 0-180 degree panoramic search sweep, targeted aiming, and relay pump actuation.
"""

import time
import threading
from typing import Union
from .serial_interface import SerialInterface
from .mock_hardware import MockSerialInterface
from ..core.logger import get_rover_logger

logger = get_rover_logger("SPRAY_PAN")

class PanSprayController:
    def __init__(self, serial_iface: Union[SerialInterface, MockSerialInterface], config: dict):
        self.serial = serial_iface
        self.servo_cfg = config.get("servo_scanner", {})
        self.pump_cfg = config.get("spray_pump", {})

        # Servo configuration
        self.min_angle = self.servo_cfg.get("min_angle", 0)
        self.max_angle = self.servo_cfg.get("max_angle", 180)
        self.home_angle = self.servo_cfg.get("home_angle", 90)
        self.step_degrees = self.servo_cfg.get("step_degrees", 5)
        self.step_delay = self.servo_cfg.get("step_delay_seconds", 0.04)
        self.camera_fov = self.servo_cfg.get("camera_fov_horizontal", 60.0)

        # Pump configuration
        self.spray_duration_sec = self.pump_cfg.get("default_spray_time_sec", 1.5)
        self.cooldown_sec = self.pump_cfg.get("cooldown_sec", 3.0)
        self.pump_enabled = self.pump_cfg.get("enabled", true if "enabled" not in self.pump_cfg else self.pump_cfg["enabled"])

        # Current state
        self.current_angle = self.home_angle
        self.is_scanning = False
        self.scan_direction = 1 # +1 for increasing angle, -1 for decreasing
        self.is_spraying = False
        self.last_spray_time = 0.0

        self._scan_thread: threading.Thread = None
        self._stop_scan_event = threading.Event()
        self._lock = threading.Lock()

        # Initialize to home position
        self.set_angle(self.home_angle)

    def set_angle(self, angle: int):
        """Sets pan servo to specific angle (0 - 180)."""
        clamped = max(self.min_angle, min(self.max_angle, int(angle)))
        self.current_angle = clamped
        self.serial.send_servo(clamped)

    def start_scanning(self):
        """Starts continuous non-blocking 0-180 degree search sweep."""
        with self._lock:
            if self.is_scanning:
                return
            self.is_scanning = True
            self._stop_scan_event.clear()
            self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True, name="PanScanThread")
            self._scan_thread.start()
            logger.info("Started 0-180° pan servo search sweep.")

    def stop_scanning(self):
        """Stops the scanning sweep."""
        with self._lock:
            if not self.is_scanning:
                return
            self._stop_scan_event.set()
            self.is_scanning = False
            logger.info("Paused pan servo search sweep.")

    def _scan_loop(self):
        """Sweeps from min_angle to max_angle and back repeatedly."""
        while not self._stop_scan_event.is_set():
            next_angle = self.current_angle + (self.step_degrees * self.scan_direction)
            if next_angle >= self.max_angle:
                next_angle = self.max_angle
                self.scan_direction = -1
            elif next_angle <= self.min_angle:
                next_angle = self.min_angle
                self.scan_direction = 1

            self.set_angle(next_angle)
            time.sleep(self.step_delay)

    def aim_at_pixel_target(self, target_x_px: int, frame_width: int = 640):
        """
        Calculates horizontal angular offset of detected leaf in camera frame
        and adjusts pan servo directly toward it.
        """
        center_x = frame_width / 2.0
        normalized_offset = (target_x_px - center_x) / center_x # -1.0 to +1.0
        angle_offset = normalized_offset * (self.camera_fov / 2.0)
        
        target_angle = int(self.current_angle - angle_offset)
        logger.info(f"Aiming nozzle toward target (x={target_x_px}px -> angle={target_angle}°)")
        self.set_angle(target_angle)
        time.sleep(0.3) # Wait for servo to settle

    def spray(self, duration_sec: float = None) -> bool:
        """
        Triggers 12V fertilizer pump through relay.
        Enforces cooldown safety to avoid pump overheating and chemical overflow.
        """
        if not self.pump_enabled:
            logger.warning("Spray triggered but pump is DISABLED in configuration.")
            return False

        now = time.time()
        if now - self.last_spray_time < self.cooldown_sec:
            logger.warning(f"Spray cooldown active. Wait {self.cooldown_sec - (now - self.last_spray_time):.1f}s.")
            return False

        dur = duration_sec if duration_sec is not None else self.spray_duration_sec
        duration_ms = int(dur * 1000)

        logger.info(f"🌿 >>> ACTIVATING SPRAY PUMP for {dur:.1f} seconds! <<<")
        self.is_spraying = True
        self.serial.send_spray(duration_ms)
        self.last_spray_time = now

        # Maintain internal state
        time.sleep(dur)
        self.is_spraying = False
        logger.info("Fertilizer spray completed.")
        return True
