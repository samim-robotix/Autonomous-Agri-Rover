"""
Motor Controller for 6-Wheel Rocker-Bogie Differential Drive.
Translates navigation intents (forward, turns, pivots, stops) into low-level PWM signals.
"""

from typing import Union
from .serial_interface import SerialInterface
from .mock_hardware import MockSerialInterface
from ..core.logger import get_rover_logger

logger = get_rover_logger("MOTORS")

class MotorController:
    def __init__(self, serial_iface: Union[SerialInterface, MockSerialInterface], config: dict):
        self.serial = serial_iface
        self.config = config.get("motor", {})
        
        self.cruise_speed = self.config.get("cruise_speed_pwm", 160)
        self.turn_speed = self.config.get("turn_speed_pwm", 140)
        self.slow_speed = self.config.get("slow_speed_pwm", 100)
        self.max_speed = self.config.get("max_speed_pwm", 255)
        self.min_speed = self.config.get("pwm_min", 60)
        
        self.current_left = 0
        self.current_right = 0
        self.is_moving = False

    def forward(self, speed: int = None):
        """Drives all 6 wheels forward."""
        spd = speed if speed is not None else self.cruise_speed
        spd = min(spd, self.max_speed)
        self.current_left = spd
        self.current_right = spd
        self.is_moving = True
        logger.debug(f"Moving FORWARD (PWM: {spd})")
        self.serial.send_move(spd, spd)

    def backward(self, speed: int = None):
        """Drives all 6 wheels backward."""
        spd = speed if speed is not None else self.cruise_speed
        spd = min(spd, self.max_speed)
        self.current_left = -spd
        self.current_right = -spd
        self.is_moving = True
        logger.debug(f"Moving REVERSE (PWM: -{spd})")
        self.serial.send_move(-spd, -spd)

    def turn_left(self, steer_intensity: float = 0.5):
        """
        Steers rover left in a forward arc.
        steer_intensity: 0.0 (straight) to 1.0 (sharp turn)
        """
        intensity = max(0.0, min(1.0, steer_intensity))
        left_spd = int(self.cruise_speed * (1.0 - 0.7 * intensity))
        right_spd = int(min(self.max_speed, self.cruise_speed * (1.0 + 0.3 * intensity)))
        
        self.current_left = left_spd
        self.current_right = right_spd
        self.is_moving = True
        logger.debug(f"Steering LEFT (L: {left_spd}, R: {right_spd})")
        self.serial.send_move(left_spd, right_spd)

    def turn_right(self, steer_intensity: float = 0.5):
        """
        Steers rover right in a forward arc.
        steer_intensity: 0.0 (straight) to 1.0 (sharp turn)
        """
        intensity = max(0.0, min(1.0, steer_intensity))
        left_spd = int(min(self.max_speed, self.cruise_speed * (1.0 + 0.3 * intensity)))
        right_spd = int(self.cruise_speed * (1.0 - 0.7 * intensity))
        
        self.current_left = left_spd
        self.current_right = right_spd
        self.is_moving = True
        logger.debug(f"Steering RIGHT (L: {left_spd}, R: {right_spd})")
        self.serial.send_move(left_spd, right_spd)

    def pivot_left(self, speed: int = None):
        """Spins rover in place counter-clockwise."""
        spd = speed if speed is not None else self.turn_speed
        self.current_left = -spd
        self.current_right = spd
        self.is_moving = True
        logger.info(f"Pivoting LEFT in place (PWM: {spd})")
        self.serial.send_move(-spd, spd)

    def pivot_right(self, speed: int = None):
        """Spins rover in place clockwise."""
        spd = speed if speed is not None else self.turn_speed
        self.current_left = spd
        self.current_right = -spd
        self.is_moving = True
        logger.info(f"Pivoting RIGHT in place (PWM: {spd})")
        self.serial.send_move(spd, -spd)

    def stop(self):
        """Brakes all 6 wheels."""
        self.current_left = 0
        self.current_right = 0
        self.is_moving = False
        logger.debug("Motors STOPPED")
        self.serial.send_stop()
