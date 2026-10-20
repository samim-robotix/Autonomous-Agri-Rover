# Agriculture Rover - Circuit, Power Management & Wiring Guide

This document specifies the complete electrical system, power distribution, motor driver configuration, sensor integration, and relay wiring for the 6-wheel rocker-bogie agriculture rover.

---

## 1. System Power Architecture

### Power Rails & Regulators
Agricultural field robots demand isolated power distribution to prevent motor inductive noise and servo brownouts from resetting the Raspberry Pi or Arduino.

```
                     +---------------------------------------+
                     |    12V Main Battery (3S Li-ion /      |
                     |   4S LiFePO4 / 12V 7-10Ah Lead-Acid)  |
                     +-------------------+-------------------+
                                         |
               +-------------------------+-------------------------+
               |                         |                         |
       Direct 12V Rail            Buck Converter #1        Buck Converter #2
       (High Current)             (LM2596 / XL4015)        (LM2596 / 6V 3A)
       [12V Unregulated]          [Step-down to 5.1V 3.5A] [Step-down to 6.0V 3A]
               |                         |                         |
       +-------+-------+                 |                         |
       |               |                 v                         v
+------+-----+  +------+-----+    +--------------+          +--------------+
| Motor      |  | 12V Spray  |    | Raspberry Pi |          | Pan Servo    |
| Drivers    |  | Pump via   |    | 4 / 5        |          | (MG996R      |
| (6 Motors) |  | Relay COM  |    +-------+------+          | High Torque) |
+------------+  +------------+            |                 +--------------+
                                          | USB Data Cable
                                          v
                                  +--------------+
                                  | Arduino /    |
                                  | ESP32 Board  |
                                  +--------------+
```

> **CRITICAL GROUNDING NOTE:** All GND connections (Battery GND, Buck Converter GNDs, Raspberry Pi GND, Arduino GND, and Motor Driver GND) must be tied to a **Common Ground Bus Bar**. Never allow floating grounds.

---

## 2. Pinout Configuration (Arduino Microcontroller)

| Component | Function | Arduino Pin | Notes |
| :--- | :--- | :--- | :--- |
| **Left Motors** | ENA (PWM Speed) | `D5` | Hardware PWM (0-255) |
| **Left Motors** | IN1 (Direction 1) | `D4` | Digital Output |
| **Left Motors** | IN2 (Direction 2) | `D2` | Digital Output |
| **Right Motors** | ENB (PWM Speed) | `D6` | Hardware PWM (0-255) |
| **Right Motors** | IN3 (Direction 1) | `D7` | Digital Output |
| **Right Motors** | IN4 (Direction 2) | `D3` | Hardware PWM (0-255) |
| **Pan Servo** | PWM Signal | `D9` | 0° - 180° sweep |
| **12V Spray Pump**| Relay Trigger | `D8` | Active LOW (LOW=ON) |
| **Ultrasonic** | Trig Pulse | `D12` | 10µs trigger |
| **Ultrasonic** | Echo Read | `D11` | 5V logic |
| **Raspberry Pi** | Serial USB Comms | `USB Port` | 115200 Baud rate |

---

## 3. 6-Wheel Rocker-Bogie Motor Wiring

The 6-wheel rocker-bogie chassis uses 3 DC gear motors per side (skid-steer / differential drive):
- **Left Side Motors (Front-Left, Mid-Left, Rear-Left):**
  - Connect all 3 positive terminals together -> Motor Driver `OUT1`.
  - Connect all 3 negative terminals together -> Motor Driver `OUT2`.
- **Right Side Motors (Front-Right, Mid-Right, Rear-Right):**
  - Connect all 3 positive terminals together -> Motor Driver `OUT3`.
  - Connect all 3 negative terminals together -> Motor Driver `OUT4`.

### Recommended Motor Drivers:
- **L298N (Dual H-Bridge):** Good for small to medium DC gear motors (up to 2A per channel).
- **BTS7960 (43A High Power H-Bridge):** Recommended if using heavy metal high-torque gear motors (e.g. 50-100 RPM Johnson motors).
- **Cytron MDD10A (10A Dual Channel):** Highly efficient, minimal heat dissipation.

---

## 4. Spraying System (12V Diaphragm Pump & Relay)

### Relay Wiring:
- **Relay VCC:** 5V (from Arduino or 5V rail).
- **Relay GND:** Common GND.
- **Relay IN:** Arduino `Pin D8`.
- **Relay COM (Common):** Battery +12V positive rail.
- **Relay NO (Normally Open):** Pump (+) Positive lead.
- **Pump (-) Negative lead:** Battery GND.

> **Flyback Diode Protection:**
> DC diaphragm pumps are strongly inductive. When the relay opens, high voltage kickback can arc the relay contacts and reset the microcontroller.
> Solder a **1N4007 or 1N5408 diode across the pump's DC terminals** (Cathode stripe to Pump (+), Anode to Pump (-)).

---

## 5. Pan Servo & Camera Mount

- The webcam and the spray nozzle are mounted together on a rotating pan bracket driven by an **MG996R metal gear servo**.
- **Servo VCC:** Connect to **Buck Converter #2 (+6.0V)**. *Do NOT power the servo from the Arduino 5V pin!*
- **Servo GND:** Common GND.
- **Servo Signal:** Arduino `Pin D9`.
- **Webcam:** Plugged into **Raspberry Pi USB 3.0 port**.
