"""
Arduino Pin Status Visualization Widget
Visualisiert Ein- und Ausgänge des Arduino in Echtzeit
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from collections import deque
import numpy as np


class LEDIndicator(QWidget):
    """LED-Indikator für digitale Pin-Anzeige"""

    def __init__(self, label_text: str, parent=None):
        super().__init__(parent)
        self.is_on = False
        self.label_text = label_text
        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # LED Circle
        self.led_label = QLabel("●")
        self.led_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.update_color()
        layout.addWidget(self.led_label)

        # Text Label
        text_label = QLabel(self.label_text)
        text_label.setFont(QFont("Arial", 10))
        layout.addWidget(text_label)

        layout.addStretch()

    def set_state(self, is_on: bool):
        """Setzt LED-Status"""
        self.is_on = is_on
        self.update_color()

    def update_color(self):
        """Aktualisiert LED-Farbe"""
        if self.is_on:
            self.led_label.setStyleSheet("color: #27ae60;")  # Grün
        else:
            self.led_label.setStyleSheet("color: #95a5a6;")  # Grau


class AnalogGauge(QWidget):
    """Analoger Gauge für Messwerte"""

    def __init__(self, label_text: str, unit: str, min_val: float = 0, max_val: float = 100, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.unit = unit
        self.min_val = min_val
        self.max_val = max_val
        self.current_value = 0.0
        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        layout = QVBoxLayout(self)

        # Label
        label = QLabel(self.label_text)
        label.setFont(QFont("Arial", 10, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # Value Display
        self.value_label = QLabel(f"0.0 {self.unit}")
        self.value_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("color: #2c3e50; background-color: #ecf0f1; border-radius: 5px; padding: 10px;")
        layout.addWidget(self.value_label)

        # Progress Bar (visual gauge)
        from PyQt5.QtWidgets import QProgressBar
        self.gauge = QProgressBar()
        self.gauge.setRange(int(self.min_val * 10), int(self.max_val * 10))
        self.gauge.setValue(0)
        self.gauge.setTextVisible(False)
        self.gauge.setMaximumHeight(20)
        layout.addWidget(self.gauge)

    def set_value(self, value: float):
        """Setzt neuen Wert"""
        self.current_value = value
        self.value_label.setText(f"{value:.2f} {self.unit}")
        self.gauge.setValue(int(value * 10))

        # Farbcodierung basierend auf Wert
        if value < self.min_val * 1.1:
            self.gauge.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
        elif value > self.max_val * 0.9:
            self.gauge.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
        else:
            self.gauge.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")


class PinStatusWidget(QWidget):
    """Widget zur Visualisierung aller Pin-Status"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        layout = QVBoxLayout(self)

        # Digital Pins Group
        digital_group = QGroupBox("Digitale Ein-/Ausgänge")
        digital_layout = QGridLayout()

        # Ausgänge
        output_label = QLabel("Ausgänge:")
        output_label.setFont(QFont("Arial", 10, QFont.Bold))
        digital_layout.addWidget(output_label, 0, 0)

        self.valve_led = LEDIndicator("D2 - Ventil (Output)")
        digital_layout.addWidget(self.valve_led, 1, 0)

        # Eingänge
        input_label = QLabel("Eingänge:")
        input_label.setFont(QFont("Arial", 10, QFont.Bold))
        digital_layout.addWidget(input_label, 2, 0)

        self.sensor_led = LEDIndicator("D3 - Sensor (Input)")
        digital_layout.addWidget(self.sensor_led, 3, 0)

        digital_group.setLayout(digital_layout)
        layout.addWidget(digital_group)

        # Analog Values Group
        analog_group = QGroupBox("Analoge Messwerte")
        analog_layout = QGridLayout()

        self.temp_gauge = AnalogGauge("Temperatur", "°C", 0, 80)
        analog_layout.addWidget(self.temp_gauge, 0, 0)

        self.pressure_gauge = AnalogGauge("Druck", "bar", 0, 10)
        analog_layout.addWidget(self.pressure_gauge, 0, 1)

        analog_group.setLayout(analog_layout)
        layout.addWidget(analog_group)

        layout.addStretch()

    def update_valve_status(self, is_on: bool):
        """Aktualisiert Ventil-Status"""
        self.valve_led.set_state(is_on)

    def update_sensor_status(self, is_triggered: bool):
        """Aktualisiert Sensor-Status"""
        self.sensor_led.set_state(is_triggered)

    def update_temperature(self, temp: float):
        """Aktualisiert Temperatur"""
        self.temp_gauge.set_value(temp)

    def update_pressure(self, pressure: float):
        """Aktualisiert Druck"""
        self.pressure_gauge.set_value(pressure)


class LiveChartWidget(QWidget):
    """Live-Diagramm für Messwerte über Zeit"""

    def __init__(self, title: str, ylabel: str, max_points: int = 100, parent=None):
        super().__init__(parent)
        self.title = title
        self.ylabel = ylabel
        self.max_points = max_points

        # Datenpuffer
        self.time_data = deque(maxlen=max_points)
        self.value_data = deque(maxlen=max_points)
        self.time_counter = 0

        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        layout = QVBoxLayout(self)

        # Matplotlib Figure
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        # Initiales leeres Diagramm
        self.line, = self.ax.plot([], [], 'b-', linewidth=2)
        self.ax.set_title(self.title, fontweight='bold')
        self.ax.set_xlabel('Zeit (Zyklen)')
        self.ax.set_ylabel(self.ylabel)
        self.ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        layout.addWidget(self.canvas)

    def add_data_point(self, value: float):
        """Fügt neuen Datenpunkt hinzu"""
        self.time_data.append(self.time_counter)
        self.value_data.append(value)
        self.time_counter += 1

        # Diagramm aktualisieren
        self.update_plot()

    def update_plot(self):
        """Aktualisiert Diagramm"""
        if len(self.time_data) == 0:
            return

        self.line.set_data(list(self.time_data), list(self.value_data))

        # Achsen anpassen
        self.ax.relim()
        self.ax.autoscale_view()

        # Y-Achse mit kleinem Puffer
        if len(self.value_data) > 0:
            y_min = min(self.value_data)
            y_max = max(self.value_data)
            y_range = y_max - y_min
            if y_range > 0:
                self.ax.set_ylim(y_min - y_range * 0.1, y_max + y_range * 0.1)

        self.canvas.draw()

    def clear(self):
        """Löscht alle Daten"""
        self.time_data.clear()
        self.value_data.clear()
        self.time_counter = 0
        self.line.set_data([], [])
        self.canvas.draw()


class ArduinoDashboard(QWidget):
    """Komplettes Arduino-Dashboard mit Pins und Charts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        layout = QHBoxLayout(self)

        # Linke Seite: Pin Status
        self.pin_status = PinStatusWidget()
        layout.addWidget(self.pin_status, 1)

        # Rechte Seite: Live Charts
        charts_layout = QVBoxLayout()

        self.temp_chart = LiveChartWidget("Temperaturverlauf", "Temperatur (°C)", max_points=100)
        charts_layout.addWidget(self.temp_chart)

        self.pressure_chart = LiveChartWidget("Druckverlauf", "Druck (bar)", max_points=100)
        charts_layout.addWidget(self.pressure_chart)

        self.cycle_time_chart = LiveChartWidget("Schaltzeit-Verlauf", "Schaltzeit (ms)", max_points=100)
        charts_layout.addWidget(self.cycle_time_chart)

        layout.addLayout(charts_layout, 2)

    def update_from_measurement(self, cycle_num: int, switch_time: float, temp, press, valve_state: bool = False, sensor_state: bool = False):
        """Aktualisiert alle Anzeigen aus Messwerten"""
        # Pin Status
        self.pin_status.update_valve_status(valve_state)
        self.pin_status.update_sensor_status(sensor_state)

        if temp is not None:
            self.pin_status.update_temperature(temp)
            self.temp_chart.add_data_point(temp)

        if press is not None:
            self.pin_status.update_pressure(press)
            self.pressure_chart.add_data_point(press)

        if switch_time is not None:
            self.cycle_time_chart.add_data_point(switch_time)

    def clear_charts(self):
        """Löscht alle Diagramme"""
        self.temp_chart.clear()
        self.pressure_chart.clear()
        self.cycle_time_chart.clear()
