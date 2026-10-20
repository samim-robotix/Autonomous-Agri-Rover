"""
Virtual Agriculture Rover Simulation Runner.
Executes the full rover brain using synthetic field video and mock Arduino hardware.
Can be executed immediately on any PC to verify the entire system end-to-end.
"""

import sys
import time
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from src.core.logger import get_rover_logger
from src.core.mission_controller import MissionController

logger = get_rover_logger("VIRTUAL_SIM")

def main():
    config_path = ROOT / "config" / "rover_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print("\n" + "="*70)
    print(" 🌾 LAUNCHING AGRICULTURE ROVER VIRTUAL SIMULATION 🌾")
    print("="*70)
    print(" - Mode: Simulated Camera + Mock Hardware (Motors, Pan Servo, Spray Pump)")
    print(" - Press 'q' in the window to stop simulation.")
    print(" - Press 's' to manually trigger spray test.\n")

    # Force mock hardware and synthetic camera
    controller = MissionController(
        config=config,
        use_mock_hardware=True,
        camera_source=999 # Non-existent device index forces synthetic field generator
    )

    try:
        controller.start()
    except KeyboardInterrupt:
        logger.info("Simulation halted by user.")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
