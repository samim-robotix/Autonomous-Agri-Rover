"""
Autonomous navigation subsystem for Agriculture Rover.
Integrates monocular vision obstacle avoidance and ultrasonic sensor safety overrides.
"""
from .autonomous_navigator import AutonomousNavigator

__all__ = ["AutonomousNavigator"]
