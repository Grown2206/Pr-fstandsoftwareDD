"""
Calibration Management
Kalibrierungsmanagement für Prüfmittel
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum


class CalibrationType(Enum):
    """Kalibrierungsart"""
    INTERNAL = "Interne Kalibrierung"
    EXTERNAL = "Externe Kalibrierung (DAkkS/DKD)"
    ADJUSTMENT = "Justierung"
    VERIFICATION = "Verifizierung"


class CalibrationStatus(Enum):
    """Kalibrierungsstatus"""
    VALID = "Gültig"
    EXPIRED = "Abgelaufen"
    DUE_SOON = "Demnächst fällig"
    FAILED = "Fehlgeschlagen"
    BLOCKED = "Gesperrt"


@dataclass
class CalibrationEquipment:
    """Prüfmittel/Sensor"""
    id: Optional[int]
    equipment_id: str  # Eindeutige Prüfmittel-Nr.
    name: str
    equipment_type: str  # "Drucksensor", "Temperatursensor", etc.

    # Hersteller
    manufacturer: str
    model: str
    serial_number: str

    # Kalibrierung
    calibration_interval_days: int  # Kalibrierintervall in Tagen
    last_calibration_date: Optional[datetime]
    next_calibration_date: Optional[datetime]
    status: CalibrationStatus

    # Genauigkeit
    accuracy_class: str = ""  # z.B. "0.5%", "Klasse 1"
    measurement_range_min: float = 0.0
    measurement_range_max: float = 0.0
    unit: str = ""

    # Standort
    location: str = ""

    # Verantwortlich
    responsible_person: str = ""

    # Anmerkungen
    notes: str = ""

    # Metadaten
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_calibration_valid(self) -> bool:
        """Prüft ob Kalibrierung gültig ist"""
        if not self.next_calibration_date:
            return False
        return datetime.now() < self.next_calibration_date

    def days_until_calibration(self) -> int:
        """Tage bis zur nächsten Kalibrierung"""
        if not self.next_calibration_date:
            return -999
        delta = self.next_calibration_date - datetime.now()
        return delta.days

    def update_calibration_status(self):
        """Aktualisiert Kalibrierungsstatus"""
        days = self.days_until_calibration()

        if days < 0:
            self.status = CalibrationStatus.EXPIRED
        elif days <= 30:
            self.status = CalibrationStatus.DUE_SOON
        else:
            self.status = CalibrationStatus.VALID


@dataclass
class CalibrationRecord:
    """Kalibrierprotokoll"""
    id: Optional[int]
    equipment_id: int
    calibration_date: datetime
    calibration_type: CalibrationType

    # Durchgeführt von
    calibrated_by: str
    laboratory: str = ""  # Kalibrierlabor

    # Ergebnis
    result: str = "Bestanden"  # Bestanden, Nicht bestanden
    deviation: Optional[float] = None  # Abweichung
    uncertainty: Optional[float] = None  # Messunsicherheit

    # Zertifikat
    certificate_number: str = ""
    certificate_file: str = ""  # Pfad zur PDF

    # Nächste Kalibrierung
    next_calibration_date: Optional[datetime] = None

    # Bemerkungen
    remarks: str = ""

    # Messwerte
    measurement_points: str = ""  # JSON mit Messpunkten

    # Kosten
    cost: float = 0.0

    def __post_init__(self):
        """Berechnet nächstes Kalibrierdatum falls nicht gesetzt"""
        if not self.next_calibration_date and hasattr(self, 'interval_days'):
            self.next_calibration_date = self.calibration_date + timedelta(days=365)


@dataclass
class CalibrationReminder:
    """Kalibriererinnerung"""
    equipment_id: int
    equipment_name: str
    next_calibration_date: datetime
    days_remaining: int
    priority: str  # "Hoch", "Mittel", "Niedrig"
    notified: bool = False
    notified_at: Optional[datetime] = None
