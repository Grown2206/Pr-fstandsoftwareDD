"""
Industrial Database Extension
Erweitert die Datenbank um Industrie-Features
"""
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime

from .db_manager import DatabaseManager
from ..models.user import User, UserRole, AuditLogEntry
from ..models.test_program import TestProgram, TestStep, Batch
from ..models.calibration import CalibrationEquipment, CalibrationRecord, CalibrationStatus, CalibrationType


class IndustrialDatabaseManager(DatabaseManager):
    """Erweiterte Datenbank mit Industrie-Features"""

    def _initialize_database(self):
        """Erstellt alle Tabellen inkl. Industrie-Features"""
        # Basis-Tabellen erstellen
        super()._initialize_database()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # ===== BENUTZER-VERWALTUNG =====

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)

            # ===== AUDIT-TRAIL =====

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER,
                    details TEXT,
                    ip_address TEXT,
                    success BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_log(timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_user
                ON audit_log(user_id)
            """)

            # ===== PRÜFPROGRAMME =====

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_programs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    description TEXT,
                    component_type TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    is_approved BOOLEAN DEFAULT 0,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    revision_number INTEGER DEFAULT 1,
                    supersedes INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (approved_by) REFERENCES users(id),
                    FOREIGN KEY (supersedes) REFERENCES test_programs(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_program_id INTEGER NOT NULL,
                    step_number INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    step_type TEXT NOT NULL,
                    parameters TEXT,
                    limits TEXT,
                    instruction TEXT,
                    is_automated BOOLEAN DEFAULT 1,
                    is_mandatory BOOLEAN DEFAULT 1,
                    min_duration_seconds INTEGER,
                    max_duration_seconds INTEGER,
                    FOREIGN KEY (test_program_id) REFERENCES test_programs(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_program_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_program_id INTEGER NOT NULL,
                    test_run_id INTEGER NOT NULL,
                    component_id INTEGER NOT NULL,
                    batch_number TEXT,
                    serial_number TEXT,
                    status TEXT DEFAULT 'Läuft',
                    overall_result TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    operator_id INTEGER NOT NULL,
                    approved BOOLEAN DEFAULT 0,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    step_results TEXT,
                    FOREIGN KEY (test_program_id) REFERENCES test_programs(id),
                    FOREIGN KEY (test_run_id) REFERENCES test_runs(id),
                    FOREIGN KEY (component_id) REFERENCES components(id),
                    FOREIGN KEY (operator_id) REFERENCES users(id),
                    FOREIGN KEY (approved_by) REFERENCES users(id)
                )
            """)

            # ===== CHARGEN/BATCHES =====

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_number TEXT NOT NULL UNIQUE,
                    component_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    tested_quantity INTEGER DEFAULT 0,
                    passed_quantity INTEGER DEFAULT 0,
                    failed_quantity INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'Offen',
                    quality_status TEXT DEFAULT 'Ungeklärt',
                    supplier TEXT,
                    supplier_batch TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_batch_number
                ON batches(batch_number)
            """)

            # ===== KALIBRIERUNGS-VERWALTUNG =====

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calibration_equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    equipment_type TEXT NOT NULL,
                    manufacturer TEXT,
                    model TEXT,
                    serial_number TEXT,
                    calibration_interval_days INTEGER NOT NULL,
                    last_calibration_date TIMESTAMP,
                    next_calibration_date TIMESTAMP,
                    status TEXT NOT NULL,
                    accuracy_class TEXT,
                    measurement_range_min REAL DEFAULT 0.0,
                    measurement_range_max REAL DEFAULT 0.0,
                    unit TEXT,
                    location TEXT,
                    responsible_person TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calibration_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,
                    calibration_date TIMESTAMP NOT NULL,
                    calibration_type TEXT NOT NULL,
                    calibrated_by TEXT NOT NULL,
                    laboratory TEXT,
                    result TEXT DEFAULT 'Bestanden',
                    deviation REAL,
                    uncertainty REAL,
                    certificate_number TEXT,
                    certificate_file TEXT,
                    next_calibration_date TIMESTAMP,
                    remarks TEXT,
                    measurement_points TEXT,
                    cost REAL DEFAULT 0.0,
                    FOREIGN KEY (equipment_id) REFERENCES calibration_equipment(id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cal_next_date
                ON calibration_equipment(next_calibration_date)
            """)

            # ===== DEFAULT ADMIN BENUTZER =====
            # Erstelle Standard-Admin wenn noch keine Benutzer existieren
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']

            if user_count == 0:
                from ..models.user import User
                password_hash, salt = User.hash_password("admin")
                cursor.execute("""
                    INSERT INTO users (username, password_hash, password_salt, full_name, email, role)
                    VALUES ('admin', ?, ?, 'Administrator', 'admin@teststand.local', 'Administrator')
                """, (password_hash, salt))

    # ===== BENUTZER-OPERATIONEN =====

    def create_user(self, user: User, password: str) -> int:
        """Erstellt neuen Benutzer"""
        password_hash, salt = User.hash_password(password)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password_hash, password_salt, full_name, email, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user.username, password_hash, salt, user.full_name, user.email, user.role.value, user.is_active))
            return cursor.lastrowid

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Holt Benutzer nach Username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'],
                    username=row['username'],
                    password_hash=row['password_hash'],
                    full_name=row['full_name'],
                    email=row['email'],
                    role=UserRole(row['role']),
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None
                )
            return None

    def get_password_salt(self, username: str) -> Optional[str]:
        """Holt Salt für Passwort-Verifizierung"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_salt FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return row['password_salt'] if row else None

    def update_last_login(self, user_id: int):
        """Aktualisiert letzten Login"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now(), user_id))

    def get_all_users(self) -> List[User]:
        """Holt alle Benutzer"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY username")
            users = []
            for row in cursor.fetchall():
                users.append(User(
                    id=row['id'],
                    username=row['username'],
                    password_hash=row['password_hash'],
                    full_name=row['full_name'],
                    email=row['email'],
                    role=UserRole(row['role']),
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None
                ))
            return users

    # ===== AUDIT-LOG OPERATIONEN =====

    def create_audit_log(self, entry: AuditLogEntry) -> int:
        """Erstellt Audit-Log Eintrag"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_log (timestamp, user_id, username, action, entity_type, entity_id, details, ip_address, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry.timestamp, entry.user_id, entry.username, entry.action, entry.entity_type,
                  entry.entity_id, entry.details, entry.ip_address, entry.success))
            return cursor.lastrowid

    def get_audit_log(self, limit: int = 100, user_id: Optional[int] = None) -> List[Dict]:
        """Holt Audit-Log Einträge"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                    SELECT * FROM audit_log WHERE user_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # ===== BATCH OPERATIONEN =====

    def create_batch(self, batch: Batch) -> int:
        """Erstellt Batch/Charge"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO batches (batch_number, component_type, quantity, supplier, supplier_batch, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (batch.batch_number, batch.component_type, batch.quantity, batch.supplier, batch.supplier_batch, batch.notes))
            return cursor.lastrowid

    def get_batch(self, batch_number: str) -> Optional[Dict]:
        """Holt Batch nach Nummer"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM batches WHERE batch_number = ?", (batch_number,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_batch_progress(self, batch_number: str, tested: int, passed: int, failed: int):
        """Aktualisiert Batch-Fortschritt"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE batches SET tested_quantity = ?, passed_quantity = ?, failed_quantity = ?
                WHERE batch_number = ?
            """, (tested, passed, failed, batch_number))

    # ===== KALIBRIERUNGS OPERATIONEN =====

    def create_calibration_equipment(self, equipment: CalibrationEquipment) -> int:
        """Erstellt Kalibrierungs-Equipment"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO calibration_equipment (
                    equipment_id, name, equipment_type, manufacturer, model, serial_number,
                    calibration_interval_days, last_calibration_date, next_calibration_date,
                    status, accuracy_class, measurement_range_min, measurement_range_max,
                    unit, location, responsible_person, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (equipment.equipment_id, equipment.name, equipment.equipment_type,
                  equipment.manufacturer, equipment.model, equipment.serial_number,
                  equipment.calibration_interval_days, equipment.last_calibration_date,
                  equipment.next_calibration_date, equipment.status.value,
                  equipment.accuracy_class, equipment.measurement_range_min,
                  equipment.measurement_range_max, equipment.unit, equipment.location,
                  equipment.responsible_person, equipment.notes))
            return cursor.lastrowid

    def get_calibration_due_soon(self, days: int = 30) -> List[Dict]:
        """Holt Equipment mit baldiger Kalibrierung"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            from_date = datetime.now()
            to_date = datetime.now().replace(hour=23, minute=59, second=59) + \
                      timedelta(days=days)

            cursor.execute("""
                SELECT * FROM calibration_equipment
                WHERE next_calibration_date BETWEEN ? AND ?
                ORDER BY next_calibration_date
            """, (from_date, to_date))

            return [dict(row) for row in cursor.fetchall()]

    def create_calibration_record(self, record: CalibrationRecord) -> int:
        """Erstellt Kalibrierprotokoll"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO calibration_records (
                    equipment_id, calibration_date, calibration_type, calibrated_by,
                    laboratory, result, deviation, uncertainty, certificate_number,
                    certificate_file, next_calibration_date, remarks, measurement_points, cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (record.equipment_id, record.calibration_date, record.calibration_type.value,
                  record.calibrated_by, record.laboratory, record.result, record.deviation,
                  record.uncertainty, record.certificate_number, record.certificate_file,
                  record.next_calibration_date, record.remarks, record.measurement_points, record.cost))
            return cursor.lastrowid
