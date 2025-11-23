# Arduino Integration für Pneumatik-Prüfstand

Dieses Verzeichnis enthält die Arduino-Firmware für die Hardware-Steuerung des Pneumatik-Prüfstands.

## 🔧 Hardware-Anforderungen

- **Arduino Uno** (oder kompatibles Board)
- **Pneumatik-Ventil** (Magnetventil, 12V oder 24V)
- **MOSFET oder Relais** für Ventilsteuerung (z.B. IRLZ44N oder 5V-Relais)
- **Initiator/Näherungsschalter** (3-Draht-Sensor)
- **Temperatursensor** LM35 oder ähnlich (optional)
- **Drucksensor** 0-10V oder 0-5V analog (optional)
- **Widerstände** (1kΩ, 10kΩ)
- **Freilaufdiode** 1N4007 für Ventil

## 📐 Schaltplan

### Pin-Belegung

```
Arduino Uno Pin-Konfiguration:
├── Digital Pin 2  → Ventil-Steuerausgang (über MOSFET/Relais)
├── Digital Pin 3  → Sensor-Eingang (Initiator)
├── Digital Pin 13 → Status-LED (eingebaut)
├── Analog Pin A0  → Temperatursensor (LM35)
├── Analog Pin A1  → Drucksensor (0-10V mit Spannungsteiler)
├── 5V             → Sensoren Versorgung
└── GND            → Gemeinsame Masse
```

### Detaillierter Schaltplan

#### 1. Magnetventil-Ansteuerung

```
Arduino Pin 2 ──┬── 1kΩ ──┬── Gate (MOSFET IRLZ44N)
                │          │
                │          └── 10kΩ ──┐
                │                      │
                │          ┌───────────┴─── GND
                │          │
                │     Source (MOSFET)
                │          │
                │          └─────────────── GND
                │
                └── Drain (MOSFET) ──┬── Ventil (-)
                                      │
                      1N4007 Diode ◁──┤ (Kathode zur +24V)
                                      │
                     Ventil (+) ──────┴── Externe Stromversorgung (+12V/+24V)
```

**Komponenten:**
- MOSFET: IRLZ44N (Logic-Level)
- Freilaufdiode: 1N4007
- Gate-Widerstand: 1kΩ
- Pull-Down: 10kΩ

#### 2. Initiator (Näherungsschalter)

```
Initiator (3-Draht):
├── Braun (+ / Brown)   → +24V (externe Versorgung)
├── Blau (- / Blue)     → GND (gemeinsam mit Arduino)
└── Schwarz (Signal)    → Arduino Pin 3 (mit internem Pull-Up)

Falls 5V Sensor:
Sensor Signal ──┬── Arduino Pin 3
                 │
                 └── 10kΩ ── +5V (externes Pull-Up, optional)
```

#### 3. Temperatursensor (LM35)

```
LM35 (TO-92 Gehäuse):
├── Pin 1 (Vcc)    → Arduino +5V
├── Pin 2 (Output) → Arduino A0
└── Pin 3 (GND)    → Arduino GND

Optional: 100nF Kondensator zwischen Vcc und GND (Störfilter)
```

**Umrechnung:** 10mV pro °C (z.B. 250mV = 25°C)

#### 4. Drucksensor (0-10V mit Spannungsteiler)

```
Für 0-10V Drucksensor:

Sensor (+) ──────────────── +24V Versorgung
Sensor (Signal) ──┬── 10kΩ ──┬── Arduino A1
                   │          │
                   │          └── 10kΩ ── GND
                   │
Sensor (-)  ───────┴────────── GND

Spannungsteiler halbiert Spannung: 0-10V → 0-5V
```

**Alternative:** Bei 0-5V Sensor direkt an A1 ohne Spannungsteiler

#### 5. Komplette Verkabelung

```
                    +5V                          +24V
                     │                            │
                     ├───────┐                    │
                     │       │                    │
                   ┌─┴─┐   ┌─┴─┐                ┌─┴─┐
                   │LM35│   │10k│                │Ven│
                   └─┬─┘   └─┬─┘                │til│
                     │       │                  └─┬─┘
    Arduino          │       │                    │
    ┌────────────────┼───────┼────────────────────┼──┐
    │ A0 ◄───────────┘       │              Drain │  │
    │ A1 ◄───────────────────┘   MOSFET ┌────────┘  │
    │ D2 ├────────────► Gate ────────────┤           │
    │ D3 ◄──── Initiator Signal           │          │
    │ 13 ├──►LED                           │          │
    │GND ├──────────────────────────────────┴────GND  │
    └────────────────────────────────────────────────┘
```

## 📝 Arduino-Sketch Upload

### 1. Arduino IDE Installation

1. Laden Sie die Arduino IDE von https://www.arduino.cc/en/software
2. Installieren Sie die IDE für Ihr Betriebssystem

### 2. Sketch hochladen

1. Öffnen Sie `pneumatic_test_stand.ino` in der Arduino IDE
2. Wählen Sie **Tools** → **Board** → **Arduino Uno**
3. Wählen Sie **Tools** → **Port** → Wählen Sie den korrekten COM-Port (z.B. COM3 oder /dev/ttyUSB0)
4. Klicken Sie auf **Upload** (→ Pfeil-Symbol)
5. Warten Sie auf "Done uploading"

### 3. Verbindung testen

1. Öffnen Sie den Serial Monitor (**Tools** → **Serial Monitor**)
2. Stellen Sie die Baudrate auf **115200** ein
3. Sie sollten eine `READY` Nachricht sehen

## 🔌 Serielle Kommunikation

### Protokoll

**Format:** `COMMAND:DATA\n`
**Baudrate:** 115200
**Antworten:** Text-basiert, mit `\n` terminiert

### Befehle

| Befehl | Parameter | Antwort | Beschreibung |
|--------|-----------|---------|--------------|
| `START` | - | `OK` | Startet Test-Modus |
| `STOP` | - | `OK` | Stoppt Test-Modus |
| `TRIGGER` | - | `DATA:{json}` | Führt einen Zyklus aus |
| `READ` | - | `DATA:{json}` | Liest aktuelle Sensoren |
| `STATUS` | - | `READY:{json}` | Gibt Status zurück |
| `RESET` | - | `OK` | Setzt Arduino zurück |

### Antwort-Beispiele

**STATUS:**
```json
READY:{"running":false,"cycles":0}
```

**TRIGGER (erfolgreicher Zyklus):**
```json
DATA:{"cycle_time_ms":123.45,"temperature":25.3,"pressure":6.2,"sensor_triggered":true,"success":true,"error":""}
```

**TRIGGER (Timeout):**
```json
DATA:{"cycle_time_ms":5000.0,"temperature":25.1,"pressure":6.0,"sensor_triggered":false,"success":false,"error":"Sensor timeout"}
```

**READ:**
```json
DATA:{"temperature":25.0,"pressure":6.1,"voltage":4.98}
```

## 🧪 Test ohne Hardware (Simulation)

Die Python-Software kann **auch ohne Arduino** betrieben werden:

```python
# Simulation-Modus (Standard)
test_controller = TestController(db_manager, use_arduino=False)

# Echter Arduino-Modus
test_controller = TestController(db_manager, use_arduino=True)
```

Im Simulation-Modus werden realistische Werte generiert.

## 🔧 Anpassungen für Ihre Hardware

### Sensor-Polarität ändern

Falls Ihr Initiator bei Erkennung HIGH ausgibt (statt LOW):

```cpp
// Zeile ~76 ändern:
if (digitalRead(PIN_SENSOR_INPUT) == HIGH) {  // Statt LOW
```

### Timeout anpassen

```cpp
// Zeile ~23:
const unsigned long SENSOR_TIMEOUT_MS = 5000;  // Auf z.B. 3000 ändern
```

### Sensor-Kalibrierung

**Temperatursensor:**
```cpp
// Zeile ~248-249: Anpassung für andere Sensoren
currentTemperature = (tempRaw * 5000.0 / 1024.0) / 10.0;  // LM35
// Für LM335: currentTemperature = (tempRaw * 5000.0 / 1024.0) / 10.0 - 273.15;
```

**Drucksensor:**
```cpp
// Zeile ~252-253: Anpassung für Ihr Sensor-Range
currentPressure = (pressureRaw * 5.0 / 1024.0) * 2.0;  // 0-5V → 0-10 bar
// Für 0-16 bar: currentPressure = (pressureRaw * 5.0 / 1024.0) * 3.2;
```

## 🛠️ Troubleshooting

### Problem: Arduino wird nicht erkannt

**Lösung:**
- Installieren Sie CH340-Treiber für Clone-Boards
- Überprüfen Sie USB-Kabel (manche sind nur für Laden)
- Versuchen Sie anderen USB-Port

### Problem: Upload schlägt fehl

**Lösung:**
- Stellen Sie sicher, dass kein anderes Programm den Port verwendet
- Schließen Sie Serial Monitor in Arduino IDE
- Schließen Sie die Python-Anwendung
- Drücken Sie Reset-Button am Arduino vor Upload

### Problem: Ventil schaltet nicht

**Lösung:**
- Überprüfen Sie MOSFET-Anschlüsse
- Messen Sie Gate-Spannung (sollte ~5V sein wenn aktiv)
- Prüfen Sie externe Stromversorgung (12V/24V)
- Überprüfen Sie Freilaufdiode-Polarität

### Problem: Sensor wird nicht erkannt

**Lösung:**
- Überprüfen Sie Verkabelung (Braun=+, Blau=-, Schwarz=Signal)
- Prüfen Sie Sensor-Versorgungsspannung (24V für die meisten Initiatoren)
- Testen Sie Sensor-Signal mit Multimeter

### Problem: Falsche Messwerte

**Lösung:**
- Kalibrieren Sie Sensoren im Code
- Prüfen Sie Spannungsteiler-Widerstände
- Überprüfen Sie Masse-Verbindungen

## 📊 LED-Status-Anzeige

- **Dauerhaft an:** Arduino bereit, kein Test
- **Blinkt (1 Hz):** Test läuft
- **Aus:** Fehler oder nicht verbunden

## 🔒 Sicherheitshinweise

⚠️ **WICHTIG:**
- Arbeiten Sie niemals an der Schaltung bei eingeschalteter Stromversorgung
- Verwenden Sie korrekte Schutzdioden bei induktiven Lasten
- Überprüfen Sie alle Spannungen vor dem Anschluss
- Pneumatik kann gefährlich sein - tragen Sie Schutzbrille
- Nicht in Ex-Bereichen verwenden ohne entsprechende Zertifizierung

## 📚 Weiterführende Links

- [Arduino Referenz](https://www.arduino.cc/reference/en/)
- [MOSFET als Schalter Tutorial](https://learn.sparkfun.com/tutorials/transistors)
- [Näherungsschalter Grundlagen](https://www.sick.com/de/de/grundlagen)

## 🆘 Support

Bei Fragen zur Hardware-Integration:
1. Überprüfen Sie die Verdrahtung anhand des Schaltplans
2. Testen Sie mit Serial Monitor in Arduino IDE
3. Öffnen Sie ein Issue auf GitHub mit:
   - Beschreibung des Problems
   - Arduino-Board-Typ
   - Sensor-/Ventil-Typ
   - Fehlermeldungen

---

**Version:** 1.0
**Getestet mit:** Arduino Uno R3, Arduino IDE 2.x
