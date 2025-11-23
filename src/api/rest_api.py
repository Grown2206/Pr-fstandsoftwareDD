"""
REST API für Pneumatik-Prüfstand
FastAPI-basierte REST-Schnittstelle
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import secrets

from ..database.industrial_db_extension import IndustrialDatabaseManager
from ..models.user import User, UserRole
from ..models.component import Component, ComponentType, ComponentStatus
from ..models.test_program import TestProgram


# ===== PYDANTIC MODELS =====

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    user: Optional[Dict[str, Any]] = None
    token: Optional[str] = None
    message: Optional[str] = None


class ComponentCreate(BaseModel):
    designation_1: str
    designation_2: str
    material_number: str
    manufacturer_number: str
    component_type: str
    status: str = "Aktiv"


class ComponentResponse(BaseModel):
    id: int
    designation_1: str
    designation_2: str
    material_number: str
    manufacturer_number: str
    component_type: str
    status: str
    total_tests: int
    total_switching_cycles: int
    total_hours: float
    total_minutes: float


class TestRunCreate(BaseModel):
    component_id: int
    configuration_id: int
    operator: str
    test_type: str


class TestRunResponse(BaseModel):
    id: int
    component_id: int
    configuration_id: int
    start_time: str
    end_time: Optional[str]
    status: str
    cycles_completed: int
    total_cycles: int
    operator: str


class SystemStatusResponse(BaseModel):
    status: str
    uptime_minutes: float
    active_tests: int
    total_components: int
    database_size_mb: float
    arduino_connected: bool


# ===== FASTAPI APP =====

app = FastAPI(
    title="Pneumatik-Prüfstand API",
    description="REST API für industriellen Pneumatik-Prüfstand",
    version="2.0.0"
)

# CORS für Web-Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion spezifische Origins angeben!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBasic()

# Globale DB-Instanz (wird beim Start initialisiert)
db_manager: Optional[IndustrialDatabaseManager] = None
app_start_time = datetime.now()


def get_db() -> IndustrialDatabaseManager:
    """Dependency: Holt DB-Manager"""
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_manager


def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)) -> User:
    """Dependency: Authentifiziert Benutzer"""
    db = get_db()
    user = db.get_user_by_username(credentials.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    salt = db.get_password_salt(credentials.username)
    if not user.verify_password(credentials.password, salt):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


# ===== ENDPOINTS =====

@app.get("/")
async def root():
    """API Root"""
    return {
        "name": "Pneumatik-Prüfstand API",
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Gesundheitsstatus"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db_manager else "not initialized"
    }


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: IndustrialDatabaseManager = Depends(get_db)):
    """Benutzer-Login"""
    user = db.get_user_by_username(request.username)

    if not user:
        return LoginResponse(success=False, message="Invalid credentials")

    salt = db.get_password_salt(request.username)
    if not user.verify_password(request.password, salt):
        return LoginResponse(success=False, message="Invalid credentials")

    if not user.is_active:
        return LoginResponse(success=False, message="Account disabled")

    # Token generieren (vereinfacht - in Produktion JWT verwenden!)
    token = secrets.token_urlsafe(32)

    return LoginResponse(
        success=True,
        user={
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role.value
        },
        token=token,
        message="Login successful"
    )


@app.get("/api/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    user: User = Depends(authenticate_user),
    db: IndustrialDatabaseManager = Depends(get_db)
):
    """System-Status"""
    import os

    # Uptime berechnen
    uptime = (datetime.now() - app_start_time).total_seconds() / 60

    # Datenbankgröße
    db_path = "data/pneumatic_teststand.db"
    db_size_mb = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0

    # Komponenten zählen
    components = db.get_all_components()

    # Aktive Tests zählen
    active_tests = len([r for r in db.get_all_test_runs() if r.get('status') == 'Läuft'])

    return SystemStatusResponse(
        status="online",
        uptime_minutes=uptime,
        active_tests=active_tests,
        total_components=len(components),
        database_size_mb=round(db_size_mb, 2),
        arduino_connected=False  # TODO: Arduino-Status abfragen
    )


# ===== KOMPONENTEN =====

@app.get("/api/components", response_model=List[ComponentResponse])
async def get_components(
    user: User = Depends(authenticate_user),
    db: IndustrialDatabaseManager = Depends(get_db)
):
    """Alle Komponenten abrufen"""
    components = db.get_all_components()
    return [
        ComponentResponse(
            id=c['id'],
            designation_1=c['designation_1'],
            designation_2=c['designation_2'],
            material_number=c['material_number'],
            manufacturer_number=c['manufacturer_number'],
            component_type=c['component_type'],
            status=c['status'],
            total_tests=c.get('total_tests', 0),
            total_switching_cycles=c.get('total_switching_cycles', 0),
            total_hours=c.get('total_hours', 0.0),
            total_minutes=c.get('total_minutes', 0.0)
        )
        for c in components
    ]


@app.get("/api/components/{component_id}", response_model=ComponentResponse)
async def get_component(
    component_id: int,
    user: User = Depends(authenticate_user),
    db: IndustrialDatabaseManager = Depends(get_db)
):
    """Einzelne Komponente abrufen"""
    component = db.get_component(component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    return ComponentResponse(
        id=component['id'],
        designation_1=component['designation_1'],
        designation_2=component['designation_2'],
        material_number=component['material_number'],
        manufacturer_number=component['manufacturer_number'],
        component_type=component['component_type'],
        status=component['status'],
        total_tests=component.get('total_tests', 0),
        total_switching_cycles=component.get('total_switching_cycles', 0),
        total_hours=component.get('total_hours', 0.0),
        total_minutes=component.get('total_minutes', 0.0)
    )


@app.post("/api/components", response_model=ComponentResponse, status_code=status.HTTP_201_CREATED)
async def create_component(
    component: ComponentCreate,
    user: User = Depends(authenticate_user),
    db: IndustrialDatabaseManager = Depends(get_db)
):
    """Neue Komponente erstellen"""
    from ..models.user import Permission

    if not user.has_permission(Permission.CREATE_COMPONENT):
        raise HTTPException(status_code=403, detail="No permission to create components")

    # Komponente erstellen
    comp = Component(
        id=None,
        designation_1=component.designation_1,
        designation_2=component.designation_2,
        material_number=component.material_number,
        manufacturer_number=component.manufacturer_number,
        component_type=ComponentType(component.component_type),
        status=ComponentStatus(component.status),
        total_tests=0,
        total_switching_cycles=0,
        total_hours=0.0,
        total_minutes=0.0
    )

    component_id = db.create_component(comp)
    created = db.get_component(component_id)

    # Audit-Log
    from ..utils.audit_logger import AuditLogger
    audit = AuditLogger(db)
    audit.log_create(user.id, user.username, "Component", component_id,
                     f"Material: {component.material_number}")

    return ComponentResponse(
        id=created['id'],
        designation_1=created['designation_1'],
        designation_2=created['designation_2'],
        material_number=created['material_number'],
        manufacturer_number=created['manufacturer_number'],
        component_type=created['component_type'],
        status=created['status'],
        total_tests=0,
        total_switching_cycles=0,
        total_hours=0.0,
        total_minutes=0.0
    )


# ===== TEST-LÄUFE =====

@app.get("/api/tests", response_model=List[TestRunResponse])
async def get_test_runs(
    limit: int = 50,
    user: User = Depends(authenticate_user),
    db: IndustrialDatabaseManager = Depends(get_db)
):
    """Alle Test-Läufe abrufen"""
    test_runs = db.get_all_test_runs()[:limit]

    return [
        TestRunResponse(
            id=t['id'],
            component_id=t['component_id'],
            configuration_id=t['configuration_id'],
            start_time=t['start_time'],
            end_time=t.get('end_time'),
            status=t['status'],
            cycles_completed=t.get('cycles_completed', 0),
            total_cycles=t.get('total_cycles', 0),
            operator=t.get('operator', 'Unknown')
        )
        for t in test_runs
    ]


@app.get("/api/tests/{test_id}/measurements")
async def get_test_measurements(
    test_id: int,
    user: User = Depends(authenticate_user),
    db: IndustrialDatabaseManager = Depends(get_db)
):
    """Messungen eines Test-Laufs"""
    measurements = db.get_measurements_for_test(test_id)

    if not measurements:
        raise HTTPException(status_code=404, detail="Test run not found or no measurements")

    return measurements


# ===== BERICHTE =====

@app.get("/api/reports/component/{component_id}")
async def get_component_report(
    component_id: int,
    user: User = Depends(authenticate_user),
    db: IndustrialDatabaseManager = Depends(get_db)
):
    """Komponenten-Bericht"""
    component = db.get_component(component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    test_runs = db.get_test_runs_for_component(component_id)

    return {
        "component": component,
        "test_runs": test_runs,
        "total_tests": len(test_runs),
        "timestamp": datetime.now().isoformat()
    }


# ===== KALIBRIERUNG =====

@app.get("/api/calibration/due")
async def get_calibration_due(
    days: int = 30,
    user: User = Depends(authenticate_user),
    db: IndustrialDatabaseManager = Depends(get_db)
):
    """Fällige Kalibrierungen"""
    from datetime import timedelta
    equipment = db.get_calibration_due_soon(days)

    return {
        "count": len(equipment),
        "days": days,
        "equipment": equipment
    }


# ===== AUDIT-LOG =====

@app.get("/api/audit")
async def get_audit_log(
    limit: int = 100,
    user: User = Depends(authenticate_user),
    db: IndustrialDatabaseManager = Depends(get_db)
):
    """Audit-Log abrufen"""
    from ..models.user import Permission

    if not user.has_permission(Permission.VIEW_AUDIT_LOG):
        raise HTTPException(status_code=403, detail="No permission to view audit log")

    entries = db.get_audit_log(limit)
    return {
        "count": len(entries),
        "entries": entries
    }


# ===== STATISTIKEN =====

@app.get("/api/statistics/overview")
async def get_statistics_overview(
    user: User = Depends(authenticate_user),
    db: IndustrialDatabaseManager = Depends(get_db)
):
    """Statistik-Übersicht"""
    components = db.get_all_components()
    test_runs = db.get_all_test_runs()

    total_cycles = sum(c.get('total_switching_cycles', 0) for c in components)
    total_hours = sum(c.get('total_hours', 0) for c in components)

    completed_tests = [t for t in test_runs if t.get('status') == 'Abgeschlossen']

    return {
        "total_components": len(components),
        "total_test_runs": len(test_runs),
        "completed_tests": len(completed_tests),
        "total_cycles": total_cycles,
        "total_hours": round(total_hours, 1),
        "timestamp": datetime.now().isoformat()
    }


# ===== INITIALISIERUNG =====

def initialize_api(db: IndustrialDatabaseManager):
    """Initialisiert API mit Datenbank"""
    global db_manager
    db_manager = db


if __name__ == "__main__":
    import uvicorn

    # Datenbank initialisieren
    db = IndustrialDatabaseManager("data/pneumatic_teststand.db")
    initialize_api(db)

    # Server starten
    uvicorn.run(app, host="0.0.0.0", port=8000)
