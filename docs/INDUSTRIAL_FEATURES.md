# 🏭 Industriestandard-Features

Diese Dokumentation beschreibt die erweiterten Industrie-Features der Pneumatik-Prüfstand Software.

## 📋 Übersicht der Features

### ✅ Implementierte Features

1. **Benutzer-Verwaltung** - Multi-User mit Rollen und Rechten
2. **Prüfprogramm-System** - Strukturierte Testpläne mit Prüfschritten
3. **SPC-Statistiken** - Cp/Cpk Prozessfähigkeitsanalyse
4. **Audit-Trail** - Vollständige Nachverfolgbarkeit
5. **Chargen-Verwaltung** - Batch/Los-Tracking
6. **Kalibrierungs-Management** - Prüfmittelüberwachung
7. **Export-Funktionen** - CSV, Excel, PDF
8. **Grenzwert-System** - Warn- und Fehlergrenzen
9. **i.O./n.i.O. Bewertung** - Automatische Gut/Schlecht-Bewertung

---

## 👤 Benutzer-Verwaltung

### Rollen und Rechte

**4 Benutzerrollen:**

| Rolle | Beschreibung | Berechtigungen |
|-------|--------------|----------------|
| **Administrator** | Volle Rechte | Alle |
| **Ingenieur** | Entwicklung & Freigabe | Tests, Berichte, Kalibrierung, Prüfprogramme, Freigaben |
| **Bediener** | Täglicher Betrieb | Tests starten/stoppen, Berichte ansehen |
| **Betrachter** | Nur Ansicht | Komponenten und Tests ansehen |

### Berechtigungen im Detail

```python
Permission.CREATE_COMPONENT      # Komponente erstellen
Permission.EDIT_COMPONENT        # Komponente bearbeiten
Permission.DELETE_COMPONENT      # Komponente löschen
Permission.START_TEST            # Test starten
Permission.STOP_TEST             # Test stoppen
Permission.GENERATE_REPORT       # Bericht erstellen
Permission.EXPORT_DATA           # Daten exportieren
Permission.MANAGE_USERS          # Benutzer verwalten
Permission.MANAGE_CALIBRATION    # Kalibrierung verwalten
Permission.MANAGE_TEST_PROGRAMS  # Prüfprogramme verwalten
Permission.APPROVE_RESULTS       # Ergebnisse freigeben
Permission.EDIT_SETTINGS         # Einstellungen bearbeiten
Permission.VIEW_AUDIT_LOG        # Audit-Log anzeigen
```

### Standard-Benutzer

```
Benutzername: admin
Passwort: admin
Rolle: Administrator
```

**⚠️ WICHTIG:** Ändern Sie das Admin-Passwort nach der ersten Anmeldung!

### Verwendung

```python
from src.models.user import User, UserRole, Permission
from src.database.industrial_db_extension import IndustrialDatabaseManager

# Benutzer erstellen
db = IndustrialDatabaseManager()
user = User(
    id=None,
    username="operator1",
    password_hash="",  # Wird automatisch generiert
    full_name="Max Mustermann",
    email="max@firma.de",
    role=UserRole.OPERATOR
)
user_id = db.create_user(user, password="sicher123")

# Benutzer authentifizieren
user = db.get_user_by_username("operator1")
salt = db.get_password_salt("operator1")
if user and user.verify_password("sicher123", salt):
    print("Login erfolgreich!")

# Berechtigung prüfen
if user.has_permission(Permission.START_TEST):
    print("Darf Test starten")
```

---

## 📊 Prüfprogramm-System

### Konzept

Prüfprogramme definieren **strukturierte Testabläufe** mit mehreren Prüfschritten, Grenzwerten und Bewertungskriterien.

### Komponenten

#### 1. TestProgram (Prüfprogramm)

```python
from src.models.test_program import TestProgram, TestStep, TestLimit, TestStepType

# Prüfprogramm erstellen
program = TestProgram(
    id=None,
    name="Dauerlauf Pneumatikzylinder",
    version="1.0",
    description="Standard-Dauerlaufprüfung",
    component_type="Pneumatikzylinder",
    created_by=user_id
)
```

#### 2. TestStep (Prüfschritt)

```python
# Prüfschritt definieren
step1 = TestStep(
    id=None,
    step_number=1,
    name="Schaltzeit-Messung",
    description="Messung der Schaltzeit unter Last",
    step_type=TestStepType.MEASUREMENT,
    is_automated=True,
    is_mandatory=True
)

# Grenzwerte hinzufügen
limit = TestLimit(
    parameter_name="Schaltzeit",
    lower_limit=80.0,   # ms
    upper_limit=120.0,  # ms
    target_value=100.0, # Sollwert
    unit="ms",
    lower_warning=85.0, # Warngrenze
    upper_warning=115.0
)
step1.limits.append(limit)

# Zum Programm hinzufügen
program.add_step(step1)
```

#### 3. Prüfschritt-Typen

```python
class TestStepType(Enum):
    MEASUREMENT = "Messung"           # Automatische Messung
    VISUAL_INSPECTION = "Sichtprüfung"  # Manuelle Sichtprüfung
    FUNCTIONAL_TEST = "Funktionstest"   # Funktionstest
    ENDURANCE_TEST = "Dauertest"       # Langzeit-Test
    PRESSURE_TEST = "Drucktest"        # Druckprüfung
```

### Grenzwert-Prüfung

```python
# Wert gegen Grenzwerte prüfen
measured_value = 105.5  # ms
status, is_ok = limit.check_value(measured_value)

# status kann sein: "OK", "WARNING", "NOK"
# is_ok: True wenn innerhalb Toleranz (auch bei WARNING)
```

### i.O. / n.i.O. Bewertung

```python
if status == "OK":
    result = "i.O."  # In Ordnung
elif status == "WARNING":
    result = "i.O. mit Abweichung"
else:  # "NOK"
    result = "n.i.O."  # Nicht in Ordnung
```

---

## 📈 SPC-Statistiken (Statistical Process Control)

### Prozessfähigkeitsanalyse

Die Software berechnet die wichtigsten SPC-Kennzahlen nach Industriestandard:

#### Kennzahlen

| Kennzahl | Beschreibung | Bewertung |
|----------|--------------|-----------|
| **Cp** | Process Capability | Prozessfähigkeit (ohne Lage) |
| **Cpk** | Process Capability Index | Prozessfähigkeit (mit Lage) |
| **Pp** | Process Performance | Langfristige Leistung |
| **Ppk** | Process Performance Index | Langfristige Leistung (mit Lage) |

#### Cpk-Bewertung

| Cpk-Wert | Bewertung | Bedeutung |
|----------|-----------|-----------|
| ≥ 2.0 | Ausgezeichnet | 6-Sigma-Prozess |
| ≥ 1.67 | Sehr gut | Sehr fähiger Prozess |
| ≥ 1.33 | Gut | Fähiger Prozess |
| ≥ 1.0 | Ausreichend | Grenzwertig fähig |
| < 1.0 | Mangelhaft | **Prozess NICHT fähig!** |

### Verwendung

```python
from src.analysis.spc_statistics import SPCAnalyzer

# Messwerte (mindestens 30 erforderlich)
measurements = [100.2, 101.5, 99.8, 100.1, ...]  # Schaltzeiten in ms

# Spezifikationsgrenzen
lower_spec_limit = 90.0   # USG (Untere Spezifikationsgrenze)
upper_spec_limit = 110.0  # OSG (Obere Spezifikationsgrenze)
target_value = 100.0      # Sollwert

# SPC-Analyse durchführen
result = SPCAnalyzer.calculate_capability(
    data=measurements,
    lower_spec_limit=lower_spec_limit,
    upper_spec_limit=upper_spec_limit,
    target_value=target_value
)

# Ergebnisse
print(f"Cp:  {result.cp}")
print(f"Cpk: {result.cpk}")
print(f"Bewertung: {result.capability_rating}")
print(f"Ausschuss: {result.out_of_spec_percent}%")

# Textbericht generieren
report = SPCAnalyzer.generate_spc_report(result)
print(report)
```

### Regelkarten (Control Charts)

```python
# Regelgrenzen berechnen
limits = SPCAnalyzer.calculate_control_limits(measurements)

print(f"UCL (Upper Control Limit): {limits['ucl']}")
print(f"UWL (Upper Warning Limit): {limits['uwl']}")
print(f"CL  (Center Line):         {limits['cl']}")
print(f"LWL (Lower Warning Limit): {limits['lwl']}")
print(f"LCL (Lower Control Limit): {limits['lcl']}")
```

### Western Electric Rules

```python
# Regelverletzungen prüfen
violations = SPCAnalyzer.check_control_rules(measurements)

for violation in violations:
    print(f"⚠ {violation}")

# Beispiel-Ausgaben:
# "Regel 1: Punkt 45 außerhalb 3-Sigma"
# "Regel 2: 9 Punkte ab Position 12 auf einer Seite"
# "Regel 3: 6 steigende Punkte ab Position 34"
```

---

## 📝 Audit-Trail (Nachverfolgbarkeit)

### Konzept

Alle relevanten Aktionen werden **unveränderbar** protokolliert für:
- **Compliance** (ISO 9001, FDA 21 CFR Part 11)
- **Nachverfolgbarkeit** (Wer hat wann was gemacht?)
- **Fehleranalyse**

### Protokollierte Aktionen

- Benutzer-Login/Logout
- Komponenten erstellen/bearbeiten/löschen
- Tests starten/stoppen/abbrechen
- Berichte erstellen
- Daten exportieren
- Einstellungen ändern
- Kalibrierungen durchführen
- Freigaben erteilen/verweigern

### Verwendung

```python
from src.utils.audit_logger import AuditLogger

audit = AuditLogger(db_manager)

# Test-Start protokollieren
audit.log_test_started(
    user_id=user.id,
    username=user.username,
    test_run_id=test_id,
    component_id=component_id
)

# Generische Protokollierung
audit.log(
    user_id=user.id,
    username=user.username,
    action="CUSTOM_ACTION",
    entity_type="CustomEntity",
    entity_id=123,
    details="Zusätzliche Informationen",
    ip_address="192.168.1.100",
    success=True
)
```

### Log-Datei

Zusätzlich zur Datenbank wird in `data/audit_trail.log` geschrieben:

```
2025-11-23 14:32:15 | INFO | admin (1) | START_TEST | TestRun #42 | SUCCESS | Test gestartet für Komponente #5
2025-11-23 14:45:30 | INFO | operator1 (2) | GENERATE_REPORT | Report | SUCCESS | Typ: ComponentReport, Anzahl: 1
```

### Audit-Log abrufen

```python
# Letzte 100 Einträge
entries = db.get_audit_log(limit=100)

# Für bestimmten Benutzer
entries = db.get_audit_log(limit=50, user_id=user.id)

# Export
from src.utils.export_manager import ExportManager
exporter = ExportManager()
csv_path = exporter.export_audit_log_csv(entries)
```

---

## 📦 Chargen-Verwaltung (Batch Management)

### Konzept

Verwaltet **Lose/Chargen** von Komponenten für:
- Rückverfolgbarkeit
- Qualitätsstatistiken pro Charge
- Lieferanten-Bewertung

### Batch-Status

| Status | Beschreibung |
|--------|--------------|
| Offen | Charge angelegt, noch keine Tests |
| In Prüfung | Tests laufen |
| Abgeschlossen | Alle Tests durchgeführt |

### Qualitätsstatus

| Status | Beschreibung |
|--------|--------------|
| Ungeklärt | Noch keine Bewertung |
| Freigegeben | Alle Tests bestanden, Charge OK |
| Gesperrt | Tests nicht bestanden, Charge gesperrt |
| Nacharbeit | Teilweise fehlerhaft, Nacharbeit nötig |

### Verwendung

```python
from src.models.test_program import Batch

# Batch erstellen
batch = Batch(
    id=None,
    batch_number="LOT-2025-001",
    component_type="Pneumatikzylinder",
    quantity=100,
    supplier="FESTO GmbH",
    supplier_batch="FESTO-XYZ-123"
)

batch_id = db.create_batch(batch)

# Fortschritt aktualisieren
db.update_batch_progress(
    batch_number="LOT-2025-001",
    tested=50,    # 50 getestet
    passed=48,    # 48 bestanden
    failed=2      # 2 durchgefallen
)

# Batch abrufen
batch_data = db.get_batch("LOT-2025-001")
print(f"Fortschritt: {batch_data['tested_quantity']}/{batch_data['quantity']}")
print(f"Ausbeute: {batch_data['passed_quantity']/batch_data['tested_quantity']*100:.1f}%")
```

---

## 🔧 Kalibrierungs-Management

### Konzept

Überwacht **Kalibrierung von Prüfmitteln** (Sensoren, Messgeräte):
- Kalibrierintervalle
- Ablauferinnerungen
- Kalibrierprotokolle
- Zertifikatsverwaltung

### Prüfmittel erfassen

```python
from src.models.calibration import CalibrationEquipment, CalibrationStatus
from datetime import datetime, timedelta

equipment = CalibrationEquipment(
    id=None,
    equipment_id="PM-001",
    name="Drucksensor Prüfstand 1",
    equipment_type="Drucksensor",
    manufacturer="IFM Electronic",
    model="PN7002",
    serial_number="SN-123456",
    calibration_interval_days=365,  # Jährlich
    last_calibration_date=datetime(2024, 11, 23),
    next_calibration_date=datetime(2025, 11, 23),
    status=CalibrationStatus.VALID,
    accuracy_class="0.5%",
    measurement_range_min=0.0,
    measurement_range_max=10.0,
    unit="bar",
    location="Prüffeld 1",
    responsible_person="Hr. Schmidt"
)

equipment_id = db.create_calibration_equipment(equipment)
```

### Kalibrierung durchführen

```python
from src.models.calibration import CalibrationRecord, CalibrationType

record = CalibrationRecord(
    id=None,
    equipment_id=equipment_id,
    calibration_date=datetime.now(),
    calibration_type=CalibrationType.EXTERNAL,
    calibrated_by="DAkkS Labor XYZ",
    laboratory="DAkkS-zertifiziertes Kalibrierlabor",
    result="Bestanden",
    deviation=0.02,  # bar
    uncertainty=0.01,  # Messunsicherheit
    certificate_number="DAkkS-K-12345-2025",
    certificate_file="/path/to/certificate.pdf",
    next_calibration_date=datetime.now() + timedelta(days=365),
    remarks="Kalibrierung ohne Beanstandungen",
    cost=250.00
)

db.create_calibration_record(record)
```

### Fällige Kalibrierungen

```python
# Alle Prüfmittel mit Kalibrierung in den nächsten 30 Tagen
due_soon = db.get_calibration_due_soon(days=30)

for equipment in due_soon:
    days_left = (equipment['next_calibration_date'] - datetime.now()).days
    print(f"⚠ {equipment['name']}: Kalibrierung in {days_left} Tagen fällig!")
```

---

## 📤 Export-Funktionen

### Unterstützte Formate

- **CSV** - Einfacher Datenexport (UTF-8, Semikolon-getrennt)
- **Excel** - Multi-Sheet Workbooks
- **PDF** - Berichte (via HTML-Konvertierung)

### CSV-Export

```python
from src.utils.export_manager import ExportManager

exporter = ExportManager()

# Einfacher CSV-Export
data = [
    {'Name': 'Komponente 1', 'Wert': 100},
    {'Name': 'Komponente 2', 'Wert': 200}
]

csv_path = exporter.export_to_csv(
    data=data,
    filename="meine_daten"
)
# Erzeugt: data/exports/meine_daten_20251123_143000.csv
```

### Excel-Export

```python
# Multi-Sheet Excel
data = {
    'Komponenten': [
        {'ID': 1, 'Name': 'Zylinder A'},
        {'ID': 2, 'Name': 'Ventil B'}
    ],
    'Tests': [
        {'Test-ID': 1, 'Zyklen': 10000},
        {'Test-ID': 2, 'Zyklen': 5000}
    ]
}

excel_path = exporter.export_to_excel(
    data=data,
    filename="vollstaendiger_bericht"
)
# Erzeugt: data/exports/vollstaendiger_bericht_20251123_143000.xlsx
# Mit 2 Sheets: "Komponenten" und "Tests"
```

### Spezialisierte Exporte

```python
# Testergebnisse als Excel
excel_path = exporter.export_test_results_excel(
    component_name="Zylinder_A",
    component_info={'designation_1': 'Zylinder A', ...},
    test_runs=[...],
    measurements=[...],
    statistics={...}
)

# SPC-Daten exportieren
spc_excel = exporter.export_spc_data(
    component_name="Zylinder_A",
    measurements=[100.1, 100.5, ...],
    spc_result={'cp': 1.5, 'cpk': 1.3, ...}
)

# Audit-Log exportieren
audit_csv = exporter.export_audit_log_csv(audit_entries)

# Kalibrierprotokolle
cal_csv = exporter.export_calibration_records(calibration_data)
```

---

## 🔐 Best Practices

### Sicherheit

1. **Passwörter**
   - Mindestens 8 Zeichen
   - Hash-Speicherung (PBKDF2-SHA256)
   - Niemals im Klartext

2. **Audit-Trail**
   - Alle sicherheitsrelevanten Aktionen protokollieren
   - Logs regelmäßig sichern
   - Niemals Logs manuell ändern

3. **Rechte**
   - Principle of Least Privilege
   - Regelmäßige Rechtevergabe-Audits
   - Inactive Accounts deaktivieren

### Qualitätssicherung

1. **Prüfprogramme**
   - Versionskontrolle nutzen
   - Änderungen freigeben lassen
   - Alte Versionen archivieren

2. **Kalibrierung**
   - Rechtzeitig planen (30 Tage Vorlauf)
   - Zertifikate archivieren
   - Bei Überschreitung: Equipment sperren

3. **SPC**
   - Mindestens 30 Messwerte für aussagekräftige Cpk
   - Prozess bei Cpk < 1.33 optimieren
   - Bei Cpk < 1.0: Sofortmaßnahmen

### Daten-Management

1. **Backups**
   - Tägliche Datenbank-Backups
   - Offsite-Speicherung
   - Regelmäßige Restore-Tests

2. **Archivierung**
   - Alte Daten archivieren (z.B. > 5 Jahre)
   - Gesetzliche Aufbewahrungsfristen beachten
   - Audit-Logs langfristig aufbewahren

---

## 🚀 Roadmap (Geplant)

- [ ] Elektronische Signatur (FDA 21 CFR Part 11)
- [ ] OEE-Berechnung (Overall Equipment Effectiveness)
- [ ] Barcode/QR-Scanner Integration
- [ ] E-Mail-Benachrichtigungen
- [ ] Web-Dashboard
- [ ] REST-API
- [ ] Abweichungsmanagement (NCR)
- [ ] FMEA-Integration

---

**Version:** 1.0
**Stand:** November 2025
**Kontakt:** support@teststand.local
