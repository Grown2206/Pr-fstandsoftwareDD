"""
Test Controller - Manages test execution
Supports both real Arduino hardware and simulation mode
"""
import time
import random
import json
from datetime import datetime
from typing import Callable, Optional, List
from threading import Thread, Event

from ..models.component import TestRun, TestMeasurement, ComponentStatus
from ..database.db_manager import DatabaseManager
from .arduino_controller import ArduinoController, SimulatedArduinoController


class TestController:
    """Controls test execution for pneumatic components"""

    def __init__(self, db_manager: DatabaseManager, use_arduino: bool = False):
        self.db = db_manager
        self.current_test: Optional[TestRun] = None
        self.is_running = False
        self.pause_event = Event()
        self.stop_event = Event()
        self.test_thread: Optional[Thread] = None
        self.progress_callback: Optional[Callable] = None
        self.measurement_callback: Optional[Callable] = None

        # Arduino control
        self.use_arduino = use_arduino
        self.arduino: Optional[ArduinoController] = None
        if use_arduino:
            self.arduino = ArduinoController()
        else:
            self.arduino = SimulatedArduinoController()

    def connect_arduino(self, port: str) -> bool:
        """Connect to Arduino on specified port"""
        if self.arduino:
            return self.arduino.connect(port)
        return False

    def disconnect_arduino(self):
        """Disconnect from Arduino"""
        if self.arduino:
            self.arduino.disconnect()

    def is_arduino_connected(self) -> bool:
        """Check if Arduino is connected"""
        return self.arduino is not None and self.arduino.is_connected

    def start_test(self, component_id: int, config_id: int,
                   progress_callback: Optional[Callable] = None,
                   measurement_callback: Optional[Callable] = None):
        """Start a new test run"""
        if self.is_running:
            raise RuntimeError("Test is already running")

        # Get component and configuration
        component = self.db.get_component(component_id)
        configs = self.db.get_configurations_for_component(component_id)
        config = next((c for c in configs if c.id == config_id), None)

        if not component or not config:
            raise ValueError("Invalid component or configuration")

        # Update component status
        component.status = ComponentStatus.UNDER_TEST
        self.db.update_component(component)

        # Create test run
        self.current_test = TestRun(
            id=None,
            component_id=component_id,
            config_id=config_id,
            start_time=datetime.now(),
            end_time=None,
            completed_cycles=0,
            target_cycles=config.target_cycles,
            status="Running",
            average_cycle_time_ms=0.0,
            min_cycle_time_ms=999999.0,
            max_cycle_time_ms=0.0,
            temperature_readings="[]",
            pressure_readings="[]",
            errors="[]"
        )

        test_run_id = self.db.create_test_run(self.current_test)
        self.current_test.id = test_run_id

        # Set callbacks
        self.progress_callback = progress_callback
        self.measurement_callback = measurement_callback

        # Start test in separate thread
        self.is_running = True
        self.pause_event.set()
        self.stop_event.clear()
        self.test_thread = Thread(target=self._run_test, args=(config,))
        self.test_thread.start()

        return test_run_id

    def _run_test(self, config):
        """Execute the test (runs in separate thread)"""
        cycle_times = []
        temp_readings = []
        pressure_readings = []
        errors = []

        # Start Arduino test if connected
        if self.arduino and self.arduino.is_connected:
            self.arduino.start_test()

        for cycle in range(config.target_cycles):
            # Check for stop signal
            if self.stop_event.is_set():
                self.current_test.status = "Aborted"
                break

            # Check for pause signal
            self.pause_event.wait()

            # Execute cycle (either with Arduino or simulation)
            cycle_start = time.time()

            if self.arduino and self.arduino.is_connected:
                # Use Arduino for real measurement
                result = self.arduino.trigger_cycle()

                if result:
                    cycle_time = result['cycle_time_ms']
                    temperature = result['temperature']
                    pressure = result['pressure']
                    successful = result['success']
                    error_msg = result.get('error', '')
                else:
                    # Arduino communication failed
                    cycle_time = config.cycle_interval_ms
                    temperature = 0.0
                    pressure = 0.0
                    successful = False
                    error_msg = "Arduino-Kommunikationsfehler"

            else:
                # Simulation mode (original code)
                base_cycle_time = config.cycle_interval_ms
                base_temperature = 25.0 + random.uniform(-2, 2)
                base_pressure = 6.0 + random.uniform(-0.5, 0.5)

                # Simulate realistic variations
                wear_factor = 1.0 + (cycle / config.target_cycles) * 0.1  # Gradual wear
                cycle_time = base_cycle_time * wear_factor * random.uniform(0.95, 1.05)

                # Simulate temperature increase over time
                temperature = base_temperature + (cycle / 1000) * 0.5 + random.uniform(-1, 1)

                # Simulate pressure variations
                pressure = base_pressure + random.uniform(-0.3, 0.3)

                # Simulate occasional errors (1% chance)
                successful = random.random() > 0.01
                error_msg = None
                if not successful:
                    error_msg = random.choice([
                        "Schaltzeit überschritten",
                        "Druckabfall erkannt",
                        "Sensor-Timeout"
                    ])

                # Simulate timing
                elapsed = time.time() - cycle_start
                wait_time = max(0, base_cycle_time / 1000.0 - elapsed)
                time.sleep(wait_time)

            # Record error if any
            if not successful and error_msg:
                errors.append({
                    'cycle': cycle,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                })

            # Create measurement
            measurement = TestMeasurement(
                id=None,
                test_run_id=self.current_test.id,
                timestamp=datetime.now(),
                cycle_number=cycle,
                switching_time_ms=cycle_time,
                temperature=temperature,
                pressure=pressure,
                successful=successful,
                error_message=error_msg
            )

            # Save measurement
            self.db.create_measurement(measurement)

            # Update statistics
            cycle_times.append(cycle_time)
            temp_readings.append(temperature)
            pressure_readings.append(pressure)

            self.current_test.completed_cycles = cycle + 1
            self.current_test.average_cycle_time_ms = sum(cycle_times) / len(cycle_times)
            self.current_test.min_cycle_time_ms = min(cycle_times)
            self.current_test.max_cycle_time_ms = max(cycle_times)
            self.current_test.temperature_readings = json.dumps(temp_readings[-100:])  # Keep last 100
            self.current_test.pressure_readings = json.dumps(pressure_readings[-100:])
            self.current_test.errors = json.dumps(errors)

            # Update database periodically (every 100 cycles)
            if cycle % 100 == 0:
                self.db.update_test_run(self.current_test)

            # Call callbacks
            if self.measurement_callback:
                self.measurement_callback(measurement)

            if self.progress_callback:
                progress = (cycle + 1) / config.target_cycles * 100
                self.progress_callback(progress, cycle + 1, config.target_cycles)

        # Stop Arduino test
        if self.arduino and self.arduino.is_connected:
            self.arduino.stop_test()

        # Complete test
        if self.current_test.status == "Running":
            self.current_test.status = "Completed"

        self.current_test.end_time = datetime.now()
        self.db.update_test_run(self.current_test)

        # Update component statistics
        component = self.db.get_component(self.current_test.component_id)
        if component:
            duration_minutes = (self.current_test.end_time - self.current_test.start_time).total_seconds() / 60
            component.add_test_results(self.current_test.completed_cycles, duration_minutes)
            component.status = ComponentStatus.ACTIVE
            self.db.update_component(component)

        self.is_running = False

        # Final progress update
        if self.progress_callback:
            self.progress_callback(100, self.current_test.completed_cycles, config.target_cycles)

    def pause_test(self):
        """Pause the running test"""
        if self.is_running:
            self.pause_event.clear()

    def resume_test(self):
        """Resume the paused test"""
        if self.is_running:
            self.pause_event.set()

    def stop_test(self):
        """Stop the running test"""
        if self.is_running:
            self.stop_event.set()
            self.pause_event.set()  # Ensure thread is not blocked
            if self.test_thread:
                self.test_thread.join(timeout=5)

    def get_current_status(self) -> dict:
        """Get current test status"""
        if not self.current_test:
            return {'running': False}

        return {
            'running': self.is_running,
            'paused': not self.pause_event.is_set(),
            'test_run_id': self.current_test.id,
            'completed_cycles': self.current_test.completed_cycles,
            'target_cycles': self.current_test.target_cycles,
            'progress': (self.current_test.completed_cycles / self.current_test.target_cycles * 100)
                        if self.current_test.target_cycles > 0 else 0,
            'status': self.current_test.status
        }
