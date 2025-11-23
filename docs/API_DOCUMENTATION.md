# REST API Dokumentation

## Übersicht

Die Pneumatik-Prüfstand REST API bietet programmatischen Zugriff auf alle Funktionen des Testsystems.

**Base URL:** `http://localhost:8000`
**API Version:** 2.0.0

## Authentifizierung

Die API verwendet HTTP Basic Authentication.

```bash
curl -u username:password http://localhost:8000/api/health
```

## Endpoints

### System

#### GET /api/health
Gesundheitsstatus des Systems

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "database": "connected"
}
```

#### GET /api/system/status
Detaillierter Systemstatus

**Response:**
```json
{
  "status": "online",
  "uptime_minutes": 120.5,
  "active_tests": 2,
  "total_components": 45,
  "database_size_mb": 12.34,
  "arduino_connected": true
}
```

### Authentifizierung

#### POST /api/auth/login
Benutzer-Login

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "Administrator",
    "email": "admin@teststand.local",
    "role": "Administrator"
  },
  "token": "abc123...",
  "message": "Login successful"
}
```

### Komponenten

#### GET /api/components
Alle Komponenten abrufen

**Response:**
```json
[
  {
    "id": 1,
    "designation_1": "Zylinder A",
    "designation_2": "Hauptzylinder",
    "material_number": "MAT-001",
    "manufacturer_number": "MAN-001",
    "component_type": "Zylinder",
    "status": "Aktiv",
    "total_tests": 150,
    "total_switching_cycles": 50000,
    "total_hours": 125.5,
    "total_minutes": 7530
  }
]
```

#### GET /api/components/{component_id}
Einzelne Komponente abrufen

**Response:** Siehe GET /api/components

#### POST /api/components
Neue Komponente erstellen

**Request Body:**
```json
{
  "designation_1": "Zylinder B",
  "designation_2": "Nebenzylinder",
  "material_number": "MAT-002",
  "manufacturer_number": "MAN-002",
  "component_type": "Zylinder",
  "status": "Aktiv"
}
```

**Response:** 201 Created + Component Object

### Tests

#### GET /api/tests
Alle Test-Läufe abrufen

**Query Parameters:**
- `limit` (optional): Anzahl der Ergebnisse (default: 50)

**Response:**
```json
[
  {
    "id": 1,
    "component_id": 1,
    "configuration_id": 1,
    "start_time": "2024-01-15T10:00:00",
    "end_time": "2024-01-15T12:00:00",
    "status": "Abgeschlossen",
    "cycles_completed": 1000,
    "total_cycles": 1000,
    "operator": "Max Mustermann"
  }
]
```

#### GET /api/tests/{test_id}/measurements
Messungen eines Test-Laufs

**Response:**
```json
[
  {
    "id": 1,
    "cycle_number": 1,
    "switching_time": 0.45,
    "pressure": 6.2,
    "temperature": 22.5,
    "timestamp": "2024-01-15T10:00:01"
  }
]
```

### Berichte

#### GET /api/reports/component/{component_id}
Komponenten-Bericht

**Response:**
```json
{
  "component": {...},
  "test_runs": [...],
  "total_tests": 150,
  "timestamp": "2024-01-15T10:30:00"
}
```

### Kalibrierung

#### GET /api/calibration/due
Fällige Kalibrierungen

**Query Parameters:**
- `days` (optional): Zeitraum in Tagen (default: 30)

**Response:**
```json
{
  "count": 3,
  "days": 30,
  "equipment": [
    {
      "id": 1,
      "equipment_id": "PM-001",
      "name": "Drucksensor 1",
      "next_calibration_date": "2024-02-01T00:00:00"
    }
  ]
}
```

### Audit-Log

#### GET /api/audit
Audit-Log abrufen

**Query Parameters:**
- `limit` (optional): Anzahl der Einträge (default: 100)

**Response:**
```json
{
  "count": 100,
  "entries": [
    {
      "id": 1,
      "timestamp": "2024-01-15T10:30:00",
      "user_id": 1,
      "username": "admin",
      "action": "CREATE",
      "entity_type": "Component",
      "entity_id": 1,
      "details": "Material: MAT-001",
      "success": true
    }
  ]
}
```

### Statistiken

#### GET /api/statistics/overview
Statistik-Übersicht

**Response:**
```json
{
  "total_components": 45,
  "total_test_runs": 500,
  "completed_tests": 480,
  "total_cycles": 250000,
  "total_hours": 1250.5,
  "timestamp": "2024-01-15T10:30:00"
}
```

## Fehlerbehandlung

Die API verwendet Standard-HTTP-Statuscodes:

- `200 OK` - Erfolgreiche Anfrage
- `201 Created` - Ressource erstellt
- `400 Bad Request` - Ungültige Anfrage
- `401 Unauthorized` - Authentifizierung fehlgeschlagen
- `403 Forbidden` - Keine Berechtigung
- `404 Not Found` - Ressource nicht gefunden
- `500 Internal Server Error` - Serverfehler

**Fehler-Response:**
```json
{
  "detail": "Fehlermeldung"
}
```

## Beispiele

### Python

```python
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8000/api"
auth = HTTPBasicAuth("admin", "admin")

# System Status
response = requests.get(f"{BASE_URL}/system/status", auth=auth)
print(response.json())

# Komponenten abrufen
response = requests.get(f"{BASE_URL}/components", auth=auth)
components = response.json()

# Neue Komponente erstellen
new_component = {
    "designation_1": "Ventil A",
    "designation_2": "Hauptventil",
    "material_number": "MAT-V001",
    "manufacturer_number": "MAN-V001",
    "component_type": "Magnetventil",
    "status": "Aktiv"
}
response = requests.post(f"{BASE_URL}/components", json=new_component, auth=auth)
print(response.json())
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:8000/api";
const auth = btoa("admin:admin");

// System Status
fetch(`${BASE_URL}/system/status`, {
  headers: {
    "Authorization": `Basic ${auth}`
  }
})
.then(response => response.json())
.then(data => console.log(data));

// Komponenten abrufen
fetch(`${BASE_URL}/components`, {
  headers: {
    "Authorization": `Basic ${auth}`
  }
})
.then(response => response.json())
.then(components => console.log(components));
```

### cURL

```bash
# System Status
curl -u admin:admin http://localhost:8000/api/system/status

# Komponenten abrufen
curl -u admin:admin http://localhost:8000/api/components

# Neue Komponente erstellen
curl -u admin:admin -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "designation_1": "Ventil A",
    "designation_2": "Hauptventil",
    "material_number": "MAT-V001",
    "manufacturer_number": "MAN-V001",
    "component_type": "Magnetventil",
    "status": "Aktiv"
  }' \
  http://localhost:8000/api/components
```

## API Server starten

```bash
# Installation
pip install -r requirements.txt

# Server starten
cd src
python -m api.rest_api

# Oder mit uvicorn
uvicorn api.rest_api:app --host 0.0.0.0 --port 8000 --reload
```

Der Server läuft dann auf `http://localhost:8000`

API-Dokumentation (Swagger UI): `http://localhost:8000/docs`

## Web Dashboard

Das Web Dashboard ist eine Single-Page-Application, die die REST API nutzt.

**Öffnen:** `src/web/dashboard.html` im Browser

**Features:**
- Echtzeit-Systemstatus
- Komponenten-Übersicht
- Aktive Test-Läufe
- Fällige Kalibrierungen
- Statistiken und Charts
- Auto-Refresh alle 10 Sekunden

**Login:**
- Standard-Login: admin / admin
