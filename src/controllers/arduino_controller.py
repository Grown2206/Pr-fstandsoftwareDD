"""
Arduino Controller - Serial communication with Arduino for test stand control
"""
import serial
import serial.tools.list_ports
import time
import json
from typing import Optional, List, Dict, Any, Callable
from threading import Lock


class ArduinoController:
    """Manages communication with Arduino test stand hardware"""

    # Command protocol
    CMD_START_TEST = "START"
    CMD_STOP_TEST = "STOP"
    CMD_TRIGGER_CYCLE = "TRIGGER"
    CMD_READ_SENSORS = "READ"
    CMD_GET_STATUS = "STATUS"
    CMD_RESET = "RESET"

    # Response codes
    RESP_OK = "OK"
    RESP_ERROR = "ERROR"
    RESP_DATA = "DATA"
    RESP_READY = "READY"

    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.port_name = ""
        self.lock = Lock()

    @staticmethod
    def list_available_ports() -> List[str]:
        """List all available serial ports"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port: str, baudrate: int = 115200, timeout: float = 2.0) -> bool:
        """
        Connect to Arduino

        Args:
            port: Serial port name (e.g., 'COM3', '/dev/ttyUSB0')
            baudrate: Communication speed (default 115200)
            timeout: Read timeout in seconds

        Returns:
            True if connected successfully
        """
        try:
            with self.lock:
                if self.is_connected:
                    self.disconnect()

                self.serial_port = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    timeout=timeout,
                    write_timeout=timeout
                )

                # Wait for Arduino to reset
                time.sleep(2)

                # Clear any initial data
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()

                # Test connection
                response = self._send_command(self.CMD_GET_STATUS)
                if response and response.startswith(self.RESP_READY):
                    self.is_connected = True
                    self.port_name = port
                    return True
                else:
                    self.serial_port.close()
                    return False

        except serial.SerialException as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from Arduino"""
        with self.lock:
            if self.serial_port and self.serial_port.is_open:
                try:
                    self._send_command(self.CMD_STOP_TEST)
                    self.serial_port.close()
                except:
                    pass
            self.is_connected = False
            self.serial_port = None

    def _send_command(self, command: str, data: str = "") -> Optional[str]:
        """
        Send command to Arduino and wait for response

        Args:
            command: Command string
            data: Optional data payload

        Returns:
            Response string or None on error
        """
        if not self.serial_port or not self.serial_port.is_open:
            return None

        try:
            # Build message: COMMAND:DATA\n
            message = f"{command}"
            if data:
                message += f":{data}"
            message += "\n"

            # Send command
            self.serial_port.write(message.encode('utf-8'))
            self.serial_port.flush()

            # Read response (wait for newline)
            response = self.serial_port.readline().decode('utf-8').strip()
            return response

        except serial.SerialException as e:
            print(f"Communication error: {e}")
            return None

    def start_test(self) -> bool:
        """Start test on Arduino"""
        with self.lock:
            response = self._send_command(self.CMD_START_TEST)
            return response == self.RESP_OK

    def stop_test(self) -> bool:
        """Stop test on Arduino"""
        with self.lock:
            response = self._send_command(self.CMD_STOP_TEST)
            return response == self.RESP_OK

    def trigger_cycle(self) -> Optional[Dict[str, Any]]:
        """
        Trigger one test cycle and get measurement

        Returns:
            Dictionary with measurement data:
            {
                'cycle_time_ms': float,
                'temperature': float,
                'pressure': float,
                'sensor_triggered': bool,
                'success': bool,
                'error': str (if any)
            }
        """
        with self.lock:
            response = self._send_command(self.CMD_TRIGGER_CYCLE)

            if not response or not response.startswith(self.RESP_DATA):
                return None

            try:
                # Parse response: DATA:{"cycle_time":123.45,"temp":25.3,...}
                json_part = response.split(":", 1)[1]
                data = json.loads(json_part)
                return data

            except (json.JSONDecodeError, IndexError) as e:
                print(f"Parse error: {e}")
                return None

    def read_sensors(self) -> Optional[Dict[str, float]]:
        """
        Read current sensor values

        Returns:
            Dictionary with sensor readings:
            {
                'temperature': float (°C),
                'pressure': float (bar),
                'voltage': float (V)
            }
        """
        with self.lock:
            response = self._send_command(self.CMD_READ_SENSORS)

            if not response or not response.startswith(self.RESP_DATA):
                return None

            try:
                json_part = response.split(":", 1)[1]
                data = json.loads(json_part)
                return data

            except (json.JSONDecodeError, IndexError) as e:
                print(f"Parse error: {e}")
                return None

    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Get Arduino status

        Returns:
            Dictionary with status information
        """
        with self.lock:
            response = self._send_command(self.CMD_GET_STATUS)

            if not response:
                return None

            try:
                # READY:{"running":false,"cycles":0}
                if ":" in response:
                    json_part = response.split(":", 1)[1]
                    data = json.loads(json_part)
                    return data
                else:
                    return {"status": "ready", "running": False}

            except (json.JSONDecodeError, IndexError):
                return {"status": response, "running": False}

    def reset(self) -> bool:
        """Reset Arduino"""
        with self.lock:
            response = self._send_command(self.CMD_RESET)
            return response == self.RESP_OK

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


class SimulatedArduinoController(ArduinoController):
    """Simulated Arduino for testing without hardware"""

    def __init__(self):
        super().__init__()
        self.simulation_cycle_time = 100.0  # ms
        self.simulation_temp = 25.0
        self.simulation_pressure = 6.0

    def connect(self, port: str, baudrate: int = 115200, timeout: float = 2.0) -> bool:
        """Simulate connection"""
        time.sleep(0.5)  # Simulate connection delay
        self.is_connected = True
        self.port_name = port + " (Simulation)"
        return True

    def disconnect(self):
        """Simulate disconnection"""
        self.is_connected = False

    def trigger_cycle(self) -> Optional[Dict[str, Any]]:
        """Simulate cycle measurement"""
        import random

        # Simulate slight variations
        cycle_time = self.simulation_cycle_time * random.uniform(0.95, 1.05)
        temp = self.simulation_temp + random.uniform(-1, 1)
        pressure = self.simulation_pressure + random.uniform(-0.3, 0.3)

        # Simulate occasional sensor trigger delay
        sensor_triggered = random.random() > 0.02  # 98% success rate

        time.sleep(cycle_time / 1000.0)  # Simulate actual cycle time

        return {
            'cycle_time_ms': round(cycle_time, 2),
            'temperature': round(temp, 1),
            'pressure': round(pressure, 2),
            'sensor_triggered': sensor_triggered,
            'success': sensor_triggered,
            'error': '' if sensor_triggered else 'Sensor timeout'
        }

    def read_sensors(self) -> Optional[Dict[str, float]]:
        """Simulate sensor reading"""
        import random
        return {
            'temperature': round(self.simulation_temp + random.uniform(-0.5, 0.5), 1),
            'pressure': round(self.simulation_pressure + random.uniform(-0.1, 0.1), 2),
            'voltage': round(24.0 + random.uniform(-0.2, 0.2), 2)
        }

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Simulate status"""
        return {
            'status': 'ready',
            'running': False,
            'cycles': 0
        }
