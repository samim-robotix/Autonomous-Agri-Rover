"""
Autonomous Navigation State Machine.
Fuses monocular vision obstacle detection with ultrasonic emergency braking
to guide the 6-wheel rover safely across crop rows.
"""

import time
from typing import Dict, Any
from ..hardware.motor_controller import MotorController
from ..core.logger import get_rover_logger

logger = get_rover_logger("NAV_BRAIN")

class NavState:
    CRUISING = "CRUISING"
    AVOIDING_LEFT = "AVOIDING_LEFT"
    AVOIDING_RIGHT = "AVOIDING_RIGHT"
    REVERSING = "REVERSING"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    PAUSED_FOR_SPRAY = "PAUSED_FOR_SPRAY"

class AutonomousNavigator:
    def __init__(self, motor_ctrl: MotorController, config: dict):
        self.motors = motor_ctrl
        self.nav_cfg = config.get("navigation", {})
        self.us_cfg = config.get("ultrasonic", {})

        self.emergency_dist_cm = self.us_cfg.get("emergency_stop_cm", 25.0)
        self.slowdown_dist_cm = self.us_cfg.get("slowdown_distance_cm", 45.0)

        self.state = NavState.CRUISING
        self.last_state_change = time.time()
        self.consecutive_blocks = 0

    def update_step(self, vision_data: Dict[str, Any], ultrasonic_dist_cm: float):
        """
        Processes one cycle of navigation sensor inputs and commands motors accordingly.
        """
        # If currently paused for spraying, do not move
        if self.state == NavState.PAUSED_FOR_SPRAY:
            self.motors.stop()
            return

        vis_decision = vision_data.get("decision", "FORWARD")
        steer_intensity = vision_data.get("steer_intensity", 0.5)

        # 1. ULTRASONIC HARDWARE-LEVEL EMERGENCY BRAKE
        if ultrasonic_dist_cm < self.emergency_dist_cm:
            if self.state != NavState.EMERGENCY_STOP and self.state != NavState.REVERSING:
                logger.warning(f"⚠️ ULTRASONIC BRAKE TRIGGERED! (Distance: {ultrasonic_dist_cm:.1f}cm < {self.emergency_dist_cm}cm)")
                self.motors.stop()
                self._transition_to(NavState.EMERGENCY_STOP)
                return

        # 2. EMERGENCY STOP RECOVERY BEHAVIOR
        if self.state == NavState.EMERGENCY_STOP:
            # Reverse away from obstacle
            logger.info("Executing reverse escape maneuver away from obstacle...")
            self.motors.backward(speed=120)
            time.sleep(0.8)
            # Pivot away
            self.motors.pivot_right(speed=130)
            time.sleep(0.6)
            self.motors.stop()
            self._transition_to(NavState.CRUISING)
            return

        # 3. VISION-BASED NAVIGATION CONTROL
        if vis_decision == "FORWARD":
            self.consecutive_blocks = 0
            if ultrasonic_dist_cm < self.slowdown_dist_cm:
                # Creep forward cautiously
                self.motors.forward(speed=self.motors.slow_speed)
            else:
                self.motors.forward(speed=self.motors.cruise_speed)
            self._transition_to(NavState.CRUISING)

        elif vis_decision == "STEER_LEFT":
            self.consecutive_blocks = 0
            self.motors.turn_left(steer_intensity=steer_intensity)
            self._transition_to(NavState.AVOIDING_LEFT)

        elif vis_decision == "STEER_RIGHT":
            self.consecutive_blocks = 0
            self.motors.turn_right(steer_intensity=steer_intensity)
            self._transition_to(NavState.AVOIDING_RIGHT)

        elif vis_decision == "REVERSE":
            self.consecutive_blocks += 1
            logger.warning(f"Vision path completely blocked! Escape maneuver #{self.consecutive_blocks}")
            self._transition_to(NavState.REVERSING)
            self.motors.backward(speed=120)
            time.sleep(1.0)
            # Pivot toward preference
            self.motors.pivot_right(speed=140)
            time.sleep(0.8)
            self.motors.stop()
            self._transition_to(NavState.CRUISING)

    def pause_for_spray(self):
        """Halts rover immediately to allow accurate stationary spraying."""
        self._transition_to(NavState.PAUSED_FOR_SPRAY)
        self.motors.stop()

    def resume_from_spray(self):
        """Resumes cruising after spraying completes."""
        self._transition_to(NavState.CRUISING)

    def _transition_to(self, new_state: str):
        if self.state != new_state:
            logger.info(f"Nav State: [{self.state}] -> [{new_state}]")
            self.state = new_state
            self.last_state_change = time.time()
