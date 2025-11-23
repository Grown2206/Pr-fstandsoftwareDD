"""
Component data models
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class ComponentType(Enum):
    """Types of pneumatic components"""
    PNEUMATIC_CYLINDER = "Pneumatikzylinder"
    SOLENOID_VALVE = "Magnetventil"
    INITIATOR = "Initiator"


class ComponentStatus(Enum):
    """Status of component"""
    ACTIVE = "Aktiv"
    INACTIVE = "Inaktiv"
    UNDER_TEST = "Im Test"
    FAILED = "Ausgefallen"
    MAINTENANCE = "Wartung"


@dataclass
class Component:
    """Component model"""
    id: Optional[int]
    designation_1: str
    designation_2: str
    material_number: str
    manufacturer_number: str
    component_type: ComponentType
    status: ComponentStatus
    total_tests: int = 0
    total_switching_cycles: int = 0
    total_hours: float = 0.0
    total_minutes: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def add_test_results(self, cycles: int, duration_minutes: float):
        """Add test results to component statistics"""
        self.total_tests += 1
        self.total_switching_cycles += cycles
        self.total_minutes += duration_minutes
        self.total_hours = self.total_minutes / 60.0
        self.updated_at = datetime.now()


@dataclass
class TestConfiguration:
    """Test configuration model"""
    id: Optional[int]
    name: str
    component_id: int
    target_cycles: int
    cycle_interval_ms: int  # Milliseconds between cycles
    max_duration_minutes: int
    monitor_temperature: bool = True
    monitor_pressure: bool = True
    alert_threshold_temperature: float = 80.0  # °C
    alert_threshold_pressure: float = 10.0  # bar
    created_at: Optional[datetime] = None


@dataclass
class TestRun:
    """Test run model"""
    id: Optional[int]
    component_id: int
    config_id: int
    start_time: datetime
    end_time: Optional[datetime]
    completed_cycles: int
    target_cycles: int
    status: str  # "Running", "Completed", "Aborted", "Failed"
    average_cycle_time_ms: float
    min_cycle_time_ms: float
    max_cycle_time_ms: float
    temperature_readings: str  # JSON string
    pressure_readings: str  # JSON string
    errors: str = ""  # JSON string of errors
    notes: str = ""


@dataclass
class TestMeasurement:
    """Individual measurement during test"""
    id: Optional[int]
    test_run_id: int
    timestamp: datetime
    cycle_number: int
    switching_time_ms: float
    temperature: Optional[float]
    pressure: Optional[float]
    successful: bool
    error_message: Optional[str] = None
