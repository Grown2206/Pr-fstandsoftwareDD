"""
FMEA System (Failure Mode and Effects Analysis)
Fehler-Möglichkeits- und Einfluss-Analyse für Prüfstand
"""
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class FMEASeverity(Enum):
    """Bedeutung (Schwere) der Auswirkung"""
    SEHR_GERING = 1  # Keine Auswirkung
    GERING = 2  # Geringfügige Unannehmlichkeit
    MAESSIG = 3  # Unannehmlichkeit
    HOCH = 4  # Beeinträchtigung
    SEHR_HOCH = 5  # Starke Beeinträchtigung
    KRITISCH = 6  # Funktionsausfall
    SEHR_KRITISCH = 7  # Schwerer Funktionsausfall
    GEFAEHRLICH = 8  # Sicherheitsrisiko
    SEHR_GEFAEHRLICH = 9  # Hohes Sicherheitsrisiko
    KATASTROPHAL = 10  # Katastrophal


class FMEAOccurrence(Enum):
    """Auftretenswahrscheinlichkeit"""
    FAST_UNMOEGLICH = 1  # < 0.01%
    SEHR_GERING = 2  # 0.01%
    GERING = 3  # 0.1%
    MAESSIG_GERING = 4  # 0.5%
    MAESSIG = 5  # 1%
    MAESSIG_HOCH = 6  # 2%
    HOCH = 7  # 5%
    SEHR_HOCH = 8  # 10%
    AEUSSERST_HOCH = 9  # 20%
    SICHER = 10  # > 50%


class FMEADetection(Enum):
    """Entdeckungswahrscheinlichkeit"""
    FAST_SICHER = 1  # > 99%
    SEHR_HOCH = 2  # 95%
    HOCH = 3  # 90%
    MAESSIG_HOCH = 4  # 80%
    MAESSIG = 5  # 70%
    GERING = 6  # 60%
    SEHR_GERING = 7  # 40%
    AEUSSERST_GERING = 8  # 20%
    UNWAHRSCHEINLICH = 9  # 10%
    FAST_UNMOEGLICH = 10  # < 5%


class RPNPriority(Enum):
    """RPN-Priorität"""
    NIEDRIG = "Niedrig"  # RPN 1-39
    MITTEL = "Mittel"  # RPN 40-99
    HOCH = "Hoch"  # RPN 100-199
    SEHR_HOCH = "Sehr Hoch"  # RPN 200+


@dataclass
class FMEAFailureMode:
    """Fehlermodus"""
    id: Optional[int]
    component_type: str  # Zylinder, Ventil, etc.
    process_step: str  # Testphase
    failure_mode: str  # Beschreibung des Fehlers
    failure_effects: str  # Auswirkungen
    failure_causes: str  # Ursachen
    severity: int  # 1-10
    occurrence: int  # 1-10
    detection: int  # 1-10
    current_controls: str  # Aktuelle Maßnahmen
    recommended_actions: str  # Empfohlene Maßnahmen
    responsibility: str  # Verantwortlich
    target_date: Optional[datetime] = None
    action_taken: Optional[str] = None
    status: str = "Offen"  # Offen, In Arbeit, Abgeschlossen
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @property
    def rpn(self) -> int:
        """Berechnet Risiko-Prioritäts-Zahl (RPN)"""
        return self.severity * self.occurrence * self.detection

    @property
    def priority(self) -> RPNPriority:
        """Bestimmt Priorität basierend auf RPN"""
        rpn = self.rpn
        if rpn >= 200:
            return RPNPriority.SEHR_HOCH
        elif rpn >= 100:
            return RPNPriority.HOCH
        elif rpn >= 40:
            return RPNPriority.MITTEL
        else:
            return RPNPriority.NIEDRIG

    @property
    def requires_immediate_action(self) -> bool:
        """Prüft ob sofortige Maßnahme erforderlich"""
        # Severity 9-10 ODER RPN > 200
        return self.severity >= 9 or self.rpn >= 200


@dataclass
class FMEAAction:
    """FMEA Maßnahme"""
    id: Optional[int]
    failure_mode_id: int
    action_description: str
    responsibility: str
    target_date: datetime
    status: str = "Geplant"  # Geplant, In Arbeit, Abgeschlossen, Überprüft
    completion_date: Optional[datetime] = None
    effectiveness_check: Optional[str] = None
    new_severity: Optional[int] = None
    new_occurrence: Optional[int] = None
    new_detection: Optional[int] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def new_rpn(self) -> Optional[int]:
        """Berechnet neuen RPN nach Maßnahme"""
        if all([self.new_severity, self.new_occurrence, self.new_detection]):
            return self.new_severity * self.new_occurrence * self.new_detection
        return None

    @property
    def is_overdue(self) -> bool:
        """Prüft ob Termin überschritten"""
        if self.status == "Abgeschlossen":
            return False
        return datetime.now() > self.target_date


class FMEAAnalyzer:
    """FMEA Analyse-Tool"""

    @staticmethod
    def analyze_failure_modes(failure_modes: List[FMEAFailureMode]) -> Dict:
        """Analysiert Liste von Fehlermodi"""
        if not failure_modes:
            return {
                'total': 0,
                'high_priority': 0,
                'immediate_action_required': 0,
                'average_rpn': 0,
                'max_rpn': 0
            }

        total = len(failure_modes)
        high_priority = len([fm for fm in failure_modes if fm.priority in [RPNPriority.HOCH, RPNPriority.SEHR_HOCH]])
        immediate = len([fm for fm in failure_modes if fm.requires_immediate_action])
        rpns = [fm.rpn for fm in failure_modes]

        return {
            'total': total,
            'high_priority': high_priority,
            'high_priority_percent': (high_priority / total * 100) if total > 0 else 0,
            'immediate_action_required': immediate,
            'average_rpn': sum(rpns) / len(rpns) if rpns else 0,
            'max_rpn': max(rpns) if rpns else 0,
            'min_rpn': min(rpns) if rpns else 0
        }

    @staticmethod
    def get_top_risks(failure_modes: List[FMEAFailureMode], limit: int = 10) -> List[FMEAFailureMode]:
        """Gibt die Top-Risiken zurück (höchste RPN)"""
        return sorted(failure_modes, key=lambda fm: fm.rpn, reverse=True)[:limit]

    @staticmethod
    def get_pareto_analysis(failure_modes: List[FMEAFailureMode]) -> List[Dict]:
        """Pareto-Analyse: 80/20 Regel auf RPN"""
        sorted_modes = sorted(failure_modes, key=lambda fm: fm.rpn, reverse=True)
        total_rpn = sum(fm.rpn for fm in sorted_modes)

        cumulative_rpn = 0
        pareto_data = []

        for i, fm in enumerate(sorted_modes):
            cumulative_rpn += fm.rpn
            cumulative_percent = (cumulative_rpn / total_rpn * 100) if total_rpn > 0 else 0

            pareto_data.append({
                'rank': i + 1,
                'failure_mode': fm.failure_mode,
                'rpn': fm.rpn,
                'cumulative_rpn': cumulative_rpn,
                'cumulative_percent': cumulative_percent,
                'in_vital_few': cumulative_percent <= 80
            })

        return pareto_data

    @staticmethod
    def calculate_effectiveness(
        original_rpn: int,
        new_rpn: int
    ) -> Dict:
        """Berechnet Wirksamkeit einer Maßnahme"""
        reduction = original_rpn - new_rpn
        reduction_percent = (reduction / original_rpn * 100) if original_rpn > 0 else 0

        effectiveness = "Sehr wirksam" if reduction_percent > 50 else \
                       "Wirksam" if reduction_percent > 25 else \
                       "Teilweise wirksam" if reduction_percent > 10 else \
                       "Gering wirksam"

        return {
            'original_rpn': original_rpn,
            'new_rpn': new_rpn,
            'reduction': reduction,
            'reduction_percent': reduction_percent,
            'effectiveness': effectiveness
        }

    @staticmethod
    def generate_fmea_report(failure_modes: List[FMEAFailureMode]) -> str:
        """Generiert FMEA-Bericht als Text"""
        analysis = FMEAAnalyzer.analyze_failure_modes(failure_modes)
        top_risks = FMEAAnalyzer.get_top_risks(failure_modes, 5)

        report = []
        report.append("=" * 80)
        report.append("FMEA-BERICHT - Pneumatik-Prüfstand")
        report.append("=" * 80)
        report.append(f"Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        report.append("")

        report.append("ZUSAMMENFASSUNG")
        report.append("-" * 80)
        report.append(f"Gesamte Fehlermodi:           {analysis['total']}")
        report.append(f"Hohe Priorität (RPN≥100):     {analysis['high_priority']} ({analysis['high_priority_percent']:.1f}%)")
        report.append(f"Sofortmaßnahme erforderlich:  {analysis['immediate_action_required']}")
        report.append(f"Durchschnittlicher RPN:       {analysis['average_rpn']:.1f}")
        report.append(f"Maximaler RPN:                {analysis['max_rpn']}")
        report.append("")

        report.append("TOP 5 RISIKEN")
        report.append("-" * 80)
        report.append(f"{'Rang':<6} {'Fehlermodus':<30} {'S':<3} {'O':<3} {'D':<3} {'RPN':<5} {'Priorität':<12}")
        report.append("-" * 80)

        for i, fm in enumerate(top_risks, 1):
            report.append(
                f"{i:<6} {fm.failure_mode[:28]:<30} {fm.severity:<3} {fm.occurrence:<3} "
                f"{fm.detection:<3} {fm.rpn:<5} {fm.priority.value:<12}"
            )

        report.append("")
        report.append("LEGENDE")
        report.append("-" * 80)
        report.append("S = Severity (Bedeutung):       1-10 (10 = Katastrophal)")
        report.append("O = Occurrence (Auftreten):     1-10 (10 = Sehr häufig)")
        report.append("D = Detection (Entdeckung):     1-10 (10 = Kaum entdeckbar)")
        report.append("RPN = Risk Priority Number:     S × O × D")
        report.append("")
        report.append("RPN-BEWERTUNG")
        report.append("  1-39:   Niedrige Priorität")
        report.append("  40-99:  Mittlere Priorität")
        report.append("  100-199: Hohe Priorität")
        report.append("  200+:   Sehr hohe Priorität - Sofortmaßnahme erforderlich!")
        report.append("=" * 80)

        return "\n".join(report)


class FMEATemplates:
    """Vordefinierte FMEA-Templates für typische Fehler"""

    @staticmethod
    def get_cylinder_templates() -> List[FMEAFailureMode]:
        """FMEA-Templates für Zylinder"""
        return [
            FMEAFailureMode(
                id=None,
                component_type="Pneumatikzylinder",
                process_step="Funktionstest",
                failure_mode="Zylinder fährt nicht aus",
                failure_effects="Test kann nicht durchgeführt werden, Produktionsstillstand",
                failure_causes="Luftdruck zu niedrig, Ventil defekt, Mechanische Blockierung",
                severity=7,
                occurrence=3,
                detection=2,
                current_controls="Drucküberwachung, Visuelle Inspektion",
                recommended_actions="Automatische Druckprüfung vor Test, Redundante Druckversorgung",
                responsibility="Instandhaltung"
            ),
            FMEAFailureMode(
                id=None,
                component_type="Pneumatikzylinder",
                process_step="Lebensdauertest",
                failure_mode="Vorzeitiger Verschleiß der Dichtungen",
                failure_effects="Leckage, ungenaue Testergebnisse, Kontamination",
                failure_causes="Schmutz in Druckluft, zu hohe Geschwindigkeit, falsche Schmierung",
                severity=5,
                occurrence=4,
                detection=3,
                current_controls="Wartungsintervalle, Luftfilterung",
                recommended_actions="Verbesserte Luftaufbereitung, Schmierungsüberwachung",
                responsibility="Qualitätssicherung"
            ),
            FMEAFailureMode(
                id=None,
                component_type="Pneumatikzylinder",
                process_step="Zeitmessung",
                failure_mode="Sensor erkennt Endlage nicht",
                failure_effects="Falsche Schaltzeitmessung, Test-Abbruch",
                failure_causes="Sensor defekt, Verschmutzung, Falsche Montage",
                severity=6,
                occurrence=2,
                detection=2,
                current_controls="Sensor-Funktionstest vor Testbeginn",
                recommended_actions="Redundante Sensorik, Automatische Plausibilitätsprüfung",
                responsibility="Entwicklung"
            )
        ]

    @staticmethod
    def get_valve_templates() -> List[FMEAFailureMode]:
        """FMEA-Templates für Ventile"""
        return [
            FMEAFailureMode(
                id=None,
                component_type="Magnetventil",
                process_step="Schalttest",
                failure_mode="Ventil schaltet nicht",
                failure_effects="Kein Luftstrom, Test fehlgeschlagen",
                failure_causes="Spulendefekt, Mechanische Blockierung, Stromausfall",
                severity=8,
                occurrence=2,
                detection=1,
                current_controls="Elektrische Überwachung, Stromprüfung",
                recommended_actions="Spulen-Temperaturüberwachung, Ersatzventil bereithalten",
                responsibility="Elektrotechnik"
            ),
            FMEAFailureMode(
                id=None,
                component_type="Magnetventil",
                process_step="Wiederholungstest",
                failure_mode="Ventil schaltet verzögert",
                failure_effects="Verfälschte Messwerte, schlechte Reproduzierbarkeit",
                failure_causes="Verschmutzung, Magnetfeld zu schwach, Alterung",
                severity=4,
                occurrence=5,
                detection=4,
                current_controls="Schaltzeit-Monitoring",
                recommended_actions="Kalibrierung Schaltzeiten, Wartungsintervall verkürzen",
                responsibility="Instandhaltung"
            )
        ]

    @staticmethod
    def get_measurement_templates() -> List[FMEAFailureMode]:
        """FMEA-Templates für Messtechnik"""
        return [
            FMEAFailureMode(
                id=None,
                component_type="Drucksensor",
                process_step="Druckmessung",
                failure_mode="Sensor liefert falsche Werte",
                failure_effects="Ungenaue Testdaten, falsche Qualitätsbewertung",
                failure_causes="Sensor-Drift, Kalibrierung überfällig, Beschädigung",
                severity=7,
                occurrence=3,
                detection=5,
                current_controls="Kalibrierungsplan, Plausibilitätsprüfung",
                recommended_actions="Automatische Nullpunkt-Kalibrierung, Vergleichsmessung",
                responsibility="Messtechnik"
            ),
            FMEAFailureMode(
                id=None,
                component_type="Zeitmessung",
                process_step="Schaltzeitmessung",
                failure_mode="Timing-Fehler durch Softwarebug",
                failure_effects="Alle Schaltzeiten falsch gemessen",
                failure_causes="Software-Fehler, Timer-Overflow, Systemlast",
                severity=8,
                occurrence=2,
                detection=6,
                current_controls="Software-Tests, Code-Review",
                recommended_actions="Hardware-Timer verwenden, Plausibilitätsprüfung",
                responsibility="Software-Entwicklung"
            )
        ]


class FMEADatabaseExtension:
    """Datenbank-Erweiterung für FMEA"""

    @staticmethod
    def create_fmea_tables(cursor):
        """Erstellt FMEA-Tabellen"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fmea_failure_modes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_type TEXT NOT NULL,
                process_step TEXT NOT NULL,
                failure_mode TEXT NOT NULL,
                failure_effects TEXT NOT NULL,
                failure_causes TEXT NOT NULL,
                severity INTEGER NOT NULL,
                occurrence INTEGER NOT NULL,
                detection INTEGER NOT NULL,
                current_controls TEXT,
                recommended_actions TEXT,
                responsibility TEXT,
                target_date TIMESTAMP,
                action_taken TEXT,
                status TEXT DEFAULT 'Offen',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fmea_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                failure_mode_id INTEGER NOT NULL,
                action_description TEXT NOT NULL,
                responsibility TEXT NOT NULL,
                target_date TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'Geplant',
                completion_date TIMESTAMP,
                effectiveness_check TEXT,
                new_severity INTEGER,
                new_occurrence INTEGER,
                new_detection INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (failure_mode_id) REFERENCES fmea_failure_modes(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fmea_rpn
            ON fmea_failure_modes(severity, occurrence, detection)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fmea_status
            ON fmea_failure_modes(status)
        """)
