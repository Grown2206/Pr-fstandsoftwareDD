"""
Database Manager for Pneumatic Test Stand
Handles all database operations using SQLite
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path

from ..models.component import (
    Component, ComponentType, ComponentStatus,
    TestConfiguration, TestRun, TestMeasurement
)


class DatabaseManager:
    """Manages all database operations"""

    def __init__(self, db_path: str = "data/teststand.db"):
        self.db_path = db_path
        self._ensure_directory()
        self._initialize_database()

    def _ensure_directory(self):
        """Ensure database directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _initialize_database(self):
        """Create all necessary tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Components table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    designation_1 TEXT NOT NULL,
                    designation_2 TEXT NOT NULL,
                    material_number TEXT NOT NULL UNIQUE,
                    manufacturer_number TEXT NOT NULL,
                    component_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_tests INTEGER DEFAULT 0,
                    total_switching_cycles INTEGER DEFAULT 0,
                    total_hours REAL DEFAULT 0.0,
                    total_minutes REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Test configurations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    component_id INTEGER NOT NULL,
                    target_cycles INTEGER NOT NULL,
                    cycle_interval_ms INTEGER NOT NULL,
                    max_duration_minutes INTEGER NOT NULL,
                    monitor_temperature BOOLEAN DEFAULT 1,
                    monitor_pressure BOOLEAN DEFAULT 1,
                    alert_threshold_temperature REAL DEFAULT 80.0,
                    alert_threshold_pressure REAL DEFAULT 10.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (component_id) REFERENCES components(id)
                )
            """)

            # Test runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component_id INTEGER NOT NULL,
                    config_id INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    completed_cycles INTEGER DEFAULT 0,
                    target_cycles INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    average_cycle_time_ms REAL DEFAULT 0.0,
                    min_cycle_time_ms REAL DEFAULT 0.0,
                    max_cycle_time_ms REAL DEFAULT 0.0,
                    temperature_readings TEXT,
                    pressure_readings TEXT,
                    errors TEXT,
                    notes TEXT,
                    FOREIGN KEY (component_id) REFERENCES components(id),
                    FOREIGN KEY (config_id) REFERENCES test_configurations(id)
                )
            """)

            # Test measurements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_run_id INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    cycle_number INTEGER NOT NULL,
                    switching_time_ms REAL NOT NULL,
                    temperature REAL,
                    pressure REAL,
                    successful BOOLEAN NOT NULL,
                    error_message TEXT,
                    FOREIGN KEY (test_run_id) REFERENCES test_runs(id)
                )
            """)

            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_component_material
                ON components(material_number)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_test_runs_component
                ON test_runs(component_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_measurements_test_run
                ON test_measurements(test_run_id)
            """)

    # ===== Component Operations =====

    def create_component(self, component: Component) -> int:
        """Create a new component"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO components (
                    designation_1, designation_2, material_number,
                    manufacturer_number, component_type, status,
                    total_tests, total_switching_cycles, total_hours, total_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                component.designation_1, component.designation_2,
                component.material_number, component.manufacturer_number,
                component.component_type.value, component.status.value,
                component.total_tests, component.total_switching_cycles,
                component.total_hours, component.total_minutes
            ))
            return cursor.lastrowid

    def get_component(self, component_id: int) -> Optional[Component]:
        """Get component by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM components WHERE id = ?", (component_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_component(row)
            return None

    def get_all_components(self) -> List[Component]:
        """Get all components"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM components ORDER BY created_at DESC")
            return [self._row_to_component(row) for row in cursor.fetchall()]

    def update_component(self, component: Component):
        """Update component"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE components SET
                    designation_1 = ?, designation_2 = ?, material_number = ?,
                    manufacturer_number = ?, component_type = ?, status = ?,
                    total_tests = ?, total_switching_cycles = ?,
                    total_hours = ?, total_minutes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                component.designation_1, component.designation_2,
                component.material_number, component.manufacturer_number,
                component.component_type.value, component.status.value,
                component.total_tests, component.total_switching_cycles,
                component.total_hours, component.total_minutes, component.id
            ))

    def delete_component(self, component_id: int):
        """Delete component"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM components WHERE id = ?", (component_id,))

    # ===== Test Configuration Operations =====

    def create_test_configuration(self, config: TestConfiguration) -> int:
        """Create test configuration"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO test_configurations (
                    name, component_id, target_cycles, cycle_interval_ms,
                    max_duration_minutes, monitor_temperature, monitor_pressure,
                    alert_threshold_temperature, alert_threshold_pressure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.name, config.component_id, config.target_cycles,
                config.cycle_interval_ms, config.max_duration_minutes,
                config.monitor_temperature, config.monitor_pressure,
                config.alert_threshold_temperature, config.alert_threshold_pressure
            ))
            return cursor.lastrowid

    def get_configurations_for_component(self, component_id: int) -> List[TestConfiguration]:
        """Get all configurations for a component"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM test_configurations
                WHERE component_id = ?
                ORDER BY created_at DESC
            """, (component_id,))
            return [self._row_to_config(row) for row in cursor.fetchall()]

    # ===== Test Run Operations =====

    def create_test_run(self, test_run: TestRun) -> int:
        """Create a new test run"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO test_runs (
                    component_id, config_id, start_time, end_time,
                    completed_cycles, target_cycles, status,
                    average_cycle_time_ms, min_cycle_time_ms, max_cycle_time_ms,
                    temperature_readings, pressure_readings, errors, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_run.component_id, test_run.config_id, test_run.start_time,
                test_run.end_time, test_run.completed_cycles, test_run.target_cycles,
                test_run.status, test_run.average_cycle_time_ms,
                test_run.min_cycle_time_ms, test_run.max_cycle_time_ms,
                test_run.temperature_readings, test_run.pressure_readings,
                test_run.errors, test_run.notes
            ))
            return cursor.lastrowid

    def update_test_run(self, test_run: TestRun):
        """Update test run"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE test_runs SET
                    end_time = ?, completed_cycles = ?, status = ?,
                    average_cycle_time_ms = ?, min_cycle_time_ms = ?,
                    max_cycle_time_ms = ?, temperature_readings = ?,
                    pressure_readings = ?, errors = ?, notes = ?
                WHERE id = ?
            """, (
                test_run.end_time, test_run.completed_cycles, test_run.status,
                test_run.average_cycle_time_ms, test_run.min_cycle_time_ms,
                test_run.max_cycle_time_ms, test_run.temperature_readings,
                test_run.pressure_readings, test_run.errors, test_run.notes,
                test_run.id
            ))

    def get_test_run(self, test_run_id: int) -> Optional[TestRun]:
        """Get test run by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test_runs WHERE id = ?", (test_run_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_test_run(row)
            return None

    def get_test_runs_for_component(self, component_id: int) -> List[TestRun]:
        """Get all test runs for a component"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM test_runs
                WHERE component_id = ?
                ORDER BY start_time DESC
            """, (component_id,))
            return [self._row_to_test_run(row) for row in cursor.fetchall()]

    # ===== Test Measurement Operations =====

    def create_measurement(self, measurement: TestMeasurement) -> int:
        """Create a new measurement"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO test_measurements (
                    test_run_id, timestamp, cycle_number, switching_time_ms,
                    temperature, pressure, successful, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                measurement.test_run_id, measurement.timestamp,
                measurement.cycle_number, measurement.switching_time_ms,
                measurement.temperature, measurement.pressure,
                measurement.successful, measurement.error_message
            ))
            return cursor.lastrowid

    def get_measurements_for_test_run(self, test_run_id: int) -> List[TestMeasurement]:
        """Get all measurements for a test run"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM test_measurements
                WHERE test_run_id = ?
                ORDER BY cycle_number
            """, (test_run_id,))
            return [self._row_to_measurement(row) for row in cursor.fetchall()]

    # ===== Helper Methods =====

    def _row_to_component(self, row) -> Component:
        """Convert database row to Component object"""
        return Component(
            id=row['id'],
            designation_1=row['designation_1'],
            designation_2=row['designation_2'],
            material_number=row['material_number'],
            manufacturer_number=row['manufacturer_number'],
            component_type=ComponentType(row['component_type']),
            status=ComponentStatus(row['status']),
            total_tests=row['total_tests'],
            total_switching_cycles=row['total_switching_cycles'],
            total_hours=row['total_hours'],
            total_minutes=row['total_minutes'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    def _row_to_config(self, row) -> TestConfiguration:
        """Convert database row to TestConfiguration object"""
        return TestConfiguration(
            id=row['id'],
            name=row['name'],
            component_id=row['component_id'],
            target_cycles=row['target_cycles'],
            cycle_interval_ms=row['cycle_interval_ms'],
            max_duration_minutes=row['max_duration_minutes'],
            monitor_temperature=bool(row['monitor_temperature']),
            monitor_pressure=bool(row['monitor_pressure']),
            alert_threshold_temperature=row['alert_threshold_temperature'],
            alert_threshold_pressure=row['alert_threshold_pressure'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )

    def _row_to_test_run(self, row) -> TestRun:
        """Convert database row to TestRun object"""
        return TestRun(
            id=row['id'],
            component_id=row['component_id'],
            config_id=row['config_id'],
            start_time=datetime.fromisoformat(row['start_time']),
            end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
            completed_cycles=row['completed_cycles'],
            target_cycles=row['target_cycles'],
            status=row['status'],
            average_cycle_time_ms=row['average_cycle_time_ms'],
            min_cycle_time_ms=row['min_cycle_time_ms'],
            max_cycle_time_ms=row['max_cycle_time_ms'],
            temperature_readings=row['temperature_readings'] or "[]",
            pressure_readings=row['pressure_readings'] or "[]",
            errors=row['errors'] or "[]",
            notes=row['notes'] or ""
        )

    def _row_to_measurement(self, row) -> TestMeasurement:
        """Convert database row to TestMeasurement object"""
        return TestMeasurement(
            id=row['id'],
            test_run_id=row['test_run_id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            cycle_number=row['cycle_number'],
            switching_time_ms=row['switching_time_ms'],
            temperature=row['temperature'],
            pressure=row['pressure'],
            successful=bool(row['successful']),
            error_message=row['error_message']
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Total components
            cursor.execute("SELECT COUNT(*) as count FROM components")
            total_components = cursor.fetchone()['count']

            # Total test runs
            cursor.execute("SELECT COUNT(*) as count FROM test_runs")
            total_test_runs = cursor.fetchone()['count']

            # Total cycles
            cursor.execute("SELECT SUM(total_switching_cycles) as total FROM components")
            total_cycles = cursor.fetchone()['total'] or 0

            # Total hours
            cursor.execute("SELECT SUM(total_hours) as total FROM components")
            total_hours = cursor.fetchone()['total'] or 0

            return {
                'total_components': total_components,
                'total_test_runs': total_test_runs,
                'total_switching_cycles': total_cycles,
                'total_hours': round(total_hours, 2)
            }
