"""
Test Program Management
Prüfprogramm-Verwaltung nach Industriestandard
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TestStepType(Enum):
    """Typ des Prüfschritts"""
    MEASUREMENT = "Messung"
    VISUAL_INSPECTION = "Sichtprüfung"
    FUNCTIONAL_TEST = "Funktionstest"
    ENDURANCE_TEST = "Dauertest"
    PRESSURE_TEST = "Drucktest"


class ComparisonOperator(Enum):
    """Vergleichsoperatoren für Grenzwerte"""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    BETWEEN = "zwischen"
    OUTSIDE = "außerhalb"


@dataclass
class TestLimit:
    """Prüfgrenze"""
    parameter_name: str
    lower_limit: Optional[float] = None  # Untere Grenze
    upper_limit: Optional[float] = None  # Obere Grenze
    target_value: Optional[float] = None  # Sollwert
    unit: str = ""

    # Warngrenzne (optional)
    lower_warning: Optional[float] = None
    upper_warning: Optional[float] = None

    def check_value(self, value: float) -> tuple[str, bool]:
        """
        Prüft ob Wert innerhalb der Grenzen liegt
        Returns: (status, is_ok)
        status: "OK", "WARNING", "NOK"
        """
        if self.lower_limit is not None and value < self.lower_limit:
            return "NOK", False

        if self.upper_limit is not None and value > self.upper_limit:
            return "NOK", False

        # Warnbereich prüfen
        if self.lower_warning is not None and value < self.lower_warning:
            return "WARNING", True

        if self.upper_warning is not None and value > self.upper_warning:
            return "WARNING", True

        return "OK", True


@dataclass
class TestStep:
    """Prüfschritt"""
    id: Optional[int]
    step_number: int
    name: str
    description: str
    step_type: TestStepType

    # Parameter
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Grenzwerte
    limits: List[TestLimit] = field(default_factory=list)

    # Prüfanweisung
    instruction: str = ""

    # Automatisch oder manuell
    is_automated: bool = True

    # Pflichtfeld
    is_mandatory: bool = True

    # Zeitvorgaben
    min_duration_seconds: Optional[int] = None
    max_duration_seconds: Optional[int] = None


@dataclass
class TestProgram:
    """Prüfprogramm/Testplan"""
    id: Optional[int]
    name: str
    version: str
    description: str

    # Zugeordneter Komponententyp
    component_type: str

    # Prüfschritte
    test_steps: List[TestStep] = field(default_factory=list)

    # Status
    is_active: bool = True
    is_approved: bool = False
    approved_by: Optional[int] = None  # User ID
    approved_at: Optional[datetime] = None

    # Metadaten
    created_by: int = 0  # User ID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Revisionskontrolle
    revision_number: int = 1
    supersedes: Optional[int] = None  # ID des vorherigen Programms

    def add_step(self, step: TestStep):
        """Fügt Prüfschritt hinzu"""
        step.step_number = len(self.test_steps) + 1
        self.test_steps.append(step)

    def get_step(self, step_number: int) -> Optional[TestStep]:
        """Holt Prüfschritt nach Nummer"""
        for step in self.test_steps:
            if step.step_number == step_number:
                return step
        return None


@dataclass
class TestProgramExecution:
    """Ausführung eines Prüfprogramms"""
    id: Optional[int]
    test_program_id: int
    test_run_id: int
    component_id: int

    # Batch/Los
    batch_number: Optional[str] = None
    serial_number: Optional[str] = None

    # Status
    status: str = "Läuft"  # Läuft, Abgeschlossen, Abgebrochen, Fehlgeschlagen

    # Gesamtergebnis
    overall_result: Optional[str] = None  # i.O., n.i.O., Nacharbeit

    # Zeiten
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Bediener
    operator_id: int = 0

    # Freigabe
    approved: bool = False
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None

    # Schrittergebnisse
    step_results: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Batch:
    """Charge/Los für Komponenten"""
    id: Optional[int]
    batch_number: str
    component_type: str

    # Menge
    quantity: int
    tested_quantity: int = 0
    passed_quantity: int = 0
    failed_quantity: int = 0

    # Status
    status: str = "Offen"  # Offen, In Prüfung, Abgeschlossen

    # Zeiten
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Lieferant
    supplier: str = ""
    supplier_batch: str = ""

    # Qualität
    quality_status: str = "Ungeklärt"  # Ungeklärt, Freigegeben, Gesperrt, Nacharbeit

    # Kommentare
    notes: str = ""
