"""
Export Manager
Erweiterte Export-Funktionen für CSV, Excel, PDF
"""
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd


class ExportManager:
    """Manager für Datenexporte"""

    def __init__(self, export_dir: str = "data/exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        fieldnames: List[str] = None
    ) -> str:
        """
        Exportiert Daten als CSV

        Args:
            data: Liste von Dictionaries
            filename: Dateiname (ohne .csv)
            fieldnames: Spalten (optional, wird aus Daten extrahiert)

        Returns:
            Pfad zur erstellten Datei
        """
        if not data:
            raise ValueError("Keine Daten zum Exportieren")

        # Timestamp hinzufügen
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{filename}_{timestamp}.csv"
        csv_path = self.export_dir / csv_filename

        # Fieldnames aus erstem Eintrag wenn nicht angegeben
        if not fieldnames:
            fieldnames = list(data[0].keys())

        # CSV schreiben
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(data)

        return str(csv_path)

    def export_to_excel(
        self,
        data: Dict[str, List[Dict[str, Any]]],
        filename: str,
        sheet_names: List[str] = None
    ) -> str:
        """
        Exportiert Daten als Excel mit mehreren Sheets

        Args:
            data: Dictionary {sheet_name: data_list}
            filename: Dateiname (ohne .xlsx)
            sheet_names: Sheet-Namen (optional)

        Returns:
            Pfad zur erstellten Datei
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"{filename}_{timestamp}.xlsx"
        excel_path = self.export_dir / excel_filename

        # Excel Writer erstellen
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for sheet_name, sheet_data in data.items():
                if sheet_data:
                    df = pd.DataFrame(sheet_data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

                    # Autofit Spaltenbreite
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(cell.value)
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width

        return str(excel_path)

    def export_test_results_csv(
        self,
        component_name: str,
        test_runs: List[Dict],
        measurements: List[Dict] = None
    ) -> str:
        """Exportiert Testergebnisse als CSV"""

        # Test-Runs exportieren
        test_runs_data = []
        for tr in test_runs:
            test_runs_data.append({
                'Test-ID': tr.get('id'),
                'Startzeit': tr.get('start_time'),
                'Endzeit': tr.get('end_time'),
                'Zyklen': tr.get('completed_cycles'),
                'Ziel-Zyklen': tr.get('target_cycles'),
                'Status': tr.get('status'),
                'Ø Schaltzeit (ms)': round(tr.get('average_cycle_time_ms', 0), 2),
                'Min Schaltzeit (ms)': round(tr.get('min_cycle_time_ms', 0), 2),
                'Max Schaltzeit (ms)': round(tr.get('max_cycle_time_ms', 0), 2)
            })

        filename = f"test_results_{component_name.replace(' ', '_')}"
        return self.export_to_csv(test_runs_data, filename)

    def export_test_results_excel(
        self,
        component_name: str,
        component_info: Dict,
        test_runs: List[Dict],
        measurements: List[Dict],
        statistics: Dict = None
    ) -> str:
        """Exportiert umfassende Testergebnisse als Excel"""

        data = {}

        # Sheet 1: Komponenten-Info
        data['Komponente'] = [{
            'Bezeichnung 1': component_info.get('designation_1'),
            'Bezeichnung 2': component_info.get('designation_2'),
            'Materialnummer': component_info.get('material_number'),
            'Herstellernummer': component_info.get('manufacturer_number'),
            'Typ': component_info.get('component_type'),
            'Gesamt Tests': component_info.get('total_tests'),
            'Gesamt Zyklen': component_info.get('total_switching_cycles'),
            'Gesamt Stunden': round(component_info.get('total_hours', 0), 2)
        }]

        # Sheet 2: Test-Runs
        test_runs_data = []
        for tr in test_runs:
            test_runs_data.append({
                'Test-ID': tr.get('id'),
                'Startzeit': tr.get('start_time'),
                'Endzeit': tr.get('end_time'),
                'Zyklen': tr.get('completed_cycles'),
                'Ziel-Zyklen': tr.get('target_cycles'),
                'Status': tr.get('status'),
                'Ø Schaltzeit (ms)': round(tr.get('average_cycle_time_ms', 0), 2),
                'Min Schaltzeit (ms)': round(tr.get('min_cycle_time_ms', 0), 2),
                'Max Schaltzeit (ms)': round(tr.get('max_cycle_time_ms', 0), 2)
            })
        data['Testläufe'] = test_runs_data

        # Sheet 3: Messungen (Sample - erste 1000)
        if measurements:
            measurements_data = []
            for m in measurements[:1000]:
                measurements_data.append({
                    'Zyklus': m.get('cycle_number'),
                    'Zeitstempel': m.get('timestamp'),
                    'Schaltzeit (ms)': round(m.get('switching_time_ms', 0), 2),
                    'Temperatur (°C)': round(m.get('temperature', 0), 1) if m.get('temperature') else None,
                    'Druck (bar)': round(m.get('pressure', 0), 2) if m.get('pressure') else None,
                    'Erfolgreich': 'Ja' if m.get('successful') else 'Nein',
                    'Fehler': m.get('error_message', '')
                })
            data['Messungen (Sample)'] = measurements_data

        # Sheet 4: Statistik
        if statistics:
            data['Statistik'] = [statistics]

        filename = f"test_report_{component_name.replace(' ', '_')}"
        return self.export_to_excel(data, filename)

    def export_audit_log_csv(self, audit_entries: List[Dict]) -> str:
        """Exportiert Audit-Log als CSV"""
        audit_data = []
        for entry in audit_entries:
            audit_data.append({
                'Zeitstempel': entry.get('timestamp'),
                'Benutzer': entry.get('username'),
                'Aktion': entry.get('action'),
                'Entität': entry.get('entity_type'),
                'Entitäts-ID': entry.get('entity_id', ''),
                'Details': entry.get('details', ''),
                'Erfolg': 'Ja' if entry.get('success') else 'Nein',
                'IP-Adresse': entry.get('ip_address', '')
            })

        return self.export_to_csv(audit_data, "audit_log")

    def export_spc_data(
        self,
        component_name: str,
        measurements: List[float],
        spc_result: Dict
    ) -> str:
        """Exportiert SPC-Daten als Excel"""

        data = {}

        # Sheet 1: SPC-Kennzahlen
        data['SPC-Kennzahlen'] = [{
            'Kennzahl': 'Cp',
            'Wert': spc_result.get('cp', 0),
            'Beschreibung': 'Prozessfähigkeit'
        }, {
            'Kennzahl': 'Cpk',
            'Wert': spc_result.get('cpk', 0),
            'Beschreibung': 'Prozessfähigkeitsindex'
        }, {
            'Kennzahl': 'Pp',
            'Wert': spc_result.get('pp', 0),
            'Beschreibung': 'Prozessleistung'
        }, {
            'Kennzahl': 'Ppk',
            'Wert': spc_result.get('ppk', 0),
            'Beschreibung': 'Prozessleistungsindex'
        }, {
            'Kennzahl': 'Mittelwert',
            'Wert': spc_result.get('mean', 0),
            'Beschreibung': 'Durchschnitt'
        }, {
            'Kennzahl': 'Standardabweichung',
            'Wert': spc_result.get('std_dev', 0),
            'Beschreibung': 'Streuung'
        }, {
            'Kennzahl': 'Ausschussrate %',
            'Wert': spc_result.get('out_of_spec_percent', 0),
            'Beschreibung': 'Anteil außerhalb Spezifikation'
        }]

        # Sheet 2: Messwerte
        data['Messwerte'] = [{'Wert': v} for v in measurements]

        # Sheet 3: Grenzwerte
        data['Grenzwerte'] = [{
            'Grenze': 'USG (LSL)',
            'Wert': spc_result.get('lower_spec_limit', 0)
        }, {
            'Grenze': 'OSG (USL)',
            'Wert': spc_result.get('upper_spec_limit', 0)
        }]

        filename = f"spc_analysis_{component_name.replace(' ', '_')}"
        return self.export_to_excel(data, filename)

    def export_calibration_records(self, calibration_data: List[Dict]) -> str:
        """Exportiert Kalibrierprotokolle"""
        cal_data = []
        for cal in calibration_data:
            cal_data.append({
                'Prüfmittel-Nr': cal.get('equipment_id'),
                'Bezeichnung': cal.get('name'),
                'Typ': cal.get('equipment_type'),
                'Hersteller': cal.get('manufacturer'),
                'Seriennummer': cal.get('serial_number'),
                'Letzte Kalibrierung': cal.get('last_calibration_date'),
                'Nächste Kalibrierung': cal.get('next_calibration_date'),
                'Status': cal.get('status'),
                'Verantwortlich': cal.get('responsible_person')
            })

        return self.export_to_csv(cal_data, "calibration_records")
