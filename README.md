# 🔧 Pneumatik-Prüfstand Software

Eine umfassende Software-Lösung für automatisierte Tests von Pneumatik-Komponenten (Pneumatikzylinder, Magnetventile, Initiatoren) mit Trend-Analyse, Verschleißerkennung und automatischer Berichterstellung.

## 🎯 Features

### Kern-Funktionalitäten
- ✅ **Automatisierte Test-Durchführung** für Pneumatikzylinder, Magnetventile und Initiatoren
- ✅ **Arduino-Integration** für echte Hardware-Steuerung mit seriellem Protokoll
- ✅ **Echtzeit-Überwachung** von Schaltzeiten, Temperaturen und Drücken
- ✅ **Umfangreiche Datenbank** für Komponenten-Verwaltung
- ✅ **Moderne grafische Benutzeroberfläche** (PyQt5)
- ✅ **Automatische Trend-Erkennung** und Verschleißanalyse
- ✅ **Vorhersage der Restlaufzeit** während laufender Tests
- ✅ **Professionelle HTML-Berichte** mit Diagrammen und Statistiken
- ✅ **Simulation-Modus** für Tests ohne Hardware

### Test-Parameter
- Schaltzeiten (ms)
- Anzahl Schaltwiederholungen
- Temperatur-Überwachung (°C)
- Druck-Überwachung (bar)
- Verschleiß-Erkennung
- Fehler-Logging

### Analyse & Reporting
- **Trend-Analyse**: Erkennung von Performance-Verschlechterungen
- **Anomalie-Erkennung**: Automatische Identifikation ungewöhnlicher Messwerte
- **Performance-Score**: Bewertung des Komponenten-Zustands (0-100)
- **Verschleiß-Rate**: Berechnung der Degradation über Zeit
- **Prognose**: Vorhersage der verbleibenden Lebensdauer
- **HTML-Berichte**: Detaillierte, exportierbare Berichte mit Visualisierungen

### Datenbank-Features
Für jede Komponente werden gespeichert:
- Bezeichnung 1 & 2
- Materialnummer
- Herstellernummer
- Komponenten-Typ
- Status (Aktiv, Im Test, Ausgefallen, etc.)
- Anzahl Tests gesamt
- Summe Schaltzyklen gesamt
- Summe Betriebsstunden/-minuten

## 🤖 Arduino-Integration

Die Software kann mit **echter Hardware** über Arduino Uno gesteuert werden!

### Hardware-Modus
- **Arduino Uno** verbunden via USB/Serial
- Echte Ventilsteuerung über MOSFET/Relais
- Messung echter Schaltzeiten mit µs-Genauigkeit
- Sensor-Überwachung (Initiatoren, Temperatur, Druck)
- Umfangreiche Dokumentation in `arduino/README.md`

### Simulation-Modus (Standard)
- Keine Hardware erforderlich
- Realistische Simulationsdaten
- Ideal für Entwicklung und Tests

**Siehe:** [Arduino Setup-Anleitung](arduino/README.md)

## 🚀 Installation

### Voraussetzungen
- Python 3.8 oder höher
- pip (Python Package Manager)
- **Optional:** Arduino Uno mit hochgeladenem Sketch (siehe `arduino/`)

### Setup

1. **Repository klonen:**
```bash
git clone <repository-url>
cd Pr-fstandsoftwareDD
```

2. **Virtuelle Umgebung erstellen (empfohlen):**
```bash
python -m venv venv

# Windows
venv\\Scripts\\activate

# Linux/Mac
source venv/bin/activate
```

3. **Abhängigkeiten installieren:**
```bash
pip install -r requirements.txt
```

## 🎮 Verwendung

### Anwendung starten
```bash
python main.py
```

### Erste Schritte

#### 1. Komponente hinzufügen
1. Navigieren Sie zum Tab **"Komponenten"**
2. Klicken Sie auf **"+ Neue Komponente"**
3. Füllen Sie die Felder aus:
   - Bezeichnung 1 & 2
   - Materialnummer (eindeutig)
   - Herstellernummer
   - Komponenten-Typ
   - Status
4. Speichern Sie die Komponente

#### 2. Test durchführen
1. Wechseln Sie zum Tab **"Test-Steuerung"**
2. Wählen Sie die zu testende Komponente
3. Konfigurieren Sie den Test:
   - Anzahl Zyklen (z.B. 10.000)
   - Intervall in Millisekunden (z.B. 100ms)
4. Klicken Sie auf **"▶ Test Starten"**
5. Beobachten Sie den Fortschritt:
   - Live-Daten (Zyklus, Schaltzeit, Temperatur, Druck)
   - Fortschrittsbalken
   - Verbleibende Zeit und voraussichtlicher Abschluss
6. Test kann pausiert oder gestoppt werden

#### 3. Berichte generieren
1. Navigieren Sie zum Tab **"Berichte"**
2. Wählen Sie eine Komponente
3. Klicken Sie auf **"📄 Bericht Erstellen"**
4. Der HTML-Bericht wird in `data/exports/` gespeichert
5. Öffnen Sie den Bericht im Browser

#### 4. Trend-Analyse durchführen
1. Wechseln Sie zum Tab **"Analyse"**
2. Wählen Sie eine Komponente mit mehreren abgeschlossenen Tests
3. Klicken Sie auf **"📊 Analysieren"**
4. Erhalten Sie detaillierte Insights:
   - Schaltzeit-Trends
   - Verschleiß-Rate
   - Anomalien
   - Performance-Score
   - Lebensdauer-Prognose

## 📊 Dashboard

Das Dashboard zeigt eine Übersicht:
- 📦 **Komponenten gesamt**: Anzahl registrierter Komponenten
- ✅ **Testläufe gesamt**: Durchgeführte Tests
- 🔄 **Schaltzyklen**: Gesamtzahl aller Schaltzyklen
- ⏱️ **Betriebs-Stunden**: Kumulative Testzeit
- 📋 **Letzte Aktivitäten**: Chronologische Test-Historie

## 🗂️ Projektstruktur

```
Pr-fstandsoftwareDD/
├── main.py                          # Haupt-Einstiegspunkt
├── requirements.txt                 # Python-Abhängigkeiten
├── README.md                        # Diese Datei
├── src/                             # Quellcode
│   ├── __init__.py
│   ├── models/                      # Datenmodelle
│   │   ├── __init__.py
│   │   └── component.py             # Component, TestRun, etc.
│   ├── database/                    # Datenbankschicht
│   │   ├── __init__.py
│   │   └── db_manager.py            # SQLite-Manager
│   ├── controllers/                 # Business-Logik
│   │   ├── __init__.py
│   │   ├── test_controller.py       # Test-Steuerung
│   │   └── arduino_controller.py    # Arduino-Kommunikation
│   ├── analysis/                    # Analyse-Module
│   │   ├── __init__.py
│   │   ├── trend_analyzer.py        # Trend-Analyse
│   │   └── remaining_time_predictor.py  # Zeitvorhersage
│   ├── reporting/                   # Berichterstellung
│   │   ├── __init__.py
│   │   └── report_generator.py      # HTML-Berichte
│   └── gui/                         # Grafische Oberfläche
│       ├── __init__.py
│       └── main_window.py           # Haupt-GUI
├── arduino/                         # Arduino-Firmware
│   ├── pneumatic_test_stand/
│   │   └── pneumatic_test_stand.ino # Arduino-Sketch
│   └── README.md                    # Hardware-Dokumentation
├── data/                            # Datenverzeichnis
│   ├── teststand.db                 # SQLite-Datenbank (auto-erstellt)
│   ├── exports/                     # Generierte Berichte
│   └── backups/                     # Datenbank-Backups
├── tests/                           # Unit-Tests
└── docs/                            # Dokumentation
```

## 🔬 Technologie-Stack

- **Python 3.8+**: Programmiersprache
- **PyQt5**: Moderne GUI-Framework
- **PySerial**: Serielle Kommunikation mit Arduino
- **Arduino**: Hardware-Steuerung (optional)
- **SQLite**: Eingebettete Datenbank
- **NumPy/SciPy**: Numerische Berechnungen
- **Pandas**: Datenanalyse
- **Matplotlib**: Visualisierungen
- **scikit-learn**: Machine Learning für Vorhersagen

## 📈 Beispiel-Workflow

```python
# Beispiel: Programmatischer Zugriff (für Automatisierung)

from src.database.db_manager import DatabaseManager
from src.controllers.test_controller import TestController
from src.models.component import Component, ComponentType, ComponentStatus

# Datenbank initialisieren
db = DatabaseManager()

# Komponente erstellen
component = Component(
    id=None,
    designation_1="Pneumatikzylinder Typ A",
    designation_2="Doppeltwirkend",
    material_number="PN-12345",
    manufacturer_number="FESTO-ABC-123",
    component_type=ComponentType.PNEUMATIC_CYLINDER,
    status=ComponentStatus.ACTIVE
)

component_id = db.create_component(component)

# Test-Controller
controller = TestController(db)

# Test starten (in separatem Thread)
test_run_id = controller.start_test(
    component_id=component_id,
    config_id=1,
    progress_callback=lambda prog, done, total: print(f"{prog:.1f}%"),
    measurement_callback=lambda m: print(f"Cycle {m.cycle_number}: {m.switching_time_ms}ms")
)
```

## 🛠️ Erweiterte Konfiguration

### Test-Konfiguration anpassen

Erstellen Sie benutzerdefinierte Test-Konfigurationen:

```python
from src.models.component import TestConfiguration

config = TestConfiguration(
    id=None,
    name="Langzeit-Belastungstest",
    component_id=1,
    target_cycles=1_000_000,      # 1 Million Zyklen
    cycle_interval_ms=50,          # 50ms zwischen Zyklen
    max_duration_minutes=14400,    # Max. 10 Tage
    monitor_temperature=True,
    monitor_pressure=True,
    alert_threshold_temperature=85.0,  # Alarm bei >85°C
    alert_threshold_pressure=11.0      # Alarm bei >11 bar
)

config_id = db.create_test_configuration(config)
```

## 📝 Datenbank-Schema

### Tabellen

1. **components**: Komponenten-Stammdaten
2. **test_configurations**: Test-Konfigurationen
3. **test_runs**: Durchgeführte Tests
4. **test_measurements**: Einzelne Messungen während Tests

### Backup

Die Datenbank wird automatisch in `data/teststand.db` gespeichert. Regelmäßige Backups empfohlen:

```bash
cp data/teststand.db data/backups/teststand_$(date +%Y%m%d).db
```

## 🎨 GUI-Features

### Moderne Oberfläche
- **Dunkles Theme** mit professionellen Farben
- **Responsives Design** für verschiedene Bildschirmgrößen
- **Echtzeit-Updates** ohne Neuladen
- **Intuitive Navigation** mit Tab-System
- **Visuelle Feedback**: Fortschrittsbalken, Farbcodes, Icons

### Keyboard-Shortcuts
- `Ctrl+N`: Neue Komponente
- `Ctrl+R`: Aktualisieren
- `Ctrl+Q`: Beenden

## 🔒 Sicherheit & Best Practices

- ✅ SQL-Injection-Schutz durch Prepared Statements
- ✅ Transaktions-Management für Daten-Integrität
- ✅ Error-Handling und Logging
- ✅ Thread-sichere Test-Ausführung
- ✅ Validierung von Benutzereingaben

## 🐛 Troubleshooting

### Problem: PyQt5 Installation schlägt fehl
**Lösung**: Installieren Sie System-Abhängigkeiten:
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt5

# macOS (Homebrew)
brew install pyqt5
```

### Problem: "No module named 'PyQt5'"
**Lösung**: Virtuelle Umgebung aktivieren und erneut installieren:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Problem: Datenbank ist gesperrt
**Lösung**: Schließen Sie alle anderen Instanzen der Anwendung.

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz.

## 👥 Support & Beitrag

Bei Fragen, Problemen oder Feature-Requests:
- Öffnen Sie ein Issue auf GitHub
- Kontaktieren Sie das Entwicklungsteam

## 🔄 Version History

### v1.0.0 (2025-11-23)
- ✅ Initiale Veröffentlichung
- ✅ Vollständige Test-Automatisierung
- ✅ Moderne GUI mit PyQt5
- ✅ Trend-Analyse und Vorhersagen
- ✅ HTML-Bericht-Generierung
- ✅ Umfangreiche Datenbank-Integration
- ✅ Echtzeit-Restlaufzeit-Berechnung

## 🚀 Roadmap

Geplante Features für zukünftige Versionen:
- [ ] PDF-Export für Berichte
- [ ] E-Mail-Benachrichtigungen bei Fehlern
- [ ] REST-API für externe Integration
- [ ] Cloud-Synchronisation
- [ ] Mobile App (Android/iOS)
- [ ] Erweiterte Statistiken und Dashboards
- [ ] Multi-User-Support mit Authentifizierung

---

**Entwickelt mit ❤️ für professionelle Pneumatik-Prüfstände**
