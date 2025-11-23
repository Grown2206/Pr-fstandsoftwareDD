"""
Audit Trail System
Vollständige Nachverfolgung aller Aktivitäten
"""
import logging
from datetime import datetime
from typing import Optional
from ..database.db_manager import DatabaseManager
from ..models.user import AuditLogEntry


class AuditLogger:
    """Audit-Trail Logger für Compliance"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

        # Setup Python Logging
        self.logger = logging.getLogger('AuditTrail')
        self.logger.setLevel(logging.INFO)

        # File Handler
        handler = logging.FileHandler('data/audit_trail.log')
        handler.setLevel(logging.INFO)

        # Format
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(
        self,
        user_id: int,
        username: str,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        details: str = "",
        ip_address: Optional[str] = None,
        success: bool = True
    ):
        """
        Protokolliert eine Aktion

        Args:
            user_id: Benutzer-ID
            username: Benutzername
            action: Aktion (z.B. "CREATE", "UPDATE", "DELETE", "LOGIN")
            entity_type: Entitätstyp (z.B. "Component", "Test", "User")
            entity_id: ID der betroffenen Entität
            details: Zusätzliche Details
            ip_address: IP-Adresse
            success: Erfolgreich?
        """
        # Erstelle Log-Entry
        entry = AuditLogEntry(
            id=None,
            timestamp=datetime.now(),
            user_id=user_id,
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            success=success
        )

        # In Datenbank speichern
        self.db.create_audit_log(entry)

        # In Log-Datei schreiben
        status = "SUCCESS" if success else "FAILED"
        log_msg = f"{username} ({user_id}) | {action} | {entity_type}"
        if entity_id:
            log_msg += f" #{entity_id}"
        log_msg += f" | {status}"
        if details:
            log_msg += f" | {details}"

        if success:
            self.logger.info(log_msg)
        else:
            self.logger.error(log_msg)

    def log_login(self, user_id: int, username: str, success: bool, ip: Optional[str] = None):
        """Protokolliert Login"""
        self.log(
            user_id=user_id,
            username=username,
            action="LOGIN",
            entity_type="Authentication",
            details="Benutzer-Anmeldung",
            ip_address=ip,
            success=success
        )

    def log_logout(self, user_id: int, username: str):
        """Protokolliert Logout"""
        self.log(
            user_id=user_id,
            username=username,
            action="LOGOUT",
            entity_type="Authentication",
            details="Benutzer-Abmeldung"
        )

    def log_component_created(self, user_id: int, username: str, component_id: int, material_nr: str):
        """Protokolliert Komponenten-Erstellung"""
        self.log(
            user_id=user_id,
            username=username,
            action="CREATE",
            entity_type="Component",
            entity_id=component_id,
            details=f"Komponente erstellt: {material_nr}"
        )

    def log_test_started(self, user_id: int, username: str, test_run_id: int, component_id: int):
        """Protokolliert Test-Start"""
        self.log(
            user_id=user_id,
            username=username,
            action="START_TEST",
            entity_type="TestRun",
            entity_id=test_run_id,
            details=f"Test gestartet für Komponente #{component_id}"
        )

    def log_test_completed(self, user_id: int, username: str, test_run_id: int, result: str):
        """Protokolliert Test-Abschluss"""
        self.log(
            user_id=user_id,
            username=username,
            action="COMPLETE_TEST",
            entity_type="TestRun",
            entity_id=test_run_id,
            details=f"Test abgeschlossen: {result}"
        )

    def log_report_generated(self, user_id: int, username: str, component_id: int, report_path: str):
        """Protokolliert Berichterstellung"""
        self.log(
            user_id=user_id,
            username=username,
            action="GENERATE_REPORT",
            entity_type="Report",
            entity_id=component_id,
            details=f"Bericht erstellt: {report_path}"
        )

    def log_data_export(self, user_id: int, username: str, export_type: str, record_count: int):
        """Protokolliert Datenexport"""
        self.log(
            user_id=user_id,
            username=username,
            action="EXPORT_DATA",
            entity_type="Export",
            details=f"Typ: {export_type}, Anzahl: {record_count}"
        )

    def log_settings_change(self, user_id: int, username: str, setting_name: str, old_value: str, new_value: str):
        """Protokolliert Einstellungsänderung"""
        self.log(
            user_id=user_id,
            username=username,
            action="UPDATE_SETTINGS",
            entity_type="Settings",
            details=f"{setting_name}: {old_value} → {new_value}"
        )

    def log_calibration(self, user_id: int, username: str, equipment_id: int, result: str):
        """Protokolliert Kalibrierung"""
        self.log(
            user_id=user_id,
            username=username,
            action="CALIBRATE",
            entity_type="CalibrationEquipment",
            entity_id=equipment_id,
            details=f"Kalibrierung durchgeführt: {result}"
        )

    def log_approval(self, user_id: int, username: str, entity_type: str, entity_id: int, approved: bool):
        """Protokolliert Freigabe/Ablehnung"""
        action = "APPROVE" if approved else "REJECT"
        status = "freigegeben" if approved else "abgelehnt"
        self.log(
            user_id=user_id,
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=f"Entität {status}"
        )
