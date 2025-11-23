# Phase 2: Erweiterte Industrial Features

## Übersicht

Phase 2 erweitert die Pneumatik-Prüfstand Software um professionelle Industrial-Features für den Einsatz in regulierten Umgebungen.

## Neue Features

### 1. 📧 E-Mail-Benachrichtigungen (`src/utils/email_notifier.py`)

**Funktionen:**
- SMTP/TLS E-Mail-Versand
- HTML und Text-Formate
- Dateianhänge

**Vordefinierte Benachrichtigungen:**
- Test abgeschlossen
- Kalibrierung fällig
- Test fehlgeschlagen (Alarm)
- Berichte verfügbar

**Beispiel:**
```python
from src.utils.email_notifier import EmailNotifier, EmailConfig

config = EmailConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="user@example.com",
    password="password"
)

notifier = EmailNotifier(config)

notifier.send_test_completed_notification(
    to_addresses=["engineer@company.com"],
    component_name="Zylinder A",
    test_id=123,
    cycles=10000,
    status="Bestanden",
    duration_minutes=120.5
)
```

### 2. 📱 Barcode/QR-Code Scanner (`src/utils/barcode_scanner.py`)

**Unterstützte Formate:**
- EAN-13, EAN-8, UPC-A
- Code 128
- QR-Codes
- Custom Batch-Codes (LOT-YYYY-NNN)
- Custom Komponenten-Codes (COMP-MAT-SERIAL)

**Funktionen:**
- Automatische Format-Erkennung
- Datenextraktion
- QR-Code Generierung
- Validierung

**Beispiel:**
```python
from src.utils.barcode_scanner import BarcodeScanner

scanner = BarcodeScanner()
result = scanner.process_scan("LOT-2024-001")
# {'barcode': 'LOT-2024-001', 'code_type': 'BATCH',
#  'data': {'type': 'batch', 'year': '2024', 'number': '001'}}

# QR-Code generieren
qr_data = BarcodeScanner.generate_batch_qr("LOT-2024-001", "Zylinder", 100)
path = BarcodeScanner.create_qr_image(qr_data, "batch_001.png")
```

### 3. ✍️ Elektronische Signatur (`src/models/electronic_signature.py`)

**FDA 21 CFR Part 11 Konform:**
- SHA-256 Content Hashing
- SHA-256 Signature Hashing
- Re-Authentifizierung erforderlich
- Unveränderliches Audit-Trail

**Signatur-Arten:**
- Approved (Freigegeben)
- Reviewed (Geprüft)
- Verified (Verifiziert)
- Witnessed (Bezeugt)
- Rejected (Abgelehnt)

**Beispiel:**
```python
from src.models.electronic_signature import ElectronicSignatureManager

esig_manager = ElectronicSignatureManager(db_manager)

# Test-Ergebnis signieren
signature = esig_manager.sign_entity(
    user=current_user,
    password="password",  # Re-Authentifizierung
    entity_type="TestRun",
    entity_id=123,
    entity_content=test_data,
    action="Test Completion",
    reason="Test erfolgreich abgeschlossen, alle Parameter i.O.",
    meaning="Approved"
)

# Signatur verifizieren
is_valid = esig_manager.verify_signature(signature.id)
```

### 4. 📊 OEE-Berechnung (`src/analysis/oee_calculator.py`)

**Overall Equipment Effectiveness Metriken:**
- Verfügbarkeit (Availability)
- Leistung (Performance)
- Qualität (Quality)
- OEE Gesamt = Verfügbarkeit × Leistung × Qualität

**Six Big Losses:**
1. Ausfälle und Störungen
2. Rüst- und Einrichtzeiten
3. Kleinere Stillstände
4. Reduzierte Geschwindigkeit
5. Anlauf-Ausschuss
6. Produktions-Ausschuss

**World-Class Benchmark:** 85% OEE

**Beispiel:**
```python
from src.analysis.oee_calculator import OEECalculator

oee = OEECalculator.calculate_oee(
    planned_production_time_minutes=480,  # 8h
    downtime_minutes=30,
    ideal_cycle_time_seconds=10,
    total_pieces=2500,
    good_pieces=2400
)

print(f"OEE: {oee.oee * 100:.1f}%")
print(f"Rating: {oee.rating}")
print(f"World Class: {oee.is_world_class}")

# Textbericht generieren
report = OEECalculator.generate_report(oee)
```

### 5. 🔍 FMEA-System (`src/analysis/fmea_system.py`)

**Fehler-Möglichkeits- und Einfluss-Analyse:**
- Severity (Bedeutung): 1-10
- Occurrence (Auftreten): 1-10
- Detection (Entdeckung): 1-10
- **RPN = S × O × D** (Risk Priority Number)

**RPN-Prioritäten:**
- 1-39: Niedrig
- 40-99: Mittel
- 100-199: Hoch
- 200+: Sehr Hoch (Sofortmaßnahme!)

**Templates:**
- Zylinder (3 Templates)
- Ventile (2 Templates)
- Messtechnik (2 Templates)

**Beispiel:**
```python
from src.analysis.fmea_system import FMEAFailureMode, FMEAAnalyzer

failure = FMEAFailureMode(
    id=None,
    component_type="Pneumatikzylinder",
    process_step="Funktionstest",
    failure_mode="Zylinder fährt nicht aus",
    failure_effects="Test kann nicht durchgeführt werden",
    failure_causes="Luftdruck zu niedrig, Ventil defekt",
    severity=7,
    occurrence=3,
    detection=2,
    current_controls="Drucküberwachung",
    recommended_actions="Automatische Druckprüfung vor Test",
    responsibility="Instandhaltung"
)

print(f"RPN: {failure.rpn}")  # 7 × 3 × 2 = 42
print(f"Priority: {failure.priority.value}")  # Mittel
print(f"Immediate Action: {failure.requires_immediate_action}")  # False

# Analyse mehrerer Fehler
analysis = FMEAAnalyzer.analyze_failure_modes([failure1, failure2, failure3])
top_risks = FMEAAnalyzer.get_top_risks([failure1, failure2, failure3], limit=5)
```

### 6. 🌐 REST API (`src/api/rest_api.py`)

**FastAPI-basierte REST-Schnittstelle:**
- HTTP Basic Authentication
- Swagger UI Dokumentation
- CORS-Support für Web-Dashboard
- Pydantic Request/Response Models

**Endpunkte:**
- `/api/health` - Health Check
- `/api/system/status` - Systemstatus
- `/api/auth/login` - Login
- `/api/components` - Komponenten CRUD
- `/api/tests` - Test-Läufe
- `/api/calibration/due` - Fällige Kalibrierungen
- `/api/audit` - Audit-Log
- `/api/statistics/overview` - Statistiken

**Server starten:**
```bash
python -m src.api.rest_api
# Oder
uvicorn src.api.rest_api:app --reload
```

**API Docs:** `http://localhost:8000/docs`

### 7. 💻 Web Dashboard (`src/web/dashboard.html`)

**Single-Page-Application mit:**
- Echtzeit-Systemstatus
- Live-Charts (Chart.js)
- Komponenten-Übersicht
- Aktive Test-Läufe
- Fällige Kalibrierungen
- Auto-Refresh (10s)
- Responsive Design

**Features:**
- Login-Screen
- Farbcodierte Status-Anzeigen
- Animations (Pulse für laufende Tests)
- Moderne UI mit Gradient-Background

**Öffnen:** Browser → `src/web/dashboard.html`

### 8. 🖥️ GUI-Erweiterungen

#### Login Dialog (`src/gui/login_dialog.py`)
- Benutzer-Authentifizierung
- Remember Me Checkbox
- Modernes Design
- Audit-Log Integration

#### SPC Analysis Tab (`src/gui/spc_analysis_tab.py`)
- Regelkarten (X-Chart)
- Cp/Cpk Berechnung
- Kontrollgrenzen (±2σ, ±3σ)
- Interpretation

#### User Management (`src/gui/user_management_dialog.py`)
- Benutzerverwaltung
- Rollen-Zuweisung
- Passwort-Reset
- Aktivieren/Deaktivieren

#### OEE Dashboard (`src/gui/oee_dashboard_tab.py`)
- OEE-Berechnung
- Six Big Losses Diagramm
- Progress Bars
- Farbcodierte Bewertung

#### Calibration Dialog (`src/gui/calibration_dialog.py`)
- Prüfmittel-Verwaltung
- Kalibrierprotokolle
- Fälligkeits-Überwachung
- Farbcodierte Warnungen

## Technologie-Stack (Ergänzungen)

**Neue Dependencies:**
- `fastapi` - REST API Framework
- `uvicorn` - ASGI Server
- `pydantic` - Datenvalidierung
- `qrcode[pil]` - QR-Code Generierung

**Siehe:** `requirements.txt`

## Compliance & Standards

✅ **FDA 21 CFR Part 11** - Elektronische Signaturen
✅ **ISO 9001** - Qualitätsmanagement
✅ **Audit Trail** - Lückenlose Nachverfolgbarkeit
✅ **Datenintegrität** - SHA-256 Hashing
✅ **Zugriffskontrolle** - RBAC mit 4 Rollen

## Installation

```bash
# Dependencies installieren
pip install -r requirements.txt

# Datenbank initialisieren
python main.py
# Standard-Login: admin / admin

# Optional: REST API starten
python -m src.api.rest_api
```

## Erste Schritte

### 1. Login
```python
from src.gui.login_dialog import LoginDialog
from src.database.industrial_db_extension import IndustrialDatabaseManager

db = IndustrialDatabaseManager("data/pneumatic_teststand.db")
login_dialog = LoginDialog(db)

if login_dialog.exec_() == QDialog.Accepted:
    user = login_dialog.get_user()
    print(f"Eingeloggt als: {user.full_name} ({user.role.value})")
```

### 2. E-Mail senden
```python
from src.utils.email_notifier import EmailNotifier, EmailConfig

config = EmailConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your_email@gmail.com",
    password="your_password"
)

notifier = EmailNotifier(config)
success = notifier.send_test_completed_notification(
    to_addresses=["recipient@example.com"],
    component_name="Zylinder A",
    test_id=123,
    cycles=10000,
    status="Bestanden",
    duration_minutes=120.5
)
```

### 3. OEE berechnen
```python
from src.analysis.oee_calculator import OEECalculator

oee = OEECalculator.calculate_oee(
    planned_production_time_minutes=480,
    downtime_minutes=30,
    ideal_cycle_time_seconds=10,
    total_pieces=2500,
    good_pieces=2400
)

print(OEECalculator.generate_report(oee))
```

### 4. REST API nutzen
```bash
# System Status
curl -u admin:admin http://localhost:8000/api/system/status

# Komponenten abrufen
curl -u admin:admin http://localhost:8000/api/components
```

### 5. Web Dashboard öffnen
1. REST API starten: `python -m src.api.rest_api`
2. Browser öffnen: `src/web/dashboard.html`
3. Login: admin / admin

## Dateien-Übersicht

### Neue Dateien (Phase 2)

```
src/
├── api/
│   └── rest_api.py                 # REST API (FastAPI)
├── analysis/
│   ├── oee_calculator.py           # OEE-Berechnung
│   └── fmea_system.py              # FMEA-System
├── gui/
│   ├── login_dialog.py             # Login-Dialog
│   ├── spc_analysis_tab.py         # SPC-Analyse Tab
│   ├── user_management_dialog.py   # Benutzerverwaltung
│   ├── oee_dashboard_tab.py        # OEE-Dashboard
│   └── calibration_dialog.py       # Kalibrierungs-Dialog
├── models/
│   └── electronic_signature.py     # E-Signatur
├── utils/
│   ├── email_notifier.py           # E-Mail-System
│   └── barcode_scanner.py          # Barcode/QR-Scanner
└── web/
    └── dashboard.html              # Web-Dashboard

docs/
├── API_DOCUMENTATION.md            # API-Dokumentation
└── PHASE2_FEATURES.md              # Diese Datei
```

## Nächste Schritte

1. **GUI-Integration vollständig testen**
   - Login-Flow
   - SPC-Analyse mit echten Daten
   - OEE-Dashboard
   - Kalibrierungsverwaltung

2. **REST API erweitern**
   - Weitere Endpunkte
   - WebSocket für Live-Updates
   - API-Keys statt Basic Auth

3. **Web Dashboard erweitern**
   - Erweiterte Charts
   - Filterfunktionen
   - Export-Funktionen

4. **FMEA vollständig integrieren**
   - GUI für FMEA-Verwaltung
   - Automatische RPN-Berechnung
   - Maßnahmen-Tracking

## Support & Dokumentation

- **Hauptdokumentation:** `README.md`
- **Industrial Features:** `docs/INDUSTRIAL_FEATURES.md`
- **API-Dokumentation:** `docs/API_DOCUMENTATION.md`
- **Arduino-Integration:** `arduino/README.md`

## Version

**Phase 2 - Version 2.0.0**
- Datum: 2024-01-15
- Umfang: 8 neue Major Features
- Neue Dateien: 13
- Neue Dependencies: 4
