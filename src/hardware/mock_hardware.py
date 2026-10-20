"""
Mock Hardware Layer for PC Simulation and Testing.
Simulates Arduino serial communication, motor physics, servo angles, and spray triggers
without needing physical hardware plugged into the machine.
"""

import time
import random
import threading
from typing import Dict, Any, Callable
from ..core.logger import get_rover_logger

logger = get_rover_logger("MOCK_HW")

class MockSerialInterface:
    def __init__(self, port: str = "MOCK", baud_rate: int = 115200, timeout: float = 1.0, auto_detect: bool = False):
        self.port = "MOCK_VIRTUAL_SERIAL"
        self.baud_rate = baud_rate
        self.is_connected = True
        
        self.telemetry: Dict[str, Any] = {
            "distance_cm": 150.0,
            "servo_angle": 90,
            "pump_active": False,
            "left_speed": 0,
            "right_speed": 0,
            "last_update": time.time()
        }
        
        self._telemetry_callbacks: list[Callable[[Dict[str, Any]], None]] = []
        self._running = True
        self._sim_thread = threading.Thread(target=self._telemetry_generator, daemon=True, name="MockTelemetryThread")
        self._sim_thread.start()

    def connect(self) -> bool:
        logger.info("[MOCK] Connected to Virtual Arduino Device.")
        self.is_connected = True
        return True

    def _telemetry_generator(self):
        """Generates realistic telemetry fluctuations."""
        while self._running:
            # Add slight realistic sensor noise to ultrasonic distance
            base_dist = self.telemetry["distance_cm"]
            if self.telemetry["left_speed"] > 0 and self.telemetry["right_speed"] > 0:
                # Rover is moving forward; simulate distance decreasing gradually
                base_dist = max(18.0, base_dist - random.uniform(0.5, 2.0))
                if base_dist <= 22.0:
                    base_dist = random.uniform(120.0, 200.0) # Reset after turn
            else:
                base_dist = random.uniform(110.0, 180.0)

            self.telemetry["distance_cm"] = round(base_dist, 1)
            self.telemetry["last_update"] = time.time()

            for cb in self._telemetry_callbacks:
                try:
                    cb(self.telemetry)
                except Exception:
                    pass
            time.sleep(0.1)

    def send_move(self, left_speed: int, right_speed: int) -> bool:
        self.telemetry["left_speed"] = left_speed
        self.telemetry["right_speed"] = right_speed
        logger.debug(f"[MOCK] Motor PWM applied -> Left: {left_speed}, Right: {right_speed}")
        return True

    def send_stop(self) -> bool:
        self.telemetry["left_speed"] = 0
        self.telemetry["right_speed"] = 0
        logger.debug("[MOCK] Motors HALTED.")
        return True

    def send_servo(self, angle_degrees: int) -> bool:
        self.telemetry["servo_angle"] = angle_degrees
        return True

    def send_spray(self, duration_ms: int = 1500) -> bool:
        logger.info(f"💦 [MOCK HW] PUMP RELAY CLOSED -> SPRAYING FERTILIZER FOR {duration_ms}ms 💦")
        self.telemetry["pump_active"] = True
        
        def reset_pump():
            time.sleep(duration_ms / 1000.0)
            self.telemetry["pump_active"] = False
            logger.info("[MOCK HW] Spray finished, pump relay opened.")
            
        threading.Thread(target=reset_pump, daemon=True).start()
        return True

    def send_pump_manual(self, on: bool) -> bool:
        self.telemetry["pump_active"] = on
        logger.info(f"[MOCK HW] Manual Pump set to {on}")
        return True

    def query_status(self) -> bool:
        return True

    def send_command(self, cmd: str) -> bool:
        logger.debug(f"[MOCK CMD]: {cmd}")
        return True

    def register_telemetry_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self._telemetry_callbacks.append(callback)

    def close(self):
        self._running = False
        logger.info("[MOCK HW] Interface closed.")
