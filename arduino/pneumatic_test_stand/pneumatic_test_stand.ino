/*
  Pneumatic Test Stand Controller

  Arduino Uno sketch for controlling pneumatic component tests

  Hardware Setup:
  - Digital Pin 2: Valve Control Output (drives solenoid valve)
  - Digital Pin 3: Sensor Input (initiator/proximity sensor)
  - Analog Pin A0: Temperature Sensor (LM35 or similar, 10mV/°C)
  - Analog Pin A1: Pressure Sensor (0-10V = 0-10 bar)
  - Digital Pin 13: Status LED (built-in)

  Serial Protocol:
  - Baudrate: 115200
  - Commands: START, STOP, TRIGGER, READ, STATUS, RESET
  - Responses: OK, ERROR, DATA:{json}, READY:{json}

  Author: Prüfstand Software Team
  Version: 1.0
*/

// Pin definitions
const int PIN_VALVE_OUTPUT = 2;      // Valve control output
const int PIN_SENSOR_INPUT = 3;      // Sensor input (initiator)
const int PIN_TEMP_SENSOR = A0;      // Temperature sensor (analog)
const int PIN_PRESSURE_SENSOR = A1;  // Pressure sensor (analog)
const int PIN_STATUS_LED = 13;       // Status LED

// Configuration
const unsigned long SENSOR_TIMEOUT_MS = 5000;  // Max time to wait for sensor
const unsigned long SERIAL_TIMEOUT_MS = 100;   // Serial read timeout
const int SENSOR_DEBOUNCE_MS = 5;              // Debounce delay

// State variables
bool testRunning = false;
unsigned long cycleCount = 0;
String inputBuffer = "";

// Timing variables
unsigned long cycleStartTime = 0;
unsigned long cycleEndTime = 0;

// Sensor readings
float currentTemperature = 0.0;
float currentPressure = 0.0;


void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.setTimeout(SERIAL_TIMEOUT_MS);

  // Configure pins
  pinMode(PIN_VALVE_OUTPUT, OUTPUT);
  pinMode(PIN_SENSOR_INPUT, INPUT_PULLUP);  // Use internal pullup
  pinMode(PIN_STATUS_LED, OUTPUT);

  // Initialize outputs to safe state
  digitalWrite(PIN_VALVE_OUTPUT, LOW);
  digitalWrite(PIN_STATUS_LED, LOW);

  // Initialize
  testRunning = false;
  cycleCount = 0;

  // Signal ready
  delay(100);
  sendStatus();
}


void loop() {
  // Read sensors periodically
  readSensors();

  // Update status LED
  updateStatusLED();

  // Process serial commands
  if (Serial.available() > 0) {
    processSerialCommand();
  }

  // Small delay to prevent overwhelming the serial
  delay(10);
}


void processSerialCommand() {
  // Read until newline
  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command.length() == 0) {
    return;
  }

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
  else {
    Serial.println("ERROR:Unknown command");
  }
}


void handleStartTest() {
  testRunning = true;
  cycleCount = 0;
  Serial.println("OK");
}


void handleStopTest() {
  testRunning = false;
  digitalWrite(PIN_VALVE_OUTPUT, LOW);  // Ensure valve is off
  Serial.println("OK");
}


void handleTriggerCycle() {
  if (!testRunning) {
    Serial.println("ERROR:Test not running");
    return;
  }

  // Execute one test cycle
  bool success = false;
  float cycleTime = 0.0;
  bool sensorTriggered = false;
  String errorMsg = "";

  // Read sensors before cycle
  readSensors();

  // Start timing
  cycleStartTime = micros();

  // Activate valve
  digitalWrite(PIN_VALVE_OUTPUT, HIGH);

  // Wait for sensor to trigger (or timeout)
  unsigned long waitStart = millis();
  while ((millis() - waitStart) < SENSOR_TIMEOUT_MS) {
    if (digitalRead(PIN_SENSOR_INPUT) == LOW) {  // Sensor active (pulled low)
      delay(SENSOR_DEBOUNCE_MS);  // Debounce
      if (digitalRead(PIN_SENSOR_INPUT) == LOW) {
        sensorTriggered = true;
        cycleEndTime = micros();
        break;
      }
    }
  }

  // Deactivate valve
  digitalWrite(PIN_VALVE_OUTPUT, LOW);

  // Calculate cycle time
  if (sensorTriggered) {
    cycleTime = (cycleEndTime - cycleStartTime) / 1000.0;  // Convert to ms
    success = true;
    cycleCount++;
  } else {
    cycleTime = SENSOR_TIMEOUT_MS;
    errorMsg = "Sensor timeout";
  }

  // Send response as JSON
  Serial.print("DATA:{");
  Serial.print("\"cycle_time_ms\":");
  Serial.print(cycleTime, 2);
  Serial.print(",\"temperature\":");
  Serial.print(currentTemperature, 1);
  Serial.print(",\"pressure\":");
  Serial.print(currentPressure, 2);
  Serial.print(",\"sensor_triggered\":");
  Serial.print(sensorTriggered ? "true" : "false");
  Serial.print(",\"success\":");
  Serial.print(success ? "true" : "false");
  Serial.print(",\"error\":\"");
  Serial.print(errorMsg);
  Serial.println("\"}");
}


void handleReadSensors() {
  readSensors();

  Serial.print("DATA:{");
  Serial.print("\"temperature\":");
  Serial.print(currentTemperature, 1);
  Serial.print(",\"pressure\":");
  Serial.print(currentPressure, 2);
  Serial.print(",\"voltage\":");

  // Calculate supply voltage from Vcc
  float voltage = readVcc() / 1000.0;
  Serial.print(voltage, 2);

  Serial.println("}");
}


void sendStatus() {
  Serial.print("READY:{");
  Serial.print("\"running\":");
  Serial.print(testRunning ? "true" : "false");
  Serial.print(",\"cycles\":");
  Serial.print(cycleCount);
  Serial.println("}");
}


void handleReset() {
  testRunning = false;
  cycleCount = 0;
  digitalWrite(PIN_VALVE_OUTPUT, LOW);
  Serial.println("OK");
}


void readSensors() {
  // Read temperature sensor (LM35: 10mV per degree Celsius)
  // Arduino ADC: 0-1023 = 0-5V
  // For LM35: Temp = (analogRead * 5000 / 1024) / 10
  int tempRaw = analogRead(PIN_TEMP_SENSOR);
  currentTemperature = (tempRaw * 5000.0 / 1024.0) / 10.0;

  // Read pressure sensor (assuming 0-5V = 0-10 bar linear)
  int pressureRaw = analogRead(PIN_PRESSURE_SENSOR);
  currentPressure = (pressureRaw * 5.0 / 1024.0) * 2.0;  // 0-5V -> 0-10 bar

  // Limit to reasonable values
  if (currentTemperature < -10 || currentTemperature > 150) {
    currentTemperature = 25.0;  // Default to room temp if unreasonable
  }

  if (currentPressure < 0 || currentPressure > 15) {
    currentPressure = 0.0;  // Default to 0 if unreasonable
  }
}


void updateStatusLED() {
  if (testRunning) {
    // Blink when running
    digitalWrite(PIN_STATUS_LED, (millis() / 500) % 2);
  } else {
    // Solid when idle
    digitalWrite(PIN_STATUS_LED, HIGH);
  }
}


long readVcc() {
  // Read 1.1V reference against AVcc
  // set the reference to Vcc and the measurement to the internal 1.1V reference
  #if defined(__AVR_ATmega32U4__) || defined(__AVR_ATmega1280__) || defined(__AVR_ATmega2560__)
    ADMUX = _BV(REFS0) | _BV(MUX4) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
  #elif defined (__AVR_ATtiny24__) || defined(__AVR_ATtiny44__) || defined(__AVR_ATtiny84__)
    ADMUX = _BV(MUX5) | _BV(MUX0);
  #elif defined (__AVR_ATtiny25__) || defined(__AVR_ATtiny45__) || defined(__AVR_ATtiny85__)
    ADMUX = _BV(MUX3) | _BV(MUX2);
  #else
    ADMUX = _BV(REFS0) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
  #endif

  delay(2); // Wait for Vref to settle
  ADCSRA |= _BV(ADSC); // Start conversion
  while (bit_is_set(ADCSRA, ADSC)); // measuring

  uint8_t low  = ADCL; // must read ADCL first - it then locks ADCH
  uint8_t high = ADCH; // unlocks both

  long result = (high << 8) | low;

  result = 1125300L / result; // Calculate Vcc (in mV); 1125300 = 1.1*1023*1000
  return result; // Vcc in millivolts
}


/*
  Circuit Diagram Notes:

  Temperature Sensor (LM35):
  - Pin 1 (Vcc) -> Arduino 5V
  - Pin 2 (Output) -> Arduino A0
  - Pin 3 (GND) -> Arduino GND

  Pressure Sensor (0-10V):
  - Use voltage divider if sensor outputs 0-10V
  - For 0-10V sensor: R1=10kΩ to sensor, R2=10kΩ to GND
  - Middle point to Arduino A1
  - Or use 0-5V sensor directly

  Solenoid Valve:
  - Use MOSFET or relay for switching
  - Arduino Pin 2 -> MOSFET Gate (through 1kΩ resistor)
  - MOSFET Source -> GND
  - MOSFET Drain -> Valve negative terminal
  - Valve positive terminal -> External power supply (12V/24V)
  - Add flyback diode across valve (1N4007 or similar)

  Initiator/Proximity Sensor:
  - 3-wire sensor: Brown(+), Blue(-), Black(signal)
  - Signal wire -> Arduino Pin 3
  - Use internal pullup (configured in code)
  - Or add external 10kΩ pullup resistor

  Status LED:
  - Built-in LED on Pin 13 (no external components needed)
*/
