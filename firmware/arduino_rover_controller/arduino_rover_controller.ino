/*
 * ==============================================================================
 * Agriculture Rover - Low-Level Microcontroller Firmware
 * Target: Arduino Uno / Mega / Nano / ESP32
 * 
 * Hardware Subsystems:
 *  1. 6-Wheel Rocker-Bogie Differential Drive (Motor Driver PWM & Direction)
 *  2. Pan Servo (0 - 180 degrees sweep for Camera & Spray Nozzle)
 *  3. 12V Fertilizer Spray Pump (Relay Module)
 *  4. HC-SR04 Ultrasonic Sensor (Emergency obstacle braking)
 *  5. Bi-directional Serial Protocol with Raspberry Pi (115200 baud)
 * ==============================================================================
 */

#include <Servo.h>

// ======================= PIN CONFIGURATION =======================
// Motor Driver Pins (Configured for L298N / Cytron / BTS7960)
// Left Motor Bank (3 wheels tied in parallel)
const int PIN_ENA = 5;       // Left Motors PWM Speed (0-255)
const int PIN_IN1 = 4;       // Left Motors Direction 1
const int PIN_IN2 = 2;       // Left Motors Direction 2

// Right Motor Bank (3 wheels tied in parallel)
const int PIN_ENB = 6;       // Right Motors PWM Speed (0-255)
const int PIN_IN3 = 7;       // Right Motors Direction 1
const int PIN_IN4 = 3;       // Right Motors Direction 2

// Pan Servo Pin
const int PIN_SERVO = 9;

// Relay Pin for 12V Spray Pump
const int PIN_RELAY_PUMP = 8;
const bool RELAY_ACTIVE_LOW = true; // Most 5V relay modules trigger on LOW

// HC-SR04 Ultrasonic Sensor Pins
const int PIN_TRIG = 12;
const int PIN_ECHO = 11;

// ======================= GLOBAL STATE & OBJECTS =======================
Servo panServo;

int currentServoAngle = 90;
int targetServoAngle = 90;
bool pumpIsActive = false;
unsigned long pumpTurnOffTime = 0;

int currentLeftSpeed = 0;
int currentRightSpeed = 0;

float ultrasonicDistanceCm = 999.0;
unsigned long lastUltrasonicPingTime = 0;
const unsigned long ULTRASONIC_INTERVAL_MS = 60; // 16 Hz ping rate

unsigned long lastHeartbeatTime = 0;
const unsigned long SERIAL_WATCHDOG_TIMEOUT_MS = 1500; // Stop rover if Pi disconnects

// Serial command buffer
String inputBuffer = "";
bool stringComplete = false;

// ======================= MOTOR CONTROL HELPERS =======================
void setLeftMotors(int speed) {
  // speed: -255 to 255
  speed = constrain(speed, -255, 255);
  currentLeftSpeed = speed;

  if (speed > 0) {
    digitalWrite(PIN_IN1, HIGH);
    digitalWrite(PIN_IN2, LOW);
    analogWrite(PIN_ENA, speed);
  } else if (speed < 0) {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, HIGH);
    analogWrite(PIN_ENA, abs(speed));
  } else {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);
    analogWrite(PIN_ENA, 0);
  }
}

void setRightMotors(int speed) {
  // speed: -255 to 255
  speed = constrain(speed, -255, 255);
  currentRightSpeed = speed;

  if (speed > 0) {
    digitalWrite(PIN_IN3, HIGH);
    digitalWrite(PIN_IN4, LOW);
    analogWrite(PIN_ENB, speed);
  } else if (speed < 0) {
    digitalWrite(PIN_IN3, LOW);
    digitalWrite(PIN_IN4, HIGH);
    analogWrite(PIN_ENB, abs(speed));
  } else {
    digitalWrite(PIN_IN3, LOW);
    digitalWrite(PIN_IN4, LOW);
    analogWrite(PIN_ENB, 0);
  }
}

void stopAllMotors() {
  setLeftMotors(0);
  setRightMotors(0);
}

// ======================= PUMP & RELAY HELPERS =======================
void setPumpState(bool turnOn) {
  pumpIsActive = turnOn;
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(PIN_RELAY_PUMP, turnOn ? LOW : HIGH);
  } else {
    digitalWrite(PIN_RELAY_PUMP, turnOn ? HIGH : LOW);
  }
}

void triggerTimedSpray(unsigned long durationMs) {
  setPumpState(true);
  pumpTurnOffTime = millis() + durationMs;
}

// ======================= SERVO HELPERS =======================
void setPanAngle(int angle) {
  angle = constrain(angle, 0, 180);
  currentServoAngle = angle;
  panServo.write(angle);
}

// ======================= ULTRASONIC SENSOR =======================
void updateUltrasonicSensor() {
  unsigned long now = millis();
  if (now - lastUltrasonicPingTime < ULTRASONIC_INTERVAL_MS) {
    return;
  }
  lastUltrasonicPingTime = now;

  // Non-blocking trigger pulse
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  // Measure pulse width with timeout (max ~3 meters = ~18ms)
  unsigned long duration = pulseIn(PIN_ECHO, HIGH, 20000);
  if (duration == 0) {
    ultrasonicDistanceCm = 999.0; // Out of range or no echo
  } else {
    // Speed of sound: 343 m/s = 0.0343 cm/microsecond. Divide by 2 for round-trip.
    ultrasonicDistanceCm = (float)(duration * 0.0343) / 2.0;
  }

  // Safety Emergency Brake: If moving forward and obstacle is closer than 25 cm
  if (ultrasonicDistanceCm < 25.0 && (currentLeftSpeed > 0 || currentRightSpeed > 0)) {
    stopAllMotors();
    Serial.print("SAFETY_STOP dist=");
    Serial.println(ultrasonicDistanceCm);
  }
}

// ======================= SERIAL PROTOCOL PARSER =======================
void processSerialCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  lastHeartbeatTime = millis(); // Refresh watchdog timer

  if (cmd.startsWith("MOVE")) {
    // Expected format: MOVE <left_speed> <right_speed>
    int firstSpace = cmd.indexOf(' ');
    int secondSpace = cmd.indexOf(' ', firstSpace + 1);
    if (firstSpace != -1 && secondSpace != -1) {
      int lSpeed = cmd.substring(firstSpace + 1, secondSpace).toInt();
      int rSpeed = cmd.substring(secondSpace + 1).toInt();
      
      // Safety check: Prevent forward motion if ultrasonic sensor is obstructed
      if (ultrasonicDistanceCm < 25.0 && (lSpeed > 0 || rSpeed > 0)) {
        stopAllMotors();
        Serial.println("ERR_OBSTACLE_AHEAD");
        return;
      }

      setLeftMotors(lSpeed);
      setRightMotors(rSpeed);
      Serial.println("ACK MOVE");
    } else {
      Serial.println("ERR_INVALID_MOVE_FORMAT");
    }
  } 
  else if (cmd.equals("STOP")) {
    stopAllMotors();
    Serial.println("ACK STOP");
  } 
  else if (cmd.startsWith("SERVO")) {
    // Expected format: SERVO <angle> (0 - 180)
    int firstSpace = cmd.indexOf(' ');
    if (firstSpace != -1) {
      int angle = cmd.substring(firstSpace + 1).toInt();
      setPanAngle(angle);
      Serial.print("ACK SERVO ");
      Serial.println(currentServoAngle);
    }
  } 
  else if (cmd.startsWith("SPRAY")) {
    // Expected format: SPRAY <duration_ms>
    int firstSpace = cmd.indexOf(' ');
    unsigned long duration = 1500; // default 1.5s
    if (firstSpace != -1) {
      duration = cmd.substring(firstSpace + 1).toInt();
    }
    triggerTimedSpray(duration);
    Serial.print("ACK SPRAY ");
    Serial.println(duration);
  } 
  else if (cmd.startsWith("PUMP")) {
    // Expected format: PUMP ON or PUMP OFF
    if (cmd.endsWith("ON")) {
      setPumpState(true);
      Serial.println("ACK PUMP ON");
    } else if (cmd.endsWith("OFF")) {
      setPumpState(false);
      Serial.println("ACK PUMP OFF");
    }
  } 
  else if (cmd.equals("PING")) {
    Serial.println("PONG");
  } 
  else if (cmd.equals("STATUS")) {
    // Return telemetry string
    Serial.print("TELEMETRY dist=");
    Serial.print(ultrasonicDistanceCm, 1);
    Serial.print(" servo=");
    Serial.print(currentServoAngle);
    Serial.print(" pump=");
    Serial.print(pumpIsActive ? 1 : 0);
    Serial.print(" left=");
    Serial.print(currentLeftSpeed);
    Serial.print(" right=");
    Serial.println(currentRightSpeed);
  } 
  else {
    Serial.print("ERR_UNKNOWN_COMMAND: ");
    Serial.println(cmd);
  }
}

// ======================= ARDUINO SETUP =======================
void setup() {
  Serial.begin(115200);
  inputBuffer.reserve(64);

  // Motor Driver Pin Modes
  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_ENB, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);

  // Relay Pin Mode
  pinMode(PIN_RELAY_PUMP, OUTPUT);
  setPumpState(false); // Make sure pump is off at startup

  // Ultrasonic Pin Modes
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  // Attach Servo
  panServo.attach(PIN_SERVO);
  setPanAngle(90); // Center position

  stopAllMotors();
  lastHeartbeatTime = millis();

  Serial.println("ROVER_FIRMWARE_READY");
}

// ======================= ARDUINO LOOP =======================
void loop() {
  // 1. Process Incoming Serial Characters
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n' || inChar == '\r') {
      if (inputBuffer.length() > 0) {
        processSerialCommand(inputBuffer);
        inputBuffer = "";
      }
    } else {
      inputBuffer += inChar;
    }
  }

  // 2. Handle Timed Spray Duration
  if (pumpIsActive && pumpTurnOffTime > 0) {
    if (millis() >= pumpTurnOffTime) {
      setPumpState(false);
      pumpTurnOffTime = 0;
      Serial.println("EVENT SPRAY_COMPLETED");
    }
  }

  // 3. Update Ultrasonic Distance Readings
  updateUltrasonicSensor();

  // 4. Watchdog Safety Timer
  // If moving and no heartbeat received from Pi for 1.5 seconds, emergency stop
  if ((currentLeftSpeed != 0 || currentRightSpeed != 0) &&
      (millis() - lastHeartbeatTime > SERIAL_WATCHDOG_TIMEOUT_MS)) {
    stopAllMotors();
    Serial.println("WATCHDOG_TRIGGERED_MOTORS_STOPPED");
  }
}
