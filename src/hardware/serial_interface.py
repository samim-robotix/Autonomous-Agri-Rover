"""
Serial Interface for Arduino / ESP32 Rover Controller.
Handles packet transmission, telemetry feedback, and watchdog pings.
"""

import time
import threading
from typing import Optional, Dict, Any, Callable
import serial
import serial.tools.list_ports

from ..core.logger import get_rover_logger

logger = get_rover_logger("SERIAL")

class SerialInterface:
    def __init__(self, port: str = "COM3", baud_rate: int = 115200, timeout: float = 1.0, auto_detect: bool = True):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.auto_detect = auto_detect
        
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self._lock = threading.Lock()
        
        # Latest Telemetry State
        self.telemetry: Dict[str, Any] = {
            "distance_cm": 999.0,
            "servo_angle": 90,
            "pump_active": False,
            "left_speed": 0,
            "right_speed": 0,
            "last_update": 0.0
        }
        
        self._telemetry_callbacks: list[Callable[[Dict[str, Any]], None]] = []
        self._rx_thread: Optional[threading.Thread] = None
        self._running = False

    def auto_detect_port(self) -> Optional[str]:
        """Scans system serial ports to find Arduino or USB-Serial devices."""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = p.description.lower()
            hwid = p.hwid.lower()
            # Common Arduino/CH340/FTDI/CP2102 signatures
            if any(sig in desc or sig in hwid for sig in ["arduino", "ch340", "cp210", "ftdi", "usb serial", "acm"]):
                logger.info(f"Auto-detected microcontroller on port: {p.device} ({p.description})")
                return p.device
        if ports:
            logger.info(f"Using first available serial port: {ports[0].device}")
            return ports[0].device
        return None

    def connect(self) -> bool:
        """Establishes connection with Arduino microcontroller."""
        with self._lock:
            target_port = self.port
            if self.auto_detect:
                detected = self.auto_detect_port()
                if detected:
                    target_port = detected

            try:
                logger.info(f"Connecting to Arduino on {target_port} @ {self.baud_rate} baud...")
                self.serial_conn = serial.Serial(target_port, self.baud_rate, timeout=self.timeout)
                time.sleep(2.0) # Allow Arduino bootloader reset
                self.is_connected = True
                self._running = True
                
                # Start listener thread
                self._rx_thread = threading.Thread(target=self._read_loop, daemon=True, name="SerialRxThread")
                self._rx_thread.start()
                
                # Handshake
                self.send_command("PING")
                logger.info(f"Serial connection established on {target_port}")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to serial port {target_port}: {e}")
                self.is_connected = False
                return False

    def _read_loop(self):
        """Background thread reading telemetry and incoming events from Arduino."""
        while self._running and self.serial_conn and self.serial_conn.is_open:
            try:
                line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                self._parse_incoming_line(line)
            except Exception as e:
                if self._running:
                    logger.warning(f"Serial read error: {e}")
                break

    def _parse_incoming_line(self, line: str):
        """Parses lines like: TELEMETRY dist=24.5 servo=90 pump=0 left=160 right=160"""
        if line.startswith("TELEMETRY"):
            parts = line.split()[1:]
            for part in parts:
                if "=" in part:
                    k, v = part.split("=", 1)
                    if k == "dist":
                        self.telemetry["distance_cm"] = float(v)
                    elif k == "servo":
                        self.telemetry["servo_angle"] = int(v)
                    elif k == "pump":
                        self.telemetry["pump_active"] = bool(int(v))
                    elif k == "left":
                        self.telemetry["left_speed"] = int(v)
                    elif k == "right":
                        self.telemetry["right_speed"] = int(v)
            self.telemetry["last_update"] = time.time()
            
            for cb in self._telemetry_callbacks:
                try:
                    cb(self.telemetry)
                except Exception as cb_err:
                    logger.error(f"Telemetry callback error: {cb_err}")

        elif line.startswith("SAFETY_STOP"):
            logger.warning(f"Microcontroller Emergency Braking Triggered: {line}")
            self.telemetry["left_speed"] = 0
            self.telemetry["right_speed"] = 0

        elif line.startswith("EVENT"):
            logger.info(f"Microcontroller Event: {line}")
        elif line.startswith("ACK") or line == "PONG":
            pass # Routine acknowledgment
        else:
            logger.debug(f"[Arduino raw]: {line}")

    def send_command(self, cmd: str) -> bool:
        """Sends command string over serial with newline termination."""
        if not self.is_connected or not self.serial_conn or not self.serial_conn.is_open:
            logger.warning(f"Cannot send command '{cmd}', serial disconnected.")
            return False
        
        with self._lock:
            try:
                formatted = (cmd.strip() + "\n").encode('utf-8')
                self.serial_conn.write(formatted)
                self.serial_conn.flush()
                return True
            except Exception as e:
                logger.error(f"Failed to transmit serial command '{cmd}': {e}")
                self.is_connected = False
                return False

    def send_move(self, left_speed: int, right_speed: int) -> bool:
        """Sends differential motor drive speeds (-255 to 255)."""
        return self.send_command(f"MOVE {int(left_speed)} {int(right_speed)}")

    def send_stop(self) -> bool:
        """Sends emergency stop to all motors."""
        return self.send_command("STOP")

    def send_servo(self, angle_degrees: int) -> bool:
        """Commands pan servo to angle (0 to 180 degrees)."""
        return self.send_command(f"SERVO {int(angle_degrees)}")

    def send_spray(self, duration_ms: int = 1500) -> bool:
        """Commands relay to activate 12V pump for duration_ms."""
        return self.send_command(f"SPRAY {int(duration_ms)}")

    def send_pump_manual(self, on: bool) -> bool:
        """Commands pump ON or OFF manually."""
        return self.send_command(f"PUMP {'ON' if on else 'OFF'}")

    def query_status(self) -> bool:
        """Requests instant status update from Arduino."""
        return self.send_command("STATUS")

    def register_telemetry_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Registers a listener for live telemetry updates."""
        self._telemetry_callbacks.append(callback)

    def close(self):
        """Shuts down connection cleanly."""
        self._running = False
        self.send_stop()
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception:
                pass
        self.is_connected = False
        logger.info("Serial interface closed.")
