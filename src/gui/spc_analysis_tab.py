"""
SPC Analysis Tab
Statistische Prozesskontrolle (SPC) Ansicht
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ..database.industrial_db_extension import IndustrialDatabaseManager
from ..analysis.spc_statistics import SPCAnalyzer


class SPCAnalysisTab(QWidget):
    """Tab für SPC-Analyse"""

    def __init__(self, db_manager: IndustrialDatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("📊 Statistische Prozesskontrolle (SPC)")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)

        # Controls
        controls_layout = QHBoxLayout()

        self.component_combo = QComboBox()
        self.component_combo.addItem("Komponente auswählen...", None)
        self.load_components()
        controls_layout.addWidget(QLabel("Komponente:"))
        controls_layout.addWidget(self.component_combo, 1)

        self.parameter_combo = QComboBox()
        self.parameter_combo.addItems([
            "Schaltzeit",
            "Druck",
            "Temperatur",
            "Zykluszeit"
        ])
        controls_layout.addWidget(QLabel("Parameter:"))
        controls_layout.addWidget(self.parameter_combo, 1)

        self.analyze_btn = QPushButton("🔍 Analysieren")
        self.analyze_btn.clicked.connect(self.perform_analysis)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        controls_layout.addWidget(self.analyze_btn)

        layout.addLayout(controls_layout)

        # Results Group
        results_group = QGroupBox("SPC-Ergebnisse")
        results_layout = QVBoxLayout()

        # Metrics Table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metrik", "Wert"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.setMaximumHeight(250)
        results_layout.addWidget(self.metrics_table)

        # Control Chart
        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        results_layout.addWidget(self.canvas)

        # Interpretation
        self.interpretation_text = QTextEdit()
        self.interpretation_text.setReadOnly(True)
        self.interpretation_text.setMaximumHeight(150)
        self.interpretation_text.setPlaceholderText("Interpretation der SPC-Analyse wird hier angezeigt...")
        results_layout.addWidget(QLabel("Interpretation:"))
        results_layout.addWidget(self.interpretation_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        self.setLayout(layout)

    def load_components(self):
        """Lädt Komponenten in Combo"""
        components = self.db.get_all_components()
        for comp in components:
            self.component_combo.addItem(
                f"{comp['designation_1']} ({comp['material_number']})",
                comp['id']
            )

    def perform_analysis(self):
        """Führt SPC-Analyse durch"""
        component_id = self.component_combo.currentData()
        if not component_id:
            return

        parameter = self.parameter_combo.currentText()

        # Messwerte abrufen
        test_runs = self.db.get_test_runs_for_component(component_id)
        if not test_runs:
            self.interpretation_text.setText("Keine Testdaten verfügbar für diese Komponente.")
            return

        # Beispiel-Daten sammeln (hier würden echte Messwerte kommen)
        values = []
        for test_run in test_runs[:50]:  # Letzte 50 Tests
            measurements = self.db.get_measurements_for_test(test_run['id'])
            if measurements:
                # Je nach Parameter unterschiedliche Werte
                if parameter == "Schaltzeit":
                    values.extend([m.get('switching_time', 0) for m in measurements if m.get('switching_time')])
                elif parameter == "Druck":
                    values.extend([m.get('pressure', 0) for m in measurements if m.get('pressure')])

        if len(values) < 10:
            self.interpretation_text.setText("Nicht genügend Messwerte für SPC-Analyse (mindestens 10 benötigt).")
            return

        # SPC-Analyse durchführen
        lsl = 0.0  # Lower Spec Limit - sollte aus Datenbank kommen
        usl = 100.0  # Upper Spec Limit - sollte aus Datenbank kommen
        target = 50.0  # Target Value - sollte aus Datenbank kommen

        spc_result = SPCAnalyzer.calculate_capability(values, lsl, usl, target)

        # Metriken anzeigen
        self.display_metrics(spc_result)

        # Regelkarte zeichnen
        self.draw_control_chart(values, spc_result)

        # Interpretation
        self.display_interpretation(spc_result)

    def display_metrics(self, spc_result):
        """Zeigt SPC-Metriken in Tabelle"""
        self.metrics_table.setRowCount(0)

        metrics = [
            ("Mittelwert (x̄)", f"{spc_result.mean:.3f}"),
            ("Standardabweichung (σ)", f"{spc_result.std_dev:.3f}"),
            ("Cp (Prozessfähigkeit)", f"{spc_result.cp:.3f}"),
            ("Cpk (Kritische Prozessfähigkeit)", f"{spc_result.cpk:.3f}"),
            ("Pp (Leistungsfähigkeit)", f"{spc_result.pp:.3f}"),
            ("Ppk (Kritische Leistungsfähigkeit)", f"{spc_result.ppk:.3f}"),
            ("Cp Bewertung", spc_result.cp_rating),
            ("Cpk Bewertung", spc_result.cpk_rating),
        ]

        for label, value in metrics:
            row = self.metrics_table.rowCount()
            self.metrics_table.insertRow(row)
            self.metrics_table.setItem(row, 0, QTableWidgetItem(label))
            self.metrics_table.setItem(row, 1, QTableWidgetItem(str(value)))

    def draw_control_chart(self, values, spc_result):
        """Zeichnet Regelkarte"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # X-Achse (Sample-Nummern)
        x = list(range(len(values)))

        # Messwerte
        ax.plot(x, values, 'bo-', label='Messwerte', markersize=4)

        # Mittelwert
        ax.axhline(y=spc_result.mean, color='g', linestyle='-', linewidth=2, label='Mittelwert')

        # Kontrollgrenzen (±3σ)
        ucl = spc_result.mean + 3 * spc_result.std_dev
        lcl = spc_result.mean - 3 * spc_result.std_dev
        ax.axhline(y=ucl, color='r', linestyle='--', label='UCL (+3σ)')
        ax.axhline(y=lcl, color='r', linestyle='--', label='LCL (-3σ)')

        # Warngrenzen (±2σ)
        uwl = spc_result.mean + 2 * spc_result.std_dev
        lwl = spc_result.mean - 2 * spc_result.std_dev
        ax.axhline(y=uwl, color='orange', linestyle=':', label='UWL (+2σ)')
        ax.axhline(y=lwl, color='orange', linestyle=':', label='LWL (-2σ)')

        ax.set_xlabel('Sample-Nummer')
        ax.set_ylabel('Wert')
        ax.set_title('Regelkarte (X-Chart)')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)

        self.canvas.draw()

    def display_interpretation(self, spc_result):
        """Zeigt Interpretation der Ergebnisse"""
        interpretation = []

        interpretation.append("=== SPC-ANALYSE INTERPRETATION ===\n")

        # Cpk Bewertung
        interpretation.append(f"Cpk-Wert: {spc_result.cpk:.3f} - {spc_result.cpk_rating}")

        if spc_result.cpk >= 1.67:
            interpretation.append("✅ Prozess ist SEHR FÄHIG. Exzellente Qualität.")
        elif spc_result.cpk >= 1.33:
            interpretation.append("✅ Prozess ist FÄHIG. Gute Qualität.")
        elif spc_result.cpk >= 1.0:
            interpretation.append("⚠ Prozess ist GERADE NOCH FÄHIG. Verbesserung empfohlen.")
        else:
            interpretation.append("❌ Prozess ist NICHT FÄHIG. Sofortige Maßnahmen erforderlich!")

        interpretation.append("")

        # Zentrierung
        if spc_result.cp > spc_result.cpk + 0.2:
            interpretation.append("⚠ Prozess ist NICHT GUT ZENTRIERT. Mittelwert sollte näher am Zielwert liegen.")
        else:
            interpretation.append("✅ Prozess ist gut zentriert.")

        interpretation.append("")

        # Streuung
        if spc_result.cp >= 1.67:
            interpretation.append("✅ Prozessstreuung ist sehr gering.")
        elif spc_result.cp >= 1.33:
            interpretation.append("✅ Prozessstreuung ist akzeptabel.")
        else:
            interpretation.append("⚠ Prozessstreuung ist zu hoch. Ursachenforschung erforderlich.")

        interpretation.append("")

        # Empfehlungen
        interpretation.append("EMPFEHLUNGEN:")
        if spc_result.cpk < 1.33:
            interpretation.append("• Ursachenanalyse durchführen (5-Why, Ishikawa)")
            interpretation.append("• Prozessparameter überprüfen")
            interpretation.append("• Schulung der Mitarbeiter")
            if spc_result.cp > spc_result.cpk + 0.2:
                interpretation.append("• Prozess-Mittelwert korrigieren (Re-Zentrierung)")

        self.interpretation_text.setText("\n".join(interpretation))
