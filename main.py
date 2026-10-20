"""
Agriculture Rover - Autonomous Vision Navigation & Targeted Leaf Disease Spraying
Master CLI Entrypoint.
"""

import os
import sys
import argparse
import yaml

from src.core.logger import get_rover_logger
from src.core.mission_controller import MissionController

logger = get_rover_logger("MAIN")

def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found at: {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Autonomous Agriculture Rover - Vision Navigation & Leaf Disease Spray System"
    )
    parser.add_argument(
        "--config", type=str, default="config/rover_config.yaml",
        help="Path to YAML configuration file (default: config/rover_config.yaml)"
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Run in Mock Hardware simulation mode (no physical Arduino or motors required)"
    )
    parser.add_argument(
        "--camera", type=str, default=None,
        help="Camera device index (e.g. 0, 1) or path to a recorded video file"
    )
    parser.add_argument(
        "--port", type=str, default=None,
        help="Microcontroller serial port override (e.g. COM4 or /dev/ttyUSB0)"
    )
    parser.add_argument(
        "--no-spray", action="store_true",
        help="Safety dry-run: disables spray pump relay actuation"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("\n" + "="*70)
    print("   🌱 AUTONOMOUS AGRICULTURE ROVER - AI & VISION CONTROL SYSTEM 🌱")
    print("="*70 + "\n")

    config = load_config(args.config)

    # CLI Overrides
    if args.port:
        config.setdefault("serial", {})["port"] = args.port
    if args.no_spray:
        config.setdefault("spray_pump", {})["enabled"] = False
        logger.info("SAFETY SWITCH: Spray pump physically disabled for this run.")

    cam_source = args.camera
    if cam_source is not None and cam_source.isdigit():
        cam_source = int(cam_source)

    # Initialize and run mission controller
    controller = MissionController(
        config=config,
        use_mock_hardware=args.mock,
        camera_source=cam_source
    )

    try:
        controller.start()
    except Exception as e:
        logger.critical(f"Fatal error in rover mission execution: {e}", exc_info=True)
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
