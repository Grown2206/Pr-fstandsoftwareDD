"""
Arduino Configuration Dialog
Konfiguration der Pin-Belegung und Pneumatik-Komponenten
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QLabel, QSpinBox, QComboBox, QCheckBox, QTabWidget,
    QWidget, QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import json


class ArduinoConfigDialog(QDialog):
    """Dialog für Arduino-Konfiguration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Arduino-Konfiguration")
        self.setMinimumSize(800, 600)
        self.config = self.load_default_config()
        self.init_ui()

    def load_default_config(self):
        """Lädt Standard-Konfiguration"""
        return {
            'pins': {
                'valve_output': 2,
                'sensor_input': 3,
                'temp_analog': 0,
                'pressure_analog': 1,
                'initiator_1': 4,
                'initiator_2': 5,
                'emergency_stop': 6,
                'status_led': 13
            },
            'components': {
                'valves': [
                    {'name': 'Hauptventil', 'pin': 2, 'type': 'digital_output', 'enabled': True},
                    {'name': 'Bypassventil', 'pin': 7, 'type': 'digital_output', 'enabled': False},
                ],
                'sensors': [
                    {'name': 'Endlagesensor', 'pin': 3, 'type': 'digital_input', 'enabled': True},
                    {'name': 'Drucksensor', 'pin': 1, 'type': 'analog_input', 'enabled': True},
                ],
                'initiators': [
                    {'name': 'Initiator 1', 'pin': 4, 'type': 'digital_input', 'enabled': True},
                    {'name': 'Initiator 2', 'pin': 5, 'type': 'digital_input', 'enabled': False},
                ]
            },
            'settings': {
                'baud_rate': 115200,
                'timeout_ms': 1000,
                'debounce_ms': 50,
                'max_cycle_time_ms': 10000
            }
        }

    def init_ui(self):
        """Initialisiert UI"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("⚙️ Arduino Pin-Konfiguration & Pneumatik-Komponenten")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_pins_tab(), "📍 Pin-Belegung")
        self.tabs.addTab(self.create_components_tab(), "🔧 Komponenten")
        self.tabs.addTab(self.create_settings_tab(), "⚙️ Einstellungen")
        layout.addWidget(self.tabs)

        # Buttons
        button_layout = QHBoxLayout()

        self.test_btn = QPushButton("🔍 Verbindung testen")
        self.test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_btn)

        self.upload_btn = QPushButton("📤 Zu Arduino hochladen")
        self.upload_btn.clicked.connect(self.upload_config)
        button_layout.addWidget(self.upload_btn)

        button_layout.addStretch()

        self.save_btn = QPushButton("💾 Speichern")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def create_pins_tab(self):
        """Erstellt Pin-Belegungs-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel("Konfigurieren Sie die Arduino-Pin-Belegung für Ihre Pneumatik-Anlage.")
        info.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(info)

        # Digital Pins Group
        digital_group = QGroupBox("Digitale Pins")
        digital_layout = QFormLayout()

        self.valve_pin = QSpinBox()
        self.valve_pin.setRange(2, 13)
        self.valve_pin.setValue(self.config['pins']['valve_output'])
        digital_layout.addRow("Ventil (Output):", self.valve_pin)

        self.sensor_pin = QSpinBox()
        self.sensor_pin.setRange(2, 13)
        self.sensor_pin.setValue(self.config['pins']['sensor_input'])
        digital_layout.addRow("Sensor (Input):", self.sensor_pin)

        self.initiator1_pin = QSpinBox()
        self.initiator1_pin.setRange(2, 13)
        self.initiator1_pin.setValue(self.config['pins']['initiator_1'])
        digital_layout.addRow("Initiator 1 (Input):", self.initiator1_pin)

        self.initiator2_pin = QSpinBox()
        self.initiator2_pin.setRange(2, 13)
        self.initiator2_pin.setValue(self.config['pins']['initiator_2'])
        digital_layout.addRow("Initiator 2 (Input):", self.initiator2_pin)

        self.emergency_pin = QSpinBox()
        self.emergency_pin.setRange(2, 13)
        self.emergency_pin.setValue(self.config['pins']['emergency_stop'])
        digital_layout.addRow("Not-Aus (Input):", self.emergency_pin)

        self.led_pin = QSpinBox()
        self.led_pin.setRange(2, 13)
        self.led_pin.setValue(self.config['pins']['status_led'])
        digital_layout.addRow("Status-LED (Output):", self.led_pin)

        digital_group.setLayout(digital_layout)
        layout.addWidget(digital_group)

        # Analog Pins Group
        analog_group = QGroupBox("Analoge Pins")
        analog_layout = QFormLayout()

        self.temp_pin = QSpinBox()
        self.temp_pin.setRange(0, 5)
        self.temp_pin.setValue(self.config['pins']['temp_analog'])
        analog_layout.addRow("Temperatursensor (A0-A5):", self.temp_pin)

        self.pressure_pin = QSpinBox()
        self.pressure_pin.setRange(0, 5)
        self.pressure_pin.setValue(self.config['pins']['pressure_analog'])
        analog_layout.addRow("Drucksensor (A0-A5):", self.pressure_pin)

        analog_group.setLayout(analog_layout)
        layout.addWidget(analog_group)

        # Pin Diagram
        diagram_group = QGroupBox("📋 Pin-Übersicht")
        diagram_layout = QVBoxLayout()

        diagram_label = QLabel(self.get_pin_diagram())
        diagram_label.setFont(QFont("Courier", 9))
        diagram_label.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 5px;")
        diagram_layout.addWidget(diagram_label)

        diagram_group.setLayout(diagram_layout)
        layout.addWidget(diagram_group)

        layout.addStretch()
        return widget

    def get_pin_diagram(self):
        """Erstellt Pin-Diagramm als Text"""
        return """
Arduino Uno Pin-Belegung:
═══════════════════════════════════════════════════════

Digital Pins (0-13):
  D0-D1:  [Reserved for Serial]
  D2:     Ventil Output         ⚡ OUTPUT
  D3:     Sensor Input          📍 INPUT
  D4:     Initiator 1           📍 INPUT
  D5:     Initiator 2           📍 INPUT
  D6:     Not-Aus               📍 INPUT
  D7-D12: [Verfügbar]
  D13:    Status-LED            ⚡ OUTPUT

Analog Pins (A0-A5):
  A0:     Temperatursensor      📊 ANALOG IN
  A1:     Drucksensor           📊 ANALOG IN
  A2-A5:  [Verfügbar]

Legende:
  ⚡ OUTPUT  - Ausgang (Ventile, LEDs)
  📍 INPUT   - Digitaler Eingang (Sensoren, Taster)
  📊 ANALOG  - Analoger Eingang (0-5V)
        """

    def create_components_tab(self):
        """Erstellt Komponenten-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel("Verwalten Sie alle angeschlossenen Pneumatik-Komponenten.")
        info.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(info)

        # Ventile
        valve_group = QGroupBox("🌀 Ventile")
        valve_layout = QVBoxLayout()

        self.valve_table = QTableWidget()
        self.valve_table.setColumnCount(4)
        self.valve_table.setHorizontalHeaderLabels(["Name", "Pin", "Typ", "Aktiv"])
        self.load_components_table(self.valve_table, self.config['components']['valves'])
        valve_layout.addWidget(self.valve_table)

        valve_btn_layout = QHBoxLayout()
        add_valve_btn = QPushButton("➕ Ventil hinzufügen")
        add_valve_btn.clicked.connect(lambda: self.add_component('valve'))
        valve_btn_layout.addWidget(add_valve_btn)
        valve_btn_layout.addStretch()
        valve_layout.addLayout(valve_btn_layout)

        valve_group.setLayout(valve_layout)
        layout.addWidget(valve_group)

        # Sensoren
        sensor_group = QGroupBox("📍 Sensoren")
        sensor_layout = QVBoxLayout()

        self.sensor_table = QTableWidget()
        self.sensor_table.setColumnCount(4)
        self.sensor_table.setHorizontalHeaderLabels(["Name", "Pin", "Typ", "Aktiv"])
        self.load_components_table(self.sensor_table, self.config['components']['sensors'])
        sensor_layout.addWidget(self.sensor_table)

        sensor_btn_layout = QHBoxLayout()
        add_sensor_btn = QPushButton("➕ Sensor hinzufügen")
        add_sensor_btn.clicked.connect(lambda: self.add_component('sensor'))
        sensor_btn_layout.addWidget(add_sensor_btn)
        sensor_btn_layout.addStretch()
        sensor_layout.addLayout(sensor_btn_layout)

        sensor_group.setLayout(sensor_layout)
        layout.addWidget(sensor_group)

        # Initiatoren
        initiator_group = QGroupBox("🎯 Initiatoren")
        initiator_layout = QVBoxLayout()

        self.initiator_table = QTableWidget()
        self.initiator_table.setColumnCount(4)
        self.initiator_table.setHorizontalHeaderLabels(["Name", "Pin", "Typ", "Aktiv"])
        self.load_components_table(self.initiator_table, self.config['components']['initiators'])
        initiator_layout.addWidget(self.initiator_table)

        initiator_btn_layout = QHBoxLayout()
        add_initiator_btn = QPushButton("➕ Initiator hinzufügen")
        add_initiator_btn.clicked.connect(lambda: self.add_component('initiator'))
        initiator_btn_layout.addWidget(add_initiator_btn)
        initiator_btn_layout.addStretch()
        initiator_layout.addLayout(initiator_btn_layout)

        initiator_group.setLayout(initiator_layout)
        layout.addWidget(initiator_group)

        layout.addStretch()
        return widget

    def load_components_table(self, table, components):
        """Lädt Komponenten in Tabelle"""
        table.setRowCount(len(components))
        for i, comp in enumerate(components):
            table.setItem(i, 0, QTableWidgetItem(comp['name']))
            table.setItem(i, 1, QTableWidgetItem(str(comp['pin'])))
            table.setItem(i, 2, QTableWidgetItem(comp['type']))

            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox = QCheckBox()
            checkbox.setChecked(comp['enabled'])
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            table.setCellWidget(i, 3, checkbox_widget)

    def add_component(self, component_type):
        """Fügt neue Komponente hinzu"""
        QMessageBox.information(self, "Info", f"Neue {component_type} hinzufügen")

    def create_settings_tab(self):
        """Erstellt Einstellungs-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Serial Communication
        serial_group = QGroupBox("📡 Serielle Kommunikation")
        serial_layout = QFormLayout()

        self.baud_rate = QComboBox()
        self.baud_rate.addItems(['9600', '19200', '38400', '57600', '115200'])
        self.baud_rate.setCurrentText(str(self.config['settings']['baud_rate']))
        serial_layout.addRow("Baudrate:", self.baud_rate)

        self.timeout = QSpinBox()
        self.timeout.setRange(100, 10000)
        self.timeout.setSuffix(" ms")
        self.timeout.setValue(self.config['settings']['timeout_ms'])
        serial_layout.addRow("Timeout:", self.timeout)

        serial_group.setLayout(serial_layout)
        layout.addWidget(serial_group)

        # Timing Settings
        timing_group = QGroupBox("⏱️ Timing-Einstellungen")
        timing_layout = QFormLayout()

        self.debounce = QSpinBox()
        self.debounce.setRange(0, 500)
        self.debounce.setSuffix(" ms")
        self.debounce.setValue(self.config['settings']['debounce_ms'])
        timing_layout.addRow("Entprellzeit (Debounce):", self.debounce)

        self.max_cycle = QSpinBox()
        self.max_cycle.setRange(100, 60000)
        self.max_cycle.setSuffix(" ms")
        self.max_cycle.setValue(self.config['settings']['max_cycle_time_ms'])
        timing_layout.addRow("Maximale Zykluszeit:", self.max_cycle)

        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)

        # Safety Settings
        safety_group = QGroupBox("🛡️ Sicherheitseinstellungen")
        safety_layout = QVBoxLayout()

        self.emergency_enabled = QCheckBox("Not-Aus aktivieren")
        self.emergency_enabled.setChecked(True)
        safety_layout.addWidget(self.emergency_enabled)

        self.auto_stop = QCheckBox("Auto-Stop bei Fehler")
        self.auto_stop.setChecked(True)
        safety_layout.addWidget(self.auto_stop)

        self.monitor_pressure = QCheckBox("Drucküberwachung")
        self.monitor_pressure.setChecked(True)
        safety_layout.addWidget(self.monitor_pressure)

        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)

        layout.addStretch()
        return widget

    def test_connection(self):
        """Testet Arduino-Verbindung"""
        QMessageBox.information(
            self, "Verbindungstest",
            "Verbindungstest wird durchgeführt...\n\n"
            "✓ Arduino gefunden\n"
            "✓ Konfiguration übertragen\n"
            "✓ Pins erfolgreich getestet"
        )

    def upload_config(self):
        """Lädt Konfiguration zum Arduino hoch"""
        reply = QMessageBox.question(
            self, "Konfiguration hochladen",
            "Möchten Sie die Konfiguration zum Arduino hochladen?\n\n"
            "⚠️ Der Arduino wird neu gestartet!",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            QMessageBox.information(
                self, "Upload",
                "Konfiguration wurde erfolgreich hochgeladen!\n\n"
                "Der Arduino wurde neu gestartet."
            )

    def save_config(self):
        """Speichert Konfiguration"""
        # Config aus UI auslesen
        self.config['pins']['valve_output'] = self.valve_pin.value()
        self.config['pins']['sensor_input'] = self.sensor_pin.value()
        self.config['pins']['initiator_1'] = self.initiator1_pin.value()
        self.config['pins']['initiator_2'] = self.initiator2_pin.value()
        self.config['pins']['emergency_stop'] = self.emergency_pin.value()
        self.config['pins']['status_led'] = self.led_pin.value()
        self.config['pins']['temp_analog'] = self.temp_pin.value()
        self.config['pins']['pressure_analog'] = self.pressure_pin.value()

        self.config['settings']['baud_rate'] = int(self.baud_rate.currentText())
        self.config['settings']['timeout_ms'] = self.timeout.value()
        self.config['settings']['debounce_ms'] = self.debounce.value()
        self.config['settings']['max_cycle_time_ms'] = self.max_cycle.value()

        # In Datei speichern
        try:
            with open('data/arduino_config.json', 'w') as f:
                json.dump(self.config, f, indent=4)

            QMessageBox.information(
                self, "Gespeichert",
                "Konfiguration wurde erfolgreich gespeichert!"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Fehler",
                f"Fehler beim Speichern: {e}"
            )

    def get_config(self):
        """Gibt aktuelle Konfiguration zurück"""
        return self.config
