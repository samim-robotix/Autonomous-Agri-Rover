"""
Hardware abstraction layer for Agriculture Rover.
Includes serial communication, motor control, pan-spray actuation, and mock hardware.
"""
from .serial_interface import SerialInterface
from .motor_controller import MotorController
from .pan_spray_controller import PanSprayController
from .mock_hardware import MockSerialInterface

__all__ = [
    "SerialInterface",
    "MotorController",
    "PanSprayController",
    "MockSerialInterface"
]
