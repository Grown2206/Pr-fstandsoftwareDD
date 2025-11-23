"""
User Management System
Benutzer-Verwaltung mit Rollen und Rechten
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
import hashlib
import secrets


class UserRole(Enum):
    """Benutzer-Rollen"""
    ADMIN = "Administrator"
    ENGINEER = "Ingenieur"
    OPERATOR = "Bediener"
    VIEWER = "Betrachter"


class Permission(Enum):
    """Berechtigungen"""
    # Komponenten
    CREATE_COMPONENT = "Komponente erstellen"
    EDIT_COMPONENT = "Komponente bearbeiten"
    DELETE_COMPONENT = "Komponente löschen"
    VIEW_COMPONENT = "Komponente anzeigen"

    # Tests
    START_TEST = "Test starten"
    STOP_TEST = "Test stoppen"
    VIEW_TEST = "Test anzeigen"

    # Berichte
    GENERATE_REPORT = "Bericht erstellen"
    EXPORT_DATA = "Daten exportieren"

    # Verwaltung
    MANAGE_USERS = "Benutzer verwalten"
    MANAGE_CALIBRATION = "Kalibrierung verwalten"
    MANAGE_TEST_PROGRAMS = "Prüfprogramme verwalten"
    APPROVE_RESULTS = "Ergebnisse freigeben"

    # Konfiguration
    EDIT_SETTINGS = "Einstellungen bearbeiten"
    VIEW_AUDIT_LOG = "Audit-Log anzeigen"


# Rollenberechtigungen
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [p for p in Permission],  # Alle Rechte
    UserRole.ENGINEER: [
        Permission.CREATE_COMPONENT, Permission.EDIT_COMPONENT,
        Permission.DELETE_COMPONENT, Permission.VIEW_COMPONENT,
        Permission.START_TEST, Permission.STOP_TEST, Permission.VIEW_TEST,
        Permission.GENERATE_REPORT, Permission.EXPORT_DATA,
        Permission.MANAGE_CALIBRATION, Permission.MANAGE_TEST_PROGRAMS,
        Permission.APPROVE_RESULTS, Permission.VIEW_AUDIT_LOG
    ],
    UserRole.OPERATOR: [
        Permission.VIEW_COMPONENT,
        Permission.START_TEST, Permission.STOP_TEST, Permission.VIEW_TEST,
        Permission.GENERATE_REPORT
    ],
    UserRole.VIEWER: [
        Permission.VIEW_COMPONENT, Permission.VIEW_TEST
    ]
}


@dataclass
class User:
    """Benutzer-Model"""
    id: Optional[int]
    username: str
    password_hash: str
    full_name: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    def has_permission(self, permission: Permission) -> bool:
        """Prüft ob Benutzer eine Berechtigung hat"""
        return permission in ROLE_PERMISSIONS.get(self.role, [])

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple:
        """Hash ein Passwort mit Salt"""
        if salt is None:
            salt = secrets.token_hex(16)

        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return pwd_hash.hex(), salt

    def verify_password(self, password: str, salt: str) -> bool:
        """Verifiziert ein Passwort"""
        pwd_hash, _ = self.hash_password(password, salt)
        return pwd_hash == self.password_hash


@dataclass
class AuditLogEntry:
    """Audit-Log Eintrag"""
    id: Optional[int]
    timestamp: datetime
    user_id: int
    username: str
    action: str
    entity_type: str  # Component, Test, User, etc.
    entity_id: Optional[int]
    details: str
    ip_address: Optional[str] = None
    success: bool = True
