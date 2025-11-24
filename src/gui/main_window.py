"""
Main Window - Modern GUI for Pneumatic Test Stand
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QHeaderView,
    QProgressBar, QTextEdit, QGroupBox, QGridLayout, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont, QColor, QPalette
import sys
from datetime import datetime

from ..database.db_manager import DatabaseManager
from ..controllers.test_controller import TestController
from ..models.component import Component, ComponentType, ComponentStatus, TestConfiguration
from ..reporting.report_generator import ReportGenerator
from ..analysis.trend_analyzer import TrendAnalyzer
from ..analysis.remaining_time_predictor import RemainingTimePredictor
from .arduino_visualization import ArduinoDashboard


class TestStandMainWindow(QMainWindow):
    """Main application window"""

    # Qt Signals for thread-safe GUI updates
    progress_signal = pyqtSignal(float, int, int)
    measurement_signal = pyqtSignal(int, float, object, object)

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.test_controller = TestController(self.db)
        self.report_generator = ReportGenerator(self.db)
        self.trend_analyzer = TrendAnalyzer(self.db)
        self.time_predictor = RemainingTimePredictor()

        # Connect signals to slots for thread-safe updates
        self.progress_signal.connect(self._update_progress_ui)
        self.measurement_signal.connect(self._update_measurement_ui)

        self.init_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_test_status)
        self.update_timer.start(1000)  # Update every second

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Pneumatik-Prüfstand Software v1.0")
        self.setGeometry(100, 100, 1400, 900)

        # Apply modern styling
        self.apply_styling()

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self.create_components_tab(), "Komponenten")
        self.tabs.addTab(self.create_test_tab(), "Test-Steuerung")
        self.tabs.addTab(self.create_reports_tab(), "Berichte")
        self.tabs.addTab(self.create_analysis_tab(), "Analyse")

        main_layout.addWidget(self.tabs)

        # Status bar
        self.statusBar().showMessage("Bereit")

    def apply_styling(self):
        """Apply modern styling to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QTabWidget::pane {
                border: 1px solid #dcdde1;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QTableWidget {
                border: 1px solid #dcdde1;
                border-radius: 5px;
                gridline-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QGroupBox {
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QGroupBox::title {
                color: #3498db;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QProgressBar {
                border: 1px solid #dcdde1;
                border-radius: 5px;
                text-align: center;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 5px;
            }
        """)

    def create_header(self):
        """Create application header"""
        header = QWidget()
        header.setStyleSheet("background-color: #2c3e50; padding: 20px;")
        layout = QHBoxLayout(header)

        title = QLabel("🔧 Pneumatik-Prüfstand Software")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # Statistics
        stats = self.db.get_statistics()
        stats_label = QLabel(
            f"Komponenten: {stats['total_components']} | "
            f"Tests: {stats['total_test_runs']} | "
            f"Zyklen: {stats['total_switching_cycles']:,}"
        )
        stats_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(stats_label)

        return header

    def create_dashboard_tab(self):
        """Create dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Welcome message
        welcome = QLabel("Willkommen beim Pneumatik-Prüfstand System")
        welcome.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; padding: 20px;")
        layout.addWidget(welcome)

        # Statistics cards
        stats_layout = QGridLayout()

        stats = self.db.get_statistics()

        # Card 1: Components
        card1 = self.create_stat_card("Komponenten gesamt", str(stats['total_components']), "#3498db")
        stats_layout.addWidget(card1, 0, 0)

        # Card 2: Test runs
        card2 = self.create_stat_card("Testläufe gesamt", str(stats['total_test_runs']), "#27ae60")
        stats_layout.addWidget(card2, 0, 1)

        # Card 3: Cycles
        card3 = self.create_stat_card("Schaltzyklen", f"{stats['total_switching_cycles']:,}", "#e74c3c")
        stats_layout.addWidget(card3, 0, 2)

        # Card 4: Hours
        card4 = self.create_stat_card("Betriebs-Stunden", f"{stats['total_hours']:.1f} h", "#f39c12")
        stats_layout.addWidget(card4, 0, 3)

        layout.addLayout(stats_layout)

        # Recent activity
        activity_group = QGroupBox("Letzte Aktivitäten")
        activity_layout = QVBoxLayout()

        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Zeit", "Komponente", "Aktion", "Details"])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.load_recent_activity()

        activity_layout.addWidget(self.activity_table)
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)

        layout.addStretch()
        return widget

    def create_stat_card(self, title: str, value: str, color: str):
        """Create a statistics card"""
        card = QGroupBox()
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: {color};
                border: none;
                border-radius: 10px;
                padding: 20px;
            }}
            QLabel {{
                color: white;
            }}
        """)

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: normal;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(value_label)

        card.setLayout(layout)
        return card

    def create_components_tab(self):
        """Create components management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar
        toolbar = QHBoxLayout()
        btn_add = QPushButton("+ Neue Komponente")
        btn_add.clicked.connect(self.add_component)
        btn_edit = QPushButton("✎ Bearbeiten")
        btn_edit.clicked.connect(self.edit_component)
        btn_delete = QPushButton("🗑 Löschen")
        btn_delete.clicked.connect(self.delete_component)
        btn_refresh = QPushButton("↻ Aktualisieren")
        btn_refresh.clicked.connect(self.load_components)

        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_delete)
        toolbar.addStretch()
        toolbar.addWidget(btn_refresh)

        layout.addLayout(toolbar)

        # Components table
        self.components_table = QTableWidget()
        self.components_table.setColumnCount(8)
        self.components_table.setHorizontalHeaderLabels([
            "ID", "Bezeichnung 1", "Bezeichnung 2", "Materialnr.",
            "Typ", "Status", "Tests", "Zyklen"
        ])
        self.components_table.horizontalHeader().setStretchLastSection(True)
        self.components_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.load_components()

        layout.addWidget(self.components_table)
        return widget

    def create_test_tab(self):
        """Create test control tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Arduino connection group
        arduino_group = QGroupBox("Arduino-Verbindung")
        arduino_layout = QHBoxLayout()

        self.arduino_port_combo = QComboBox()
        self.refresh_arduino_ports()
        arduino_layout.addWidget(QLabel("Port:"))
        arduino_layout.addWidget(self.arduino_port_combo)

        self.btn_refresh_ports = QPushButton("↻")
        self.btn_refresh_ports.setMaximumWidth(40)
        self.btn_refresh_ports.clicked.connect(self.refresh_arduino_ports)
        arduino_layout.addWidget(self.btn_refresh_ports)

        self.btn_connect_arduino = QPushButton("🔌 Verbinden")
        self.btn_connect_arduino.clicked.connect(self.toggle_arduino_connection)
        arduino_layout.addWidget(self.btn_connect_arduino)

        self.arduino_status_label = QLabel("⚫ Nicht verbunden")
        self.arduino_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        arduino_layout.addWidget(self.arduino_status_label)

        arduino_layout.addStretch()
        arduino_group.setLayout(arduino_layout)
        layout.addWidget(arduino_group)

        # Test configuration
        config_group = QGroupBox("Test-Konfiguration")
        config_layout = QFormLayout()

        self.test_component_combo = QComboBox()
        self.load_component_combo()
        config_layout.addRow("Komponente:", self.test_component_combo)

        self.test_cycles_spin = QSpinBox()
        self.test_cycles_spin.setRange(100, 1000000)
        self.test_cycles_spin.setValue(10000)
        config_layout.addRow("Anzahl Zyklen:", self.test_cycles_spin)

        self.test_interval_spin = QSpinBox()
        self.test_interval_spin.setRange(10, 10000)
        self.test_interval_spin.setValue(100)
        config_layout.addRow("Intervall (ms):", self.test_interval_spin)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Control buttons
        control_layout = QHBoxLayout()
        self.btn_start_test = QPushButton("▶ Test Starten")
        self.btn_start_test.clicked.connect(self.start_test)
        self.btn_pause_test = QPushButton("⏸ Pausieren")
        self.btn_pause_test.clicked.connect(self.pause_test)
        self.btn_pause_test.setEnabled(False)
        self.btn_stop_test = QPushButton("⏹ Stoppen")
        self.btn_stop_test.clicked.connect(self.stop_test)
        self.btn_stop_test.setEnabled(False)

        control_layout.addWidget(self.btn_start_test)
        control_layout.addWidget(self.btn_pause_test)
        control_layout.addWidget(self.btn_stop_test)
        layout.addLayout(control_layout)

        # Progress
        progress_group = QGroupBox("Test-Fortschritt")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Kein Test läuft")
        self.progress_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        progress_layout.addWidget(self.progress_label)

        self.remaining_time_label = QLabel("")
        self.remaining_time_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        progress_layout.addWidget(self.remaining_time_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Live data
        live_group = QGroupBox("Live-Daten")
        live_layout = QGridLayout()

        self.live_cycle_label = QLabel("Zyklus: -")
        self.live_time_label = QLabel("Schaltzeit: -")
        self.live_temp_label = QLabel("Temperatur: -")
        self.live_pressure_label = QLabel("Druck: -")

        live_layout.addWidget(self.live_cycle_label, 0, 0)
        live_layout.addWidget(self.live_time_label, 0, 1)
        live_layout.addWidget(self.live_temp_label, 1, 0)
        live_layout.addWidget(self.live_pressure_label, 1, 1)

        live_group.setLayout(live_layout)
        layout.addWidget(live_group)

        # Arduino Pin & Chart Visualization
        visualization_group = QGroupBox("📊 Arduino Pin-Status & Live-Diagramme")
        visualization_layout = QVBoxLayout()

        self.arduino_dashboard = ArduinoDashboard()
        visualization_layout.addWidget(self.arduino_dashboard)

        visualization_group.setLayout(visualization_layout)
        layout.addWidget(visualization_group)

        layout.addStretch()
        return widget

    def create_reports_tab(self):
        """Create reports tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel("Berichte generieren für Komponenten und Tests")
        info.setStyleSheet("font-size: 16px; padding: 10px;")
        layout.addWidget(info)

        # Component report
        comp_group = QGroupBox("Komponenten-Bericht")
        comp_layout = QFormLayout()

        self.report_component_combo = QComboBox()
        self.load_component_combo_for_reports()
        comp_layout.addRow("Komponente:", self.report_component_combo)

        btn_gen_comp_report = QPushButton("📄 Bericht Erstellen")
        btn_gen_comp_report.clicked.connect(self.generate_component_report)
        comp_layout.addRow(btn_gen_comp_report)

        comp_group.setLayout(comp_layout)
        layout.addWidget(comp_group)

        # Recent reports
        reports_group = QGroupBox("Generierte Berichte")
        reports_layout = QVBoxLayout()

        self.reports_list = QTextEdit()
        self.reports_list.setReadOnly(True)
        self.reports_list.setMaximumHeight(200)
        reports_layout.addWidget(self.reports_list)

        reports_group.setLayout(reports_layout)
        layout.addWidget(reports_group)

        layout.addStretch()
        return widget

    def create_analysis_tab(self):
        """Create analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel("Trend-Analyse und Performance-Bewertung")
        info.setStyleSheet("font-size: 16px; padding: 10px;")
        layout.addWidget(info)

        # Analysis selection
        select_group = QGroupBox("Komponente Auswählen")
        select_layout = QFormLayout()

        self.analysis_component_combo = QComboBox()
        self.load_component_combo_for_analysis()
        select_layout.addRow("Komponente:", self.analysis_component_combo)

        btn_analyze = QPushButton("📊 Analysieren")
        btn_analyze.clicked.connect(self.analyze_component)
        select_layout.addRow(btn_analyze)

        select_group.setLayout(select_layout)
        layout.addWidget(select_group)

        # Analysis results
        results_group = QGroupBox("Analyse-Ergebnisse")
        results_layout = QVBoxLayout()

        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        results_layout.addWidget(self.analysis_results)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        return widget

    # ===== Component Management =====

    def load_components(self):
        """Load components into table"""
        components = self.db.get_all_components()
        self.components_table.setRowCount(len(components))

        for i, comp in enumerate(components):
            self.components_table.setItem(i, 0, QTableWidgetItem(str(comp.id)))
            self.components_table.setItem(i, 1, QTableWidgetItem(comp.designation_1))
            self.components_table.setItem(i, 2, QTableWidgetItem(comp.designation_2))
            self.components_table.setItem(i, 3, QTableWidgetItem(comp.material_number))
            self.components_table.setItem(i, 4, QTableWidgetItem(comp.component_type.value))
            self.components_table.setItem(i, 5, QTableWidgetItem(comp.status.value))
            self.components_table.setItem(i, 6, QTableWidgetItem(str(comp.total_tests)))
            self.components_table.setItem(i, 7, QTableWidgetItem(f"{comp.total_switching_cycles:,}"))

    def add_component(self):
        """Add new component"""
        dialog = ComponentDialog(self)
        if dialog.exec_():
            component = dialog.get_component()
            try:
                self.db.create_component(component)
                self.load_components()
                self.load_component_combo()
                QMessageBox.information(self, "Erfolg", "Komponente wurde hinzugefügt")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Hinzufügen: {str(e)}")

    def edit_component(self):
        """Edit selected component"""
        row = self.components_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie eine Komponente aus")
            return

        comp_id = int(self.components_table.item(row, 0).text())
        component = self.db.get_component(comp_id)

        dialog = ComponentDialog(self, component)
        if dialog.exec_():
            updated_component = dialog.get_component()
            self.db.update_component(updated_component)
            self.load_components()
            QMessageBox.information(self, "Erfolg", "Komponente wurde aktualisiert")

    def delete_component(self):
        """Delete selected component"""
        row = self.components_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie eine Komponente aus")
            return

        reply = QMessageBox.question(self, "Bestätigung",
                                      "Komponente wirklich löschen?",
                                      QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            comp_id = int(self.components_table.item(row, 0).text())
            self.db.delete_component(comp_id)
            self.load_components()
            QMessageBox.information(self, "Erfolg", "Komponente wurde gelöscht")

    # ===== Test Control =====

    def load_component_combo(self):
        """Load components into combo box"""
        self.test_component_combo.clear()
        components = self.db.get_all_components()
        for comp in components:
            self.test_component_combo.addItem(
                f"{comp.designation_1} ({comp.material_number})",
                comp.id
            )

    def start_test(self):
        """Start test"""
        print("DEBUG: start_test() called")
        if self.test_component_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie eine Komponente aus")
            return

        component_id = self.test_component_combo.currentData()
        target_cycles = self.test_cycles_spin.value()
        interval_ms = self.test_interval_spin.value()

        print(f"DEBUG: Starting test - Component ID: {component_id}, Cycles: {target_cycles}, Interval: {interval_ms}ms")

        # Create configuration
        config = TestConfiguration(
            id=None,
            name=f"Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            component_id=component_id,
            target_cycles=target_cycles,
            cycle_interval_ms=interval_ms,
            max_duration_minutes=target_cycles * interval_ms // 60000
        )

        config_id = self.db.create_test_configuration(config)
        print(f"DEBUG: Configuration created with ID: {config_id}")

        # Start test
        try:
            print("DEBUG: Calling test_controller.start_test() with callbacks...")
            print(f"DEBUG: progress_callback = {self.on_progress_update}")
            print(f"DEBUG: measurement_callback = {self.on_measurement_update}")

            self.test_controller.start_test(
                component_id,
                config_id,
                progress_callback=self.on_progress_update,
                measurement_callback=self.on_measurement_update
            )

            print("DEBUG: test_controller.start_test() returned successfully")

            self.time_predictor.start(target_cycles)

            # Diagramme für neuen Test leeren
            self.arduino_dashboard.clear_charts()

            self.btn_start_test.setEnabled(False)
            self.btn_pause_test.setEnabled(True)
            self.btn_stop_test.setEnabled(True)

            self.statusBar().showMessage("Test läuft...")
            print("DEBUG: Test started, GUI updated")

        except Exception as e:
            print(f"ERROR: Exception in start_test: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Fehler", f"Test konnte nicht gestartet werden: {str(e)}")

    def pause_test(self):
        """Pause/resume test"""
        status = self.test_controller.get_current_status()
        if status.get('paused'):
            self.test_controller.resume_test()
            self.btn_pause_test.setText("⏸ Pausieren")
            self.statusBar().showMessage("Test läuft...")
        else:
            self.test_controller.pause_test()
            self.btn_pause_test.setText("▶ Fortsetzen")
            self.statusBar().showMessage("Test pausiert")

    def stop_test(self):
        """Stop test"""
        reply = QMessageBox.question(self, "Bestätigung",
                                      "Test wirklich stoppen?",
                                      QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.test_controller.stop_test()
            self.btn_start_test.setEnabled(True)
            self.btn_pause_test.setEnabled(False)
            self.btn_stop_test.setEnabled(False)
            self.statusBar().showMessage("Test gestoppt")

    def on_progress_update(self, progress: float, completed: int, total: int):
        """Update progress display - thread-safe wrapper using Qt Signal"""
        print(f"DEBUG: on_progress_update called: {progress:.1f}%, {completed}/{total}")
        # Emit signal - Qt automatically handles thread-safety
        self.progress_signal.emit(float(progress), int(completed), int(total))

    def _update_progress_ui(self, progress: float, completed: int, total: int):
        """Actually update progress display (runs in main thread via signal/slot)"""
        print(f"DEBUG: _update_progress_ui executing: {progress:.1f}%")
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(f"Fortschritt: {completed:,} / {total:,} Zyklen ({progress:.1f}%)")

    def on_measurement_update(self, measurement):
        """Update live data display - thread-safe wrapper using Qt Signal"""
        try:
            cycle_num = int(measurement.cycle_number)
            switch_time = float(measurement.switching_time_ms)
            temp = float(measurement.temperature) if measurement.temperature else None
            press = float(measurement.pressure) if measurement.pressure else None

            print(f"DEBUG: on_measurement_update called: Cycle {cycle_num}, Time {switch_time:.2f}ms")

            # Emit signal - Qt automatically handles thread-safety
            self.measurement_signal.emit(cycle_num, switch_time, temp, press)
        except Exception as e:
            print(f"ERROR in on_measurement_update: {e}")
            import traceback
            traceback.print_exc()

    def _update_measurement_ui(self, cycle_num: int, switch_time: float, temp, press):
        """Actually update measurement display (runs in main thread via signal/slot)"""
        print(f"DEBUG: _update_measurement_ui executing: Cycle {cycle_num}")
        self.live_cycle_label.setText(f"Zyklus: {cycle_num:,}")
        self.live_time_label.setText(f"Schaltzeit: {switch_time:.2f} ms")
        if temp is not None:
            self.live_temp_label.setText(f"Temperatur: {temp:.1f} °C")
        if press is not None:
            self.live_pressure_label.setText(f"Druck: {press:.2f} bar")

        # Update time prediction
        self.time_predictor.update(switch_time)

        # Update Arduino Dashboard Visualization
        # Simuliere Ventil-Status (an während der Schaltzeit)
        valve_on = (cycle_num % 2 == 0)  # Wechselt bei jedem Zyklus
        sensor_triggered = (cycle_num % 2 == 1)  # Gegenphasig zum Ventil

        self.arduino_dashboard.update_from_measurement(
            cycle_num=cycle_num,
            switch_time=switch_time,
            temp=temp,
            press=press,
            valve_state=valve_on,
            sensor_state=sensor_triggered
        )

    def update_test_status(self):
        """Update test status (called by timer)"""
        status = self.test_controller.get_current_status()

        if status['running']:
            # Update remaining time
            prediction = self.time_predictor.predict()
            if prediction['status'] == 'ok':
                self.remaining_time_label.setText(
                    f"Verbleibend: {prediction['remaining_time_formatted']} | "
                    f"Fertig um: {prediction['estimated_completion_formatted']} | "
                    f"Konfidenz: {prediction['confidence']:.0f}%"
                )

        elif self.btn_stop_test.isEnabled():
            # Test just finished
            self.btn_start_test.setEnabled(True)
            self.btn_pause_test.setEnabled(False)
            self.btn_stop_test.setEnabled(False)
            self.statusBar().showMessage("Test abgeschlossen")
            self.remaining_time_label.setText("")

            # Show message box in next event loop iteration to avoid paint conflicts
            QTimer.singleShot(100, lambda: QMessageBox.information(
                self, "Test abgeschlossen",
                "Der Test wurde erfolgreich abgeschlossen!"
            ))

    # ===== Reports =====

    def load_component_combo_for_reports(self):
        """Load components for reports"""
        self.report_component_combo.clear()
        components = self.db.get_all_components()
        for comp in components:
            self.report_component_combo.addItem(
                f"{comp.designation_1} ({comp.material_number})",
                comp.id
            )

    def generate_component_report(self):
        """Generate component report"""
        if self.report_component_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie eine Komponente aus")
            return

        component_id = self.report_component_combo.currentData()

        try:
            report_path = self.report_generator.generate_component_report(component_id)
            self.reports_list.append(f"✓ Bericht erstellt: {report_path}")
            QMessageBox.information(self, "Erfolg",
                                    f"Bericht wurde erstellt:\n{report_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen: {str(e)}")

    # ===== Analysis =====

    def load_component_combo_for_analysis(self):
        """Load components for analysis"""
        self.analysis_component_combo.clear()
        components = self.db.get_all_components()
        for comp in components:
            self.analysis_component_combo.addItem(
                f"{comp.designation_1} ({comp.material_number})",
                comp.id
            )

    def analyze_component(self):
        """Analyze component"""
        if self.analysis_component_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie eine Komponente aus")
            return

        component_id = self.analysis_component_combo.currentData()

        try:
            analysis = self.trend_analyzer.analyze_component_trends(component_id)

            # Format results
            results = "=== TREND-ANALYSE ===\n\n"

            if analysis['status'] == 'success':
                results += f"Anzahl Testläufe: {analysis['total_test_runs']}\n\n"

                results += "SCHALTZEIT-TREND:\n"
                trend = analysis['cycle_time_trend']
                results += f"  Richtung: {trend['direction']}\n"
                results += f"  Korrelation: {trend['correlation']:.2f}\n"
                results += f"  Beschreibung: {trend['description']}\n\n"

                results += "VERSCHLEISS:\n"
                deg = analysis['degradation_rate']
                results += f"  Rate: {deg['rate_ms_per_day']:.3f} ms/Tag\n"
                results += f"  Beschreibung: {deg['description']}\n\n"

                results += "ANOMALIEN:\n"
                anom = analysis['anomalies']
                results += f"  Anzahl: {anom['count']}\n"
                results += f"  Beschreibung: {anom['description']}\n\n"

                results += "PERFORMANCE:\n"
                perf = analysis['performance_score']
                results += f"  Score: {perf['score']}/100\n"
                results += f"  Bewertung: {perf['rating']}\n\n"

                results += "PROGNOSE:\n"
                pred = analysis['predictions']
                results += f"  Geschätzte Restzyklen: {pred['estimated_failure_cycles']:,}\n"
                results += f"  Beschreibung: {pred['description']}\n"
            else:
                results += f"Status: {analysis.get('message', 'Keine Daten')}\n"

            self.analysis_results.setText(results)

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Analyse: {str(e)}")

    # ===== Arduino Connection =====

    def refresh_arduino_ports(self):
        """Refresh list of available Arduino ports"""
        from ..controllers.arduino_controller import ArduinoController

        self.arduino_port_combo.clear()
        ports = ArduinoController.list_available_ports()

        if ports:
            for port in ports:
                self.arduino_port_combo.addItem(port)
        else:
            self.arduino_port_combo.addItem("Keine Ports gefunden")

    def toggle_arduino_connection(self):
        """Connect or disconnect Arduino"""
        if self.test_controller.is_arduino_connected():
            # Disconnect
            self.test_controller.disconnect_arduino()
            self.btn_connect_arduino.setText("🔌 Verbinden")
            self.arduino_status_label.setText("⚫ Nicht verbunden")
            self.arduino_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.statusBar().showMessage("Arduino getrennt")

        else:
            # Connect
            port = self.arduino_port_combo.currentText()

            if port == "Keine Ports gefunden":
                QMessageBox.warning(self, "Warnung",
                                    "Kein Arduino-Port verfügbar.\n\n"
                                    "Bitte verbinden Sie den Arduino und klicken Sie auf '↻'.")
                return

            try:
                if self.test_controller.connect_arduino(port):
                    self.btn_connect_arduino.setText("🔌 Trennen")
                    self.arduino_status_label.setText("🟢 Verbunden")
                    self.arduino_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                    self.statusBar().showMessage(f"Arduino verbunden auf {port}")
                    QMessageBox.information(self, "Erfolg",
                                            f"Erfolgreich mit Arduino verbunden!\nPort: {port}")
                else:
                    QMessageBox.critical(self, "Fehler",
                                        f"Verbindung zu {port} fehlgeschlagen.\n\n"
                                        "Bitte überprüfen Sie:\n"
                                        "- Arduino ist angeschlossen\n"
                                        "- Richtiger Port ausgewählt\n"
                                        "- Arduino-Sketch ist hochgeladen")

            except Exception as e:
                QMessageBox.critical(self, "Fehler",
                                    f"Verbindungsfehler: {str(e)}")

    # ===== Recent Activity =====

    def load_recent_activity(self):
        """Load recent activity"""
        test_runs = []
        components = self.db.get_all_components()
        for comp in components[:5]:  # Last 5 components
            runs = self.db.get_test_runs_for_component(comp.id)
            for run in runs[:2]:  # Last 2 runs per component
                test_runs.append((comp, run))

        test_runs.sort(key=lambda x: x[1].start_time, reverse=True)
        test_runs = test_runs[:10]  # Keep only 10 most recent

        self.activity_table.setRowCount(len(test_runs))

        for i, (comp, run) in enumerate(test_runs):
            self.activity_table.setItem(i, 0, QTableWidgetItem(
                run.start_time.strftime("%d.%m.%Y %H:%M")
            ))
            self.activity_table.setItem(i, 1, QTableWidgetItem(comp.designation_1))
            self.activity_table.setItem(i, 2, QTableWidgetItem("Test"))
            self.activity_table.setItem(i, 3, QTableWidgetItem(
                f"{run.completed_cycles:,} Zyklen, Status: {run.status}"
            ))


class ComponentDialog(QDialog):
    """Dialog for adding/editing components"""

    def __init__(self, parent=None, component: Component = None):
        super().__init__(parent)
        self.component = component
        self.setWindowTitle("Komponente" if component is None else "Komponente bearbeiten")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        """Initialize dialog UI"""
        layout = QFormLayout(self)

        self.designation1_edit = QLineEdit()
        self.designation2_edit = QLineEdit()
        self.material_edit = QLineEdit()
        self.manufacturer_edit = QLineEdit()

        self.type_combo = QComboBox()
        for ctype in ComponentType:
            self.type_combo.addItem(ctype.value, ctype)

        self.status_combo = QComboBox()
        for status in ComponentStatus:
            self.status_combo.addItem(status.value, status)

        # Fill in existing data if editing
        if self.component:
            self.designation1_edit.setText(self.component.designation_1)
            self.designation2_edit.setText(self.component.designation_2)
            self.material_edit.setText(self.component.material_number)
            self.manufacturer_edit.setText(self.component.manufacturer_number)
            self.type_combo.setCurrentText(self.component.component_type.value)
            self.status_combo.setCurrentText(self.component.status.value)

        layout.addRow("Bezeichnung 1:", self.designation1_edit)
        layout.addRow("Bezeichnung 2:", self.designation2_edit)
        layout.addRow("Materialnummer:", self.material_edit)
        layout.addRow("Herstellernummer:", self.manufacturer_edit)
        layout.addRow("Typ:", self.type_combo)
        layout.addRow("Status:", self.status_combo)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Speichern")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)

    def get_component(self) -> Component:
        """Get component from dialog"""
        return Component(
            id=self.component.id if self.component else None,
            designation_1=self.designation1_edit.text(),
            designation_2=self.designation2_edit.text(),
            material_number=self.material_edit.text(),
            manufacturer_number=self.manufacturer_edit.text(),
            component_type=self.type_combo.currentData(),
            status=self.status_combo.currentData(),
            total_tests=self.component.total_tests if self.component else 0,
            total_switching_cycles=self.component.total_switching_cycles if self.component else 0,
            total_hours=self.component.total_hours if self.component else 0.0,
            total_minutes=self.component.total_minutes if self.component else 0.0
        )
