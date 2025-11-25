"""
Test Archiver - Archiviert alte Tests und exportiert sie
"""
import os
import json
import zipfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from ..database.db_manager import DatabaseManager


class TestArchiver:
    """Archiviert alte Test-Läufe"""

    def __init__(self, db_manager: DatabaseManager, archive_path: str = "data/archives"):
        self.db = db_manager
        self.archive_path = Path(archive_path)
        self.archive_path.mkdir(parents=True, exist_ok=True)

    def archive_old_tests(self, days_old: int = 90, delete_after_archive: bool = False) -> Dict:
        """
        Archiviert Tests, die älter als die angegebenen Tage sind

        Args:
            days_old: Tests älter als diese Anzahl an Tagen werden archiviert
            delete_after_archive: Wenn True, werden Tests nach dem Archivieren aus der DB gelöscht

        Returns:
            Dictionary mit Statistiken über archivierte Tests
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)

        # Alle alten Test-Läufe finden
        old_tests = self._get_old_tests(cutoff_date)

        if not old_tests:
            return {
                'success': True,
                'archived_count': 0,
                'message': f'Keine Tests älter als {days_old} Tage gefunden'
            }

        # Archiv-Dateiname erstellen
        archive_name = f"test_archive_{cutoff_date.strftime('%Y%m%d')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        archive_file = self.archive_path / archive_name

        # Tests exportieren und archivieren
        try:
            archived_count = self._create_archive(old_tests, archive_file)

            # Optional: Tests aus Datenbank löschen
            if delete_after_archive:
                self._delete_archived_tests(old_tests)

            return {
                'success': True,
                'archived_count': archived_count,
                'archive_file': str(archive_file),
                'deleted_from_db': delete_after_archive,
                'message': f'{archived_count} Tests wurden archiviert'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Fehler beim Archivieren: {str(e)}'
            }

    def _get_old_tests(self, cutoff_date: datetime) -> List:
        """Holt alle Tests, die älter als das Cutoff-Datum sind"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM test_runs
                WHERE date(start_time) < date(?)
                ORDER BY start_time ASC
            """, (cutoff_date.isoformat(),))

            return cursor.fetchall()

    def _create_archive(self, test_runs: List, archive_file: Path) -> int:
        """Erstellt ein ZIP-Archiv mit allen Test-Daten"""
        archived_count = 0

        with zipfile.ZipFile(archive_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Für jeden Test-Lauf
            for test_run in test_runs:
                test_id = test_run['id']
                component_id = test_run['component_id']
                start_time = test_run['start_time']

                # Komponenten-Info holen
                component = self.db.get_component(component_id)

                # Test-Daten sammeln
                test_data = {
                    'test_run': dict(test_run),
                    'component': {
                        'id': component.id,
                        'designation_1': component.designation_1,
                        'designation_2': component.designation_2,
                        'material_number': component.material_number,
                        'manufacturer_number': component.manufacturer_number,
                        'component_type': component.component_type.value,
                    } if component else None,
                    'measurements': self._get_measurements(test_id),
                    'configuration': self._get_test_configuration(test_run['config_id'])
                }

                # Als JSON im Archiv speichern
                json_filename = f"test_{test_id}_{start_time.replace(':', '-')}.json"
                zipf.writestr(json_filename, json.dumps(test_data, indent=2, ensure_ascii=False))

                archived_count += 1

            # Index-Datei erstellen
            index_data = {
                'archive_date': datetime.now().isoformat(),
                'test_count': archived_count,
                'tests': [
                    {
                        'test_id': test_run['id'],
                        'component_id': test_run['component_id'],
                        'start_time': test_run['start_time'],
                        'status': test_run['status'],
                        'completed_cycles': test_run['completed_cycles']
                    }
                    for test_run in test_runs
                ]
            }
            zipf.writestr('archive_index.json', json.dumps(index_data, indent=2, ensure_ascii=False))

        return archived_count

    def _get_measurements(self, test_run_id: int) -> List[Dict]:
        """Holt alle Messungen für einen Test-Lauf"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM test_measurements
                WHERE test_run_id = ?
                ORDER BY cycle_number ASC
            """, (test_run_id,))

            measurements = []
            for row in cursor.fetchall():
                measurements.append(dict(row))

            return measurements

    def _get_test_configuration(self, config_id: int) -> Optional[Dict]:
        """Holt die Test-Konfiguration"""
        if not config_id:
            return None

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM test_configurations
                WHERE id = ?
            """, (config_id,))

            row = cursor.fetchone()
            return dict(row) if row else None

    def _delete_archived_tests(self, test_runs: List):
        """Löscht archivierte Tests aus der Datenbank"""
        test_ids = [test_run['id'] for test_run in test_runs]

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Messungen löschen
            for test_id in test_ids:
                cursor.execute("DELETE FROM test_measurements WHERE test_run_id = ?", (test_id,))

            # Test-Läufe löschen
            for test_id in test_ids:
                cursor.execute("DELETE FROM test_runs WHERE id = ?", (test_id,))

            conn.commit()

    def list_archives(self) -> List[Dict]:
        """Listet alle vorhandenen Archive auf"""
        archives = []

        for archive_file in self.archive_path.glob("*.zip"):
            file_stats = archive_file.stat()

            # Versuche Index aus Archiv zu lesen
            try:
                with zipfile.ZipFile(archive_file, 'r') as zipf:
                    if 'archive_index.json' in zipf.namelist():
                        index_data = json.loads(zipf.read('archive_index.json'))
                        test_count = index_data.get('test_count', 0)
                        archive_date = index_data.get('archive_date', 'Unbekannt')
                    else:
                        test_count = len([name for name in zipf.namelist() if name.startswith('test_')])
                        archive_date = datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            except Exception:
                test_count = 0
                archive_date = datetime.fromtimestamp(file_stats.st_mtime).isoformat()

            archives.append({
                'filename': archive_file.name,
                'path': str(archive_file),
                'size_mb': file_stats.st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(file_stats.st_mtime),
                'test_count': test_count,
                'archive_date': archive_date
            })

        # Nach Datum sortieren (neueste zuerst)
        archives.sort(key=lambda x: x['created'], reverse=True)

        return archives

    def restore_archive(self, archive_file: str) -> Dict:
        """
        Stellt Tests aus einem Archiv wieder her

        Args:
            archive_file: Pfad zum Archiv

        Returns:
            Dictionary mit Statistiken über wiederhergestellte Tests
        """
        archive_path = Path(archive_file)

        if not archive_path.exists():
            return {
                'success': False,
                'error': 'Archiv-Datei nicht gefunden'
            }

        restored_count = 0
        errors = []

        try:
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                # Alle Test-Dateien durchgehen
                for filename in zipf.namelist():
                    if filename.startswith('test_') and filename.endswith('.json'):
                        try:
                            test_data = json.loads(zipf.read(filename))
                            self._restore_test(test_data)
                            restored_count += 1
                        except Exception as e:
                            errors.append(f"{filename}: {str(e)}")

            message = f'{restored_count} Tests wiederhergestellt'
            if errors:
                message += f', {len(errors)} Fehler'

            return {
                'success': True,
                'restored_count': restored_count,
                'errors': errors,
                'message': message
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Fehler beim Wiederherstellen: {str(e)}'
            }

    def _restore_test(self, test_data: Dict):
        """Stellt einen einzelnen Test wieder her"""
        # Hinweis: Diese Methode fügt Tests wieder zur Datenbank hinzu
        # Sie sollte mit Vorsicht verwendet werden, um Duplikate zu vermeiden

        test_run = test_data['test_run']

        # Prüfen, ob Test bereits existiert
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM test_runs WHERE id = ?", (test_run['id'],))
            if cursor.fetchone():
                # Test existiert bereits
                return

            # Test-Konfiguration wiederherstellen (falls nicht vorhanden)
            config = test_data.get('configuration')
            if config:
                cursor.execute("SELECT id FROM test_configurations WHERE id = ?", (config['id'],))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO test_configurations (
                            id, name, component_id, target_cycles, cycle_interval_ms,
                            max_duration_minutes, monitor_temperature, monitor_pressure,
                            alert_threshold_temperature, alert_threshold_pressure, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        config['id'], config['name'], config['component_id'],
                        config['target_cycles'], config['cycle_interval_ms'],
                        config['max_duration_minutes'], config['monitor_temperature'],
                        config['monitor_pressure'], config['alert_threshold_temperature'],
                        config['alert_threshold_pressure'], config.get('created_at')
                    ))

            # Test-Lauf wiederherstellen
            cursor.execute("""
                INSERT INTO test_runs (
                    id, component_id, config_id, start_time, end_time,
                    completed_cycles, target_cycles, status,
                    average_cycle_time_ms, min_cycle_time_ms, max_cycle_time_ms,
                    temperature_readings, pressure_readings, errors, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_run['id'], test_run['component_id'], test_run['config_id'],
                test_run['start_time'], test_run['end_time'],
                test_run['completed_cycles'], test_run['target_cycles'], test_run['status'],
                test_run['average_cycle_time_ms'], test_run['min_cycle_time_ms'],
                test_run['max_cycle_time_ms'], test_run['temperature_readings'],
                test_run['pressure_readings'], test_run['errors'], test_run.get('notes', '')
            ))

            # Messungen wiederherstellen
            measurements = test_data.get('measurements', [])
            for measurement in measurements:
                cursor.execute("""
                    INSERT INTO test_measurements (
                        id, test_run_id, timestamp, cycle_number, switching_time_ms,
                        temperature, pressure, successful, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    measurement['id'], measurement['test_run_id'],
                    measurement['timestamp'], measurement['cycle_number'],
                    measurement['switching_time_ms'], measurement['temperature'],
                    measurement['pressure'], measurement['successful'],
                    measurement.get('error_message')
                ))

            conn.commit()

    def get_archive_statistics(self) -> Dict:
        """Gibt Statistiken über alle Archive zurück"""
        archives = self.list_archives()

        if not archives:
            return {
                'total_archives': 0,
                'total_tests': 0,
                'total_size_mb': 0,
                'oldest_archive': None,
                'newest_archive': None
            }

        total_tests = sum(archive['test_count'] for archive in archives)
        total_size = sum(archive['size_mb'] for archive in archives)

        return {
            'total_archives': len(archives),
            'total_tests': total_tests,
            'total_size_mb': round(total_size, 2),
            'oldest_archive': archives[-1]['created'].strftime('%Y-%m-%d'),
            'newest_archive': archives[0]['created'].strftime('%Y-%m-%d')
        }
