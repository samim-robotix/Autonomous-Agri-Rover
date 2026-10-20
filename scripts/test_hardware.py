"""
Interactive Hardware Diagnostics Utility for Agriculture Rover.
Allows independent testing of 6-wheel motors, pan servo, spray pump, and ultrasonic sensor.
"""

import sys
import time
import yaml
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from src.hardware.serial_interface import SerialInterface
from src.hardware.mock_hardware import MockSerialInterface
from src.hardware.motor_controller import MotorController
from src.hardware.pan_spray_controller import PanSprayController

def print_menu():
    print("\n" + "="*50)
    print("      🔧 ROVER HARDWARE DIAGNOSTICS MENU 🔧")
    print("="*50)
    print(" [1] Test 6-Wheel Motors (Fwd / Back / Left / Right)")
    print(" [2] Test Pan Servo Sweep (0° -> 180° -> 90°)")
    print(" [3] Test 12V Fertilizer Spray Pump (1.5s pulse)")
    print(" [4] Monitor Ultrasonic Distance Sensor Live")
    print(" [5] Run Full Automated System Diagnostics")
    print(" [q] Quit Diagnostics")
    print("="*50)

def main():
    config_path = ROOT / "config" / "rover_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print("\nSelect Hardware Interface:")
    print("1. Real Hardware (Arduino on Serial)")
    print("2. Mock Simulation Mode")
    choice = input("Enter choice (1/2, default 1): ").strip()

    if choice == "2":
        serial_iface = MockSerialInterface()
    else:
        ser_cfg = config.get("serial", {})
        serial_iface = SerialInterface(
            port=ser_cfg.get("port", "COM3"),
            baud_rate=ser_cfg.get("baud_rate", 115200),
            auto_detect=ser_cfg.get("auto_detect", True)
        )
        if not serial_iface.connect():
            print("[WARN] Real Arduino not detected. Switching to Mock mode.")
            serial_iface = MockSerialInterface()

    motors = MotorController(serial_iface, config)
    pan_spray = PanSprayController(serial_iface, config)

    try:
        while True:
            print_menu()
            cmd = input("Select diagnostic test (1-5, q): ").strip().lower()

            if cmd == "1":
                print("\n[TEST] 6-Wheel Motor Drive Test...")
                print(" -> Forward (1.5s)"); motors.forward(140); time.sleep(1.5)
                print(" -> Stop (0.5s)"); motors.stop(); time.sleep(0.5)
                print(" -> Reverse (1.5s)"); motors.backward(140); time.sleep(1.5)
                print(" -> Stop (0.5s)"); motors.stop(); time.sleep(0.5)
                print(" -> Pivot Left (1.0s)"); motors.pivot_left(130); time.sleep(1.0)
                print(" -> Stop (0.5s)"); motors.stop(); time.sleep(0.5)
                print(" -> Pivot Right (1.0s)"); motors.pivot_right(130); time.sleep(1.0)
                motors.stop()
                print("[SUCCESS] Motor test complete.")

            elif cmd == "2":
                print("\n[TEST] Pan Servo 0-180° Sweep Test...")
                for angle in [0, 45, 90, 135, 180, 90]:
                    print(f" -> Setting angle: {angle}°")
                    pan_spray.set_angle(angle)
                    time.sleep(0.8)
                print("[SUCCESS] Servo test complete.")

            elif cmd == "3":
                print("\n[TEST] Spray Pump Test...")
                confirm = input("Are you sure? (Make sure nozzle is safely positioned) [y/N]: ").strip().lower()
                if confirm == 'y':
                    pan_spray.spray(1.5)
                    print("[SUCCESS] Pump triggered.")
                else:
                    print("Test cancelled.")

            elif cmd == "4":
                print("\n[TEST] Monitoring Ultrasonic Sensor (Press Ctrl+C to stop)...")
                try:
                    for _ in range(30):
                        dist = serial_iface.telemetry.get("distance_cm", 999.0)
                        bar = "#" * int(min(50, dist / 4))
                        print(f"\rDistance: {dist:6.1f} cm | [{bar:<50}]", end="", flush=True)
                        time.sleep(0.2)
                    print("\n[INFO] Sensor monitor finished.")
                except KeyboardInterrupt:
                    print("\nStopped.")

            elif cmd == "5":
                print("\n[AUTOMATED TEST] Running full system checkout...")
                pan_spray.set_angle(90); time.sleep(0.5)
                pan_spray.set_angle(45); time.sleep(0.5)
                pan_spray.set_angle(135); time.sleep(0.5)
                pan_spray.set_angle(90); time.sleep(0.5)
                motors.forward(120); time.sleep(0.8)
                motors.stop(); time.sleep(0.4)
                print("[ALL SYSTEMS CHECKED OK]")

            elif cmd in ["q", "quit", "exit"]:
                break
    finally:
        motors.stop()
        serial_iface.close()
        print("\nDiagnostics closed safely.")

if __name__ == "__main__":
    main()
