"""
OEE Calculator
Overall Equipment Effectiveness - Gesamtanlageneffektivität
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


@dataclass
class OEEResult:
    """OEE-Ergebnis"""
    # Hauptkennzahlen
    oee: float  # Overall Equipment Effectiveness (0-100%)
    availability: float  # Verfügbarkeit (0-100%)
    performance: float  # Leistung (0-100%)
    quality: float  # Qualität (0-100%)

    # Zeitkomponenten
    planned_production_time: float  # Geplante Produktionszeit (Minuten)
    actual_operating_time: float  # Tatsächliche Betriebszeit (Minuten)
    downtime: float  # Stillstandszeit (Minuten)

    # Mengenkomponenten
    ideal_cycle_time: float  # Ideale Zykluszeit (Sekunden)
    total_pieces: int  # Gesamtproduktion (Stück)
    good_pieces: int  # Gutteile (Stück)
    rejected_pieces: int  # Ausschuss (Stück)

    # Berechnete Werte
    theoretical_output: int  # Theoretische Menge
    actual_output: int  # Tatsächliche Menge

    # Bewertung
    rating: str  # "World Class", "Gut", "Durchschnitt", "Verbesserungsbedarf"

    # Verluste
    availability_loss: float  # Verfügbarkeitsverlust (%)
    performance_loss: float  # Leistungsverlust (%)
    quality_loss: float  # Qualitätsverlust (%)


class OEECalculator:
    """Berechnet OEE-Kennzahlen"""

    # OEE-Bewertung nach Industriestandard
    WORLD_CLASS_OEE = 85.0  # World Class Manufacturing
    GOOD_OEE = 60.0
    AVERAGE_OEE = 40.0

    @staticmethod
    def calculate_oee(
        planned_production_time_minutes: float,
        downtime_minutes: float,
        ideal_cycle_time_seconds: float,
        total_pieces: int,
        good_pieces: int
    ) -> OEEResult:
        """
        Berechnet OEE

        Args:
            planned_production_time_minutes: Geplante Produktionszeit in Minuten
            downtime_minutes: Stillstandszeit in Minuten
            ideal_cycle_time_seconds: Ideale Zykluszeit in Sekunden
            total_pieces: Gesamtanzahl produzierter Teile
            good_pieces: Anzahl Gutteile

        Returns:
            OEEResult mit allen Kennzahlen
        """
        # 1. VERFÜGBARKEIT (Availability)
        # Verfügbarkeit = Betriebszeit / Geplante Produktionszeit
        actual_operating_time = planned_production_time_minutes - downtime_minutes
        availability = (actual_operating_time / planned_production_time_minutes * 100) if planned_production_time_minutes > 0 else 0

        # 2. LEISTUNG (Performance)
        # Leistung = (Tatsächliche Menge / Theoretische Menge) * 100
        theoretical_output = int((actual_operating_time * 60) / ideal_cycle_time_seconds) if ideal_cycle_time_seconds > 0 else 0
        performance = (total_pieces / theoretical_output * 100) if theoretical_output > 0 else 0
        # Cap bei 100% (Überproduktion nicht als Verbesserung werten)
        performance = min(performance, 100.0)

        # 3. QUALITÄT (Quality)
        # Qualität = Gutteile / Gesamtproduktion * 100
        quality = (good_pieces / total_pieces * 100) if total_pieces > 0 else 0

        # OEE = Verfügbarkeit × Leistung × Qualität
        oee = (availability / 100) * (performance / 100) * (quality / 100) * 100

        # Verluste berechnen
        availability_loss = 100 - availability
        performance_loss = 100 - performance
        quality_loss = 100 - quality

        # Ausschuss
        rejected_pieces = total_pieces - good_pieces

        # Bewertung
        rating = OEECalculator._rate_oee(oee)

        return OEEResult(
            oee=round(oee, 2),
            availability=round(availability, 2),
            performance=round(performance, 2),
            quality=round(quality, 2),
            planned_production_time=planned_production_time_minutes,
            actual_operating_time=actual_operating_time,
            downtime=downtime_minutes,
            ideal_cycle_time=ideal_cycle_time_seconds,
            total_pieces=total_pieces,
            good_pieces=good_pieces,
            rejected_pieces=rejected_pieces,
            theoretical_output=theoretical_output,
            actual_output=total_pieces,
            rating=rating,
            availability_loss=round(availability_loss, 2),
            performance_loss=round(performance_loss, 2),
            quality_loss=round(quality_loss, 2)
        )

    @staticmethod
    def _rate_oee(oee: float) -> str:
        """Bewertet OEE-Wert"""
        if oee >= OEECalculator.WORLD_CLASS_OEE:
            return "World Class (≥85%)"
        elif oee >= OEECalculator.GOOD_OEE:
            return "Gut (≥60%)"
        elif oee >= OEECalculator.AVERAGE_OEE:
            return "Durchschnittlich (≥40%)"
        else:
            return "Verbesserungsbedarf (<40%)"

    @staticmethod
    def calculate_from_test_runs(test_runs: List[Dict]) -> Optional[OEEResult]:
        """
        Berechnet OEE aus Testläufen

        Args:
            test_runs: Liste von Test-Run Dictionaries

        Returns:
            OEEResult oder None wenn nicht genug Daten
        """
        if not test_runs:
            return None

        # Aggregiere Daten
        total_planned_time = 0.0
        total_downtime = 0.0
        total_pieces = 0
        total_good_pieces = 0
        cycle_times = []

        for run in test_runs:
            if run.get('end_time') and run.get('start_time'):
                # Geplante Zeit
                duration = (run['end_time'] - run['start_time']).total_seconds() / 60
                total_planned_time += duration

                # Pieces
                completed = run.get('completed_cycles', 0)
                target = run.get('target_cycles', 0)
                total_pieces += completed

                # Quality (angenommen: Tests mit "Completed" Status sind i.O.)
                if run.get('status') == 'Completed':
                    # Fehlerrate aus errors JSON
                    import json
                    errors = json.loads(run.get('errors', '[]'))
                    failed_cycles = len(errors)
                    good_cycles = completed - failed_cycles
                    total_good_pieces += max(0, good_cycles)
                else:
                    # Abgebrochen oder fehlgeschlagen = alle schlecht
                    pass

                # Downtime = Zeit wo nicht produziert wurde
                if completed < target:
                    # Unvollständig = Downtime
                    missing_cycles = target - completed
                    avg_cycle_time = run.get('average_cycle_time_ms', 100) / 1000
                    total_downtime += (missing_cycles * avg_cycle_time) / 60

                # Cycle Times
                if run.get('average_cycle_time_ms'):
                    cycle_times.append(run['average_cycle_time_ms'] / 1000)

        # Ideale Zykluszeit = Minimum der durchschnittlichen Zeiten
        if cycle_times:
            ideal_cycle_time = min(cycle_times)
        else:
            ideal_cycle_time = 0.1  # Default 100ms

        if total_planned_time == 0:
            return None

        return OEECalculator.calculate_oee(
            planned_production_time_minutes=total_planned_time,
            downtime_minutes=total_downtime,
            ideal_cycle_time_seconds=ideal_cycle_time,
            total_pieces=total_pieces,
            good_pieces=total_good_pieces
        )

    @staticmethod
    def generate_oee_report(result: OEEResult) -> str:
        """Generiert OEE-Textbericht"""
        report = "=== OEE-ANALYSE (Overall Equipment Effectiveness) ===\n\n"

        report += "GESAMTANLAGENEFFEKTIVITÄT:\n"
        report += f"  OEE: {result.oee:.2f}%\n"
        report += f"  Bewertung: {result.rating}\n\n"

        report += "KOMPONENTEN:\n"
        report += f"  Verfügbarkeit: {result.availability:.2f}%\n"
        report += f"  Leistung:      {result.performance:.2f}%\n"
        report += f"  Qualität:      {result.quality:.2f}%\n\n"

        report += "ZEIT-ANALYSE:\n"
        report += f"  Geplante Zeit:  {result.planned_production_time:.1f} min\n"
        report += f"  Betriebszeit:   {result.actual_operating_time:.1f} min\n"
        report += f"  Stillstandszeit: {result.downtime:.1f} min\n"
        report += f"  Verfügbarkeit:  {result.availability:.1f}%\n\n"

        report += "MENGEN-ANALYSE:\n"
        report += f"  Theoretische Menge: {result.theoretical_output:,} Stück\n"
        report += f"  Tatsächliche Menge: {result.actual_output:,} Stück\n"
        report += f"  Gutteile:          {result.good_pieces:,} Stück\n"
        report += f"  Ausschuss:         {result.rejected_pieces:,} Stück\n\n"

        report += "VERLUSTE:\n"
        report += f"  Verfügbarkeitsverlust: {result.availability_loss:.2f}%\n"
        report += f"  Leistungsverlust:      {result.performance_loss:.2f}%\n"
        report += f"  Qualitätsverlust:      {result.quality_loss:.2f}%\n\n"

        # Interpretation
        report += "INTERPRETATION:\n"
        if result.oee >= 85:
            report += "  ✓ Exzellente Anlageneffektivität (World Class)!\n"
        elif result.oee >= 60:
            report += "  ✓ Gute Anlageneffektivität.\n"
        elif result.oee >= 40:
            report += "  ⚠ Durchschnittliche Effektivität - Optimierungspotenzial vorhanden.\n"
        else:
            report += "  ✗ Niedrige Effektivität - dringende Verbesserungsmaßnahmen erforderlich!\n"

        # Empfehlungen
        report += "\nVERBESSERUNGSPOTENZIAL:\n"

        # Größter Verlust identifizieren
        losses = [
            (result.availability_loss, "Verfügbarkeit", "Reduzierung von Stillständen"),
            (result.performance_loss, "Leistung", "Optimierung der Zykluszeiten"),
            (result.quality_loss, "Qualität", "Verbesserung der Qualitätssicherung")
        ]
        losses.sort(reverse=True)

        report += f"  1. Priorität: {losses[0][1]} ({losses[0][0]:.1f}% Verlust)\n"
        report += f"     → {losses[0][2]}\n"
        report += f"  2. Priorität: {losses[1][1]} ({losses[1][0]:.1f}% Verlust)\n"
        report += f"     → {losses[1][2]}\n"

        return report

    @staticmethod
    def calculate_six_big_losses(result: OEEResult) -> Dict[str, float]:
        """
        Berechnet die 6 großen Verluste

        Returns:
            Dictionary mit den 6 Verlustarten
        """
        # Die 6 großen Verluste nach TPM (Total Productive Maintenance)
        return {
            # Verfügbarkeitsverluste
            'breakdowns': result.availability_loss * 0.6,  # Anlagenstörungen
            'setup_adjustments': result.availability_loss * 0.4,  # Rüst-/Einrichtzeit

            # Leistungsverluste
            'minor_stoppages': result.performance_loss * 0.5,  # Kleine Stopps
            'reduced_speed': result.performance_loss * 0.5,  # Reduzierte Geschwindigkeit

            # Qualitätsverluste
            'startup_rejects': result.quality_loss * 0.3,  # Anlaufverluste
            'production_rejects': result.quality_loss * 0.7  # Produktionsausschuss
        }
