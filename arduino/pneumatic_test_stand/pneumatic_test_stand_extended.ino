/*
  Pneumatic Test Stand Controller - Extended Version

  Arduino Uno sketch for controlling pneumatic component tests
  Supports multiple valves, initiators, and safety features

  Hardware Setup (Default Configuration):
  Digital Outputs:
  - Pin 2: Main Valve Control (drives solenoid valve)
  - Pin 7: Bypass Valve Control (optional)
  - Pin 13: Status LED (built-in)

  Digital Inputs:
  - Pin 3: End Position Sensor (initiator/proximity sensor)
  - Pin 4: Initiator 1 (proximity sensor)
  - Pin 5: Initiator 2 (proximity sensor)
  - Pin 6: Emergency Stop (normally closed)

  Analog Inputs:
  - Pin A0: Temperature Sensor (LM35 or similar, 10mV/°C)
  - Pin A1: Pressure Sensor (0-10V = 0-10 bar)

  Serial Protocol:
  - Baudrate: 115200
  - Commands: START, STOP, TRIGGER, READ, STATUS, RESET, CONFIG
  - Responses: OK, ERROR, DATA:{json}, READY:{json}

  Author: Prüfstand Software Team
  Version: 2.0 (Extended)
*/

// ===== PIN DEFINITIONS =====
// Digital Outputs
const int PIN_MAIN_VALVE = 2;      // Main valve control output
const int PIN_BYPASS_VALVE = 7;    // Bypass valve (optional)
const int PIN_STATUS_LED = 13;     // Status LED

// Digital Inputs
const int PIN_SENSOR_INPUT = 3;    // End position sensor
const int PIN_INITIATOR_1 = 4;     // Initiator 1 (proximity)
const int PIN_INITIATOR_2 = 5;     // Initiator 2 (proximity)
const int PIN_EMERGENCY_STOP = 6;  // Emergency stop button (NC)

// Analog Inputs
const int PIN_TEMP_SENSOR = A0;    // Temperature sensor
const int PIN_PRESSURE_SENSOR = A1; // Pressure sensor

// ===== CONFIGURATION =====
const unsigned long SENSOR_TIMEOUT_MS = 5000;  // Max time to wait for sensor
const unsigned long SERIAL_TIMEOUT_MS = 100;   // Serial read timeout
const int SENSOR_DEBOUNCE_MS = 5;              // Debounce delay
const float PRESSURE_MIN_BAR = 2.0;            // Minimum safe pressure
const float PRESSURE_MAX_BAR = 10.0;           // Maximum safe pressure

// ===== STATE VARIABLES =====
bool testRunning = false;
bool emergencyStop = false;
unsigned long cycleCount = 0;

// Valve states
bool mainValveActive = false;
bool bypassValveActive = false;

// Feature enables
bool enableInitiator1 = true;
bool enableInitiator2 = false;
bool enableBypassValve = false;
bool enableEmergencyStop = true;
bool enablePressureMonitoring = true;

// Timing variables
unsigned long cycleStartTime = 0;
unsigned long cycleEndTime = 0;

// Sensor readings
float currentTemperature = 0.0;
float currentPressure = 0.0;
bool initiator1Triggered = false;
bool initiator2Triggered = false;

// ===== SETUP =====
void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.setTimeout(SERIAL_TIMEOUT_MS);

  // Configure output pins
  pinMode(PIN_MAIN_VALVE, OUTPUT);
  pinMode(PIN_BYPASS_VALVE, OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);

  // Configure input pins with pullup
  pinMode(PIN_SENSOR_INPUT, INPUT_PULLUP);
  pinMode(PIN_INITIATOR_1, INPUT_PULLUP);
  pinMode(PIN_INITIATOR_2, INPUT_PULLUP);
  pinMode(PIN_EMERGENCY_STOP, INPUT_PULLUP);

  // Initialize outputs to safe state
  setAllValvesOff();
  digitalWrite(PIN_STATUS_LED, LOW);

  // Initialize state
  testRunning = false;
  emergencyStop = false;
  cycleCount = 0;

  // Signal ready
  delay(100);
  sendStatus();
}

// ===== MAIN LOOP =====
void loop() {
  // Check emergency stop first
  checkEmergencyStop();

  // Read sensors periodically
  readSensors();

  // Update status LED
  updateStatusLED();

  // Process serial commands
  if (Serial.available() > 0) {
    processSerialCommand();
  }

  // Small delay
  delay(10);
}

// ===== EMERGENCY STOP =====
void checkEmergencyStop() {
  if (!enableEmergencyStop) return;

  // Emergency stop button is normally closed (NC)
  // If it opens (HIGH), emergency condition
  if (digitalRead(PIN_EMERGENCY_STOP) == HIGH) {
    if (!emergencyStop) {
      // Emergency stop triggered!
      emergencyStop = true;
      testRunning = false;
      setAllValvesOff();

      // Flash LED rapidly
      for (int i = 0; i < 10; i++) {
        digitalWrite(PIN_STATUS_LED, HIGH);
        delay(100);
        digitalWrite(PIN_STATUS_LED, LOW);
        delay(100);
      }

      Serial.println("ERROR:Emergency stop triggered!");
    }
  } else {
    emergencyStop = false;
  }
}

// ===== SERIAL COMMAND PROCESSING =====
void processSerialCommand() {
  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command.length() == 0) return;

  // Parse command and data
  int colonPos = command.indexOf(':');
  String cmd = (colonPos > 0) ? command.substring(0, colonPos) : command;
  String data = (colonPos > 0) ? command.substring(colonPos + 1) : "";

  // Process command
  if (cmd == "START") {
    handleStartTest();
  }
  else if (cmd == "STOP") {
    handleStopTest();
  }
  else if (cmd == "TRIGGER") {
    handleTriggerCycle();
  }
  else if (cmd == "READ") {
    handleReadSensors();
  }
  else if (cmd == "STATUS") {
    sendStatus();
  }
  else if (cmd == "RESET") {
    handleReset();
  }
  else if (cmd == "CONFIG") {
    handleConfig(data);
  }
  else if (cmd == "VALVE") {
    handleValveControl(data);
  }
  else {
    Serial.println("ERROR:Unknown command");
  }
}

// ===== TEST CONTROL =====
void handleStartTest() {
  if (emergencyStop) {
    Serial.println("ERROR:Emergency stop active");
    return;
  }

  // Check pressure if monitoring enabled
  if (enablePressureMonitoring) {
    readSensors();
    if (currentPressure < PRESSURE_MIN_BAR) {
      Serial.println("ERROR:Pressure too low");
      return;
    }
    if (currentPressure > PRESSURE_MAX_BAR) {
      Serial.println("ERROR:Pressure too high");
      return;
    }
  }

  testRunning = true;
  cycleCount = 0;
  Serial.println("OK");
}

void handleStopTest() {
  testRunning = false;
  setAllValvesOff();
  Serial.println("OK");
}

void handleReset() {
  testRunning = false;
  emergencyStop = false;
  cycleCount = 0;
  setAllValvesOff();
  Serial.println("OK");
}

// ===== TRIGGER CYCLE =====
void handleTriggerCycle() {
  if (!testRunning) {
    Serial.println("ERROR:Test not running");
    return;
  }

  if (emergencyStop) {
    Serial.println("ERROR:Emergency stop active");
    return;
  }

  // Execute one test cycle
  bool success = false;
  float cycleTime = 0.0;
  bool sensorTriggered = false;
  String errorMsg = "";

  // Read all sensors before cycle
  readSensors();
  readInitiators();

  // Check pressure if monitoring enabled
  if (enablePressureMonitoring &&
      (currentPressure < PRESSURE_MIN_BAR || currentPressure > PRESSURE_MAX_BAR)) {
    Serial.println("ERROR:Pressure out of range");
    return;
  }

  // Start timing
  cycleStartTime = micros();

  // Activate main valve
  digitalWrite(PIN_MAIN_VALVE, HIGH);
  mainValveActive = true;

  // Wait for end position sensor (or timeout)
  unsigned long waitStart = millis();
  while ((millis() - waitStart) < SENSOR_TIMEOUT_MS) {
    // Check emergency stop
    if (enableEmergencyStop && digitalRead(PIN_EMERGENCY_STOP) == HIGH) {
      setAllValvesOff();
      Serial.println("ERROR:Emergency stop during cycle");
      return;
    }

    // Check sensor
    if (digitalRead(PIN_SENSOR_INPUT) == LOW) {
      delay(SENSOR_DEBOUNCE_MS);
      if (digitalRead(PIN_SENSOR_INPUT) == LOW) {
        sensorTriggered = true;
        cycleEndTime = micros();
        break;
      }
    }
  }

  // Deactivate valve
  digitalWrite(PIN_MAIN_VALVE, LOW);
  mainValveActive = false;

  // Calculate cycle time
  if (sensorTriggered) {
    cycleTime = (cycleEndTime - cycleStartTime) / 1000.0;
    success = true;
    cycleCount++;
  } else {
    cycleTime = SENSOR_TIMEOUT_MS;
    errorMsg = "Sensor timeout";
  }

  // Read initiators at end
  readInitiators();

  // Send response as JSON
  sendCycleData(cycleTime, sensorTriggered, success, errorMsg);
}

// ===== SENSOR READING =====
void handleReadSensors() {
  readSensors();
  readInitiators();

  Serial.print("DATA:{");
  Serial.print("\"temperature\":");
  Serial.print(currentTemperature, 1);
  Serial.print(",\"pressure\":");
  Serial.print(currentPressure, 2);
  Serial.print(",\"initiator1\":");
  Serial.print(initiator1Triggered ? "true" : "false");
  Serial.print(",\"initiator2\":");
  Serial.print(initiator2Triggered ? "true" : "false");
  Serial.print(",\"emergency_stop\":");
  Serial.print(emergencyStop ? "true" : "false");
  Serial.print(",\"voltage\":");
  Serial.print(readVcc() / 1000.0, 2);
  Serial.println("}");
}

void readSensors() {
  // Temperature (LM35: 10mV per °C)
  int tempRaw = analogRead(PIN_TEMP_SENSOR);
  currentTemperature = (tempRaw * 5000.0 / 1024.0) / 10.0;

  // Pressure (0-5V = 0-10 bar)
  int pressureRaw = analogRead(PIN_PRESSURE_SENSOR);
  currentPressure = (pressureRaw * 5.0 / 1024.0) * 2.0;

  // Limit to reasonable values
  if (currentTemperature < -10 || currentTemperature > 150) {
    currentTemperature = 25.0;
  }
  if (currentPressure < 0 || currentPressure > 15) {
    currentPressure = 0.0;
  }
}

void readInitiators() {
  if (enableInitiator1) {
    initiator1Triggered = (digitalRead(PIN_INITIATOR_1) == LOW);
  }
  if (enableInitiator2) {
    initiator2Triggered = (digitalRead(PIN_INITIATOR_2) == LOW);
  }
}

// ===== CONFIGURATION =====
void handleConfig(String data) {
  // Format: CONFIG:key=value
  int eqPos = data.indexOf('=');
  if (eqPos < 0) {
    Serial.println("ERROR:Invalid config format");
    return;
  }

  String key = data.substring(0, eqPos);
  String value = data.substring(eqPos + 1);

  if (key == "initiator1") {
    enableInitiator1 = (value == "1" || value == "true");
  }
  else if (key == "initiator2") {
    enableInitiator2 = (value == "1" || value == "true");
  }
  else if (key == "bypass") {
    enableBypassValve = (value == "1" || value == "true");
  }
  else if (key == "emergency") {
    enableEmergencyStop = (value == "1" || value == "true");
  }
  else if (key == "pressure_monitor") {
    enablePressureMonitoring = (value == "1" || value == "true");
  }
  else {
    Serial.println("ERROR:Unknown config key");
    return;
  }

  Serial.println("OK");
}

// ===== VALVE CONTROL =====
void handleValveControl(String data) {
  // Format: VALVE:main=1 or VALVE:bypass=0
  int eqPos = data.indexOf('=');
  if (eqPos < 0) {
    Serial.println("ERROR:Invalid valve format");
    return;
  }

  String valve = data.substring(0, eqPos);
  String state = data.substring(eqPos + 1);
  bool activate = (state == "1" || state == "on");

  if (valve == "main") {
    digitalWrite(PIN_MAIN_VALVE, activate ? HIGH : LOW);
    mainValveActive = activate;
  }
  else if (valve == "bypass" && enableBypassValve) {
    digitalWrite(PIN_BYPASS_VALVE, activate ? HIGH : LOW);
    bypassValveActive = activate;
  }
  else {
    Serial.println("ERROR:Unknown valve");
    return;
  }

  Serial.println("OK");
}

void setAllValvesOff() {
  digitalWrite(PIN_MAIN_VALVE, LOW);
  digitalWrite(PIN_BYPASS_VALVE, LOW);
  mainValveActive = false;
  bypassValveActive = false;
}

// ===== STATUS & DATA =====
void sendStatus() {
  Serial.print("READY:{");
  Serial.print("\"running\":");
  Serial.print(testRunning ? "true" : "false");
  Serial.print(",\"cycles\":");
  Serial.print(cycleCount);
  Serial.print(",\"emergency_stop\":");
  Serial.print(emergencyStop ? "true" : "false");
  Serial.print(",\"main_valve\":");
  Serial.print(mainValveActive ? "true" : "false");
  Serial.print(",\"bypass_valve\":");
  Serial.print(bypassValveActive ? "true" : "false");
  Serial.println("}");
}

void sendCycleData(float cycleTime, bool sensorTriggered, bool success, String error) {
  Serial.print("DATA:{");
  Serial.print("\"cycle_time_ms\":");
  Serial.print(cycleTime, 2);
  Serial.print(",\"temperature\":");
  Serial.print(currentTemperature, 1);
  Serial.print(",\"pressure\":");
  Serial.print(currentPressure, 2);
  Serial.print(",\"sensor_triggered\":");
  Serial.print(sensorTriggered ? "true" : "false");
  Serial.print(",\"initiator1\":");
  Serial.print(initiator1Triggered ? "true" : "false");
  Serial.print(",\"initiator2\":");
  Serial.print(initiator2Triggered ? "true" : "false");
  Serial.print(",\"success\":");
  Serial.print(success ? "true" : "false");
  Serial.print(",\"error\":\"");
  Serial.print(error);
  Serial.println("\"}");
}

// ===== STATUS LED =====
void updateStatusLED() {
  if (emergencyStop) {
    // Fast blink for emergency
    digitalWrite(PIN_STATUS_LED, (millis() / 100) % 2);
  }
  else if (testRunning) {
    // Normal blink when running
    digitalWrite(PIN_STATUS_LED, (millis() / 500) % 2);
  }
  else {
    // Solid when idle
    digitalWrite(PIN_STATUS_LED, HIGH);
  }
}

// ===== VCC READING =====
long readVcc() {
  #if defined(__AVR_ATmega32U4__) || defined(__AVR_ATmega1280__) || defined(__AVR_ATmega2560__)
    ADMUX = _BV(REFS0) | _BV(MUX4) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
  #elif defined (__AVR_ATtiny24__) || defined(__AVR_ATtiny44__) || defined(__AVR_ATtiny84__)
    ADMUX = _BV(MUX5) | _BV(MUX0);
  #elif defined (__AVR_ATtiny25__) || defined(__AVR_ATtiny45__) || defined(__AVR_ATtiny85__)
    ADMUX = _BV(MUX3) | _BV(MUX2);
  #else
    ADMUX = _BV(REFS0) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
  #endif

  delay(2);
  ADCSRA |= _BV(ADSC);
  while (bit_is_set(ADCSRA, ADSC));

  uint8_t low  = ADCL;
  uint8_t high = ADCH;

  long result = (high << 8) | low;
  result = 1125300L / result;
  return result;
}

/*
  ===== CIRCUIT DIAGRAM =====

  DIGITAL OUTPUTS:
  D2  (Main Valve) ----[1kΩ]----> MOSFET Gate
                                   |
                        MOSFET ----+---- Valve(+)
                                   |
                                  GND

  D7  (Bypass Valve) - Same as above for second valve
  D13 (Status LED) - Built-in, no external circuit needed

  DIGITAL INPUTS:
  D3  (End Sensor) ----< Initiator Signal >---- [10kΩ to 5V]
  D4  (Initiator 1) --- Same as above
  D5  (Initiator 2) --- Same as above
  D6  (Emergency Stop) - Normally Closed Button between D6 and GND

  ANALOG INPUTS:
  A0  (Temperature) --- LM35 Output (10mV/°C)
  A1  (Pressure) ------ Pressure Sensor (0-5V = 0-10bar)

  POWER:
  Arduino: USB or 7-12V DC
  Valves: External 12V/24V supply (depending on valve specs)
  Sensors: 5V from Arduino or external 12/24V (depending on sensor)

  SAFETY:
  - Add flyback diodes (1N4007) across all inductive loads (valves)
  - Use optocouplers for galvanic isolation in industrial environments
  - Fuse all power supplies appropriately
  - Emergency stop should be hardware-based, not just software
*/
