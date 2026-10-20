# 🌱 Autonomous Agriculture Rover

> **6-Wheel Rocker-Bogie Autonomous Navigation & Targeted Leaf Disease Spraying System**  
> *Developed with Pure Python & OpenCV Vision (No ROS2 required) + YOLOv8 AI + Arduino/ESP32 Actuator Control.*

---

## 📋 System Overview

The Agriculture Rover is designed to navigate crop fields autonomously, detect obstacles in rugged terrain, continuously scan crops using a 0–180° pan servo mechanism, and accurately spray fertilizer directly onto infected leaves when plant diseases are identified.

```
                      +-----------------------------+
                      |   Raspberry Pi 4 / 5        |
                      |   (Vision & AI Brain)       |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v                                           v
      +-----------------+                         +-----------------+
      | Web Camera      |                         | Arduino / ESP32 |
      | (USB Video)     |                         | (Actuators)     |
      +--------+--------+                         +---+----+----+---+
               |                                      |    |    |   
               v                                      |    |    |   
    [ Obstacle Detection ]                            |    |    |   
    [ + YOLO Leaf AI     ]                            |    |    |   
               |                                      |    |    |   
               +------------- High-Level ------------+    |    |   
                              Serial Protocol             |    |   
                                                          v    v    v
                                              [6 Motors] [Pan] [Spray Pump]
```

### Key Capabilities
1. **Vision-Based Navigation Without ROS 2:**
   - Ground plane Region of Interest (ROI) extraction.
   - 3-Zone dynamic density analysis (**Left**, **Center**, **Right**).
   - Real-time steering recommendation (`FORWARD`, `STEER_LEFT`, `STEER_RIGHT`, `REVERSE`).
   - Hardware-level emergency stop via front **HC-SR04 ultrasonic sensor**.
2. **Panoramic Leaf Disease Scanning (0°–180°):**
   - Metal-gear pan servo continuously sweeps the top-mounted camera and nozzle across 0° to 180°.
   - YOLOv8 deep learning model spots fungal and bacterial lesions (*blight, rust, leaf spot, mildew, virus*).
3. **Precision Targeted Spraying:**
   - When an infected leaf is detected, the rover pauses, stops the scanning sweep, aligns the nozzle precisely with the target pixel coordinates, and pulses the 12V diaphragm pump via an optocoupler relay.
4. **Mock Hardware Simulation Mode:**
   - Test and develop the full rover software pipeline on any Windows/Mac/Linux laptop without requiring physical robot hardware.

---

## 📂 Project Structure

```
Agriculture Rover/
├── config/
│   └── rover_config.yaml           # Master configuration (pins, speeds, thresholds, YOLO weights)
├── firmware/
│   └── arduino_rover_controller/
│       └── arduino_rover_controller.ino # Complete Arduino C++ firmware (motor PWM, servo, pump relay, ultrasonic)
├── src/
│   ├── core/
│   │   ├── logger.py               # Colorized timestamped logger
│   │   └── mission_controller.py   # Master orchestrator coordinating vision, pan-sweep, and navigation
│   ├── hardware/
│   │   ├── serial_interface.py     # USB serial protocol with auto-reconnect & packet parsing
│   │   ├── motor_controller.py     # 6-wheel rocker-bogie differential drive abstractions
│   │   ├── pan_spray_controller.py # 0-180° sweep & targeted relay sprayer
│   │   └── mock_hardware.py        # Hardware simulation backend for PC testing
│   ├── vision/
│   │   ├── camera_stream.py        # Multi-threaded low-latency camera stream (with synthetic field generator)
│   │   ├── obstacle_detector.py    # Monocular CV 3-zone obstacle avoidance
│   │   └── leaf_disease_detector.py # YOLOv8 detector with OpenCV heuristic fallback
│   └── navigation/
│       └── autonomous_navigator.py # Navigation state machine with ultrasonic safety brake
├── models/
│   ├── download_weights.py         # 1-click YOLOv8 model downloader
│   └── dataset_guide.md            # PlantVillage / Roboflow custom training guide
├── scripts/
│   ├── calibrate_camera.py         # GUI with sliders to calibrate ROI and obstacle thresholds live
│   ├── test_hardware.py            # Diagnostic menu to test motors, servo, pump, and sensor individually
│   └── test_vision_pipeline.py     # Real-time visual debugger for camera, obstacles, and leaf detections
├── simulation/
│   └── test_virtual_rover.py       # Standalone PC simulation runner
├── circuit_and_wiring_guide.md     # Detailed electrical schematics, power rails, and pinouts
├── requirements.txt                # Python dependencies
├── setup_env.bat                   # 1-click Windows setup script
├── setup_env.sh                    # 1-click Raspberry Pi / Linux setup script
├── run_rover.bat                   # 1-click Windows launcher
├── run_rover.sh                    # 1-click Raspberry Pi launcher
└── main.py                         # Master entrypoint CLI
```

---

## 🚀 Quick Start Guide

### Step 1: Environment Setup
**On Windows:**
```bat
setup_env.bat
```
*Or manually:*
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python models\download_weights.py
```

**On Raspberry Pi 4 / 5:**
```bash
chmod +x setup_env.sh run_rover.sh
./setup_env.sh
```

---

### Step 2: Test on PC (Simulation / Mock Mode)
Run the complete rover mission without any physical robot or camera connected:
```bash
python main.py --mock
```
Or run the dedicated virtual simulation:
```bash
python simulation\test_virtual_rover.py
```
- **HUD Keys:**
  - `q`: Safely halt and exit.
  - `s`: Trigger test spray pulse.
  - `p`: Pause rover motors.

---

### Step 3: Deploy to Physical Rover

1. **Flash Firmware to Arduino:**
   - Open `firmware/arduino_rover_controller/arduino_rover_controller.ino` in the Arduino IDE.
   - Select your board (Arduino Uno / Mega / Nano / ESP32) and Port.
   - Click **Upload**.
2. **Calibrate Camera & Obstacle Mask:**
   ```bash
   python scripts\calibrate_camera.py
   ```
   - Adjust trackbars to set your Ground ROI and obstacle sensitivity.
   - Press `s` to save settings directly to `config/rover_config.yaml`.
3. **Run Hardware Diagnostics:**
   ```bash
   python scripts\test_hardware.py
   ```
   - Test motor directions, servo 0–180° sweep, and spray pump pulse.
4. **Launch Autonomous Mission:**
   ```bash
   python main.py
   ```
   *(On Raspberry Pi: `./run_rover.sh`)*

---

## ⚙️ Configuration Reference (`config/rover_config.yaml`)

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `serial.port` | `COM3` / `/dev/ttyUSB0` | Microcontroller USB port |
| `motor.cruise_speed_pwm` | `160` | Normal forward navigation speed (0–255) |
| `servo_scanner.step_degrees` | `5` | Angle step for 0–180° scan sweep |
| `spray_pump.default_spray_time_sec`| `1.5` | Pump on-time when disease spotted |
| `ultrasonic.emergency_stop_cm` | `25.0` | Hardware obstacle collision distance |
| `vision.obstacle_detection.ground_roi_start_ratio`| `0.45` | Lower 55% of camera frame used for path analysis |

---

## 🛠️ Diagnostics & Utilities

| Script | Purpose |
| :--- | :--- |
| `scripts/test_hardware.py` | Interactive CLI menu to test motors, servo, pump, and ultrasonic distance |
| `scripts/calibrate_camera.py` | Live GUI trackbar tool to tune lighting and field thresholds |
| `scripts/test_vision_pipeline.py` | Visual debugger showing 3-zone obstacle masks and YOLO bounding boxes |
| `models/download_weights.py` | Model setup helper |

---

## ⚡ Circuit & Wiring
For detailed schematics, power rail distribution (12V, 5V, 6V), motor driver wiring, and relay flyback diode protection, see [circuit_and_wiring_guide.md](circuit_and_wiring_guide.md).
