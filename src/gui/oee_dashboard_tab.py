"""
OEE Dashboard Tab
Overall Equipment Effectiveness Übersicht
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QDateEdit, QProgressBar
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ..database.industrial_db_extension import IndustrialDatabaseManager
from ..analysis.oee_calculator import OEECalculator


class OEEDashboardTab(QWidget):
    """Tab für OEE-Dashboard"""

    def __init__(self, db_manager: IndustrialDatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("📈 OEE Dashboard (Overall Equipment Effectiveness)")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)

        # Input Group
        input_group = QGroupBox("OEE-Berechnung")
        input_layout = QFormLayout()

        self.planned_time_input = QLineEdit()
        self.planned_time_input.setPlaceholderText("Minuten")
        self.planned_time_input.setText("480")  # 8h default
        input_layout.addRow("Geplante Produktionszeit:", self.planned_time_input)

        self.downtime_input = QLineEdit()
        self.downtime_input.setPlaceholderText("Minuten")
        self.downtime_input.setText("30")
        input_layout.addRow("Stillstandszeit:", self.downtime_input)

        self.cycle_time_input = QLineEdit()
        self.cycle_time_input.setPlaceholderText("Sekunden")
        self.cycle_time_input.setText("10")
        input_layout.addRow("Ideale Zykluszeit:", self.cycle_time_input)

        self.total_pieces_input = QLineEdit()
        self.total_pieces_input.setPlaceholderText("Anzahl")
        self.total_pieces_input.setText("2500")
        input_layout.addRow("Produzierte Teile gesamt:", self.total_pieces_input)

        self.good_pieces_input = QLineEdit()
        self.good_pieces_input.setPlaceholderText("Anzahl")
        self.good_pieces_input.setText("2400")
        input_layout.addRow("Gutteile:", self.good_pieces_input)

        self.calculate_btn = QPushButton("🔍 OEE Berechnen")
        self.calculate_btn.clicked.connect(self.calculate_oee)
        self.calculate_btn.setStyleSheet("""
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
        input_layout.addRow("", self.calculate_btn)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # OEE Metrics
        metrics_layout = QHBoxLayout()

        # Verfügbarkeit
        avail_group = QGroupBox("⏱ Verfügbarkeit")
        avail_layout = QVBoxLayout()
        self.avail_value = QLabel("0.0%")
        self.avail_value.setFont(QFont("Arial", 24, QFont.Bold))
        self.avail_value.setAlignment(Qt.AlignCenter)
        self.avail_value.setStyleSheet("color: #3498db;")
        avail_layout.addWidget(self.avail_value)
        self.avail_bar = QProgressBar()
        self.avail_bar.setRange(0, 100)
        avail_layout.addWidget(self.avail_bar)
        avail_group.setLayout(avail_layout)
        metrics_layout.addWidget(avail_group)

        # Leistung
        perf_group = QGroupBox("⚡ Leistung")
        perf_layout = QVBoxLayout()
        self.perf_value = QLabel("0.0%")
        self.perf_value.setFont(QFont("Arial", 24, QFont.Bold))
        self.perf_value.setAlignment(Qt.AlignCenter)
        self.perf_value.setStyleSheet("color: #f39c12;")
        perf_layout.addWidget(self.perf_value)
        self.perf_bar = QProgressBar()
        self.perf_bar.setRange(0, 100)
        perf_layout.addWidget(self.perf_bar)
        perf_group.setLayout(perf_layout)
        metrics_layout.addWidget(perf_group)

        # Qualität
        qual_group = QGroupBox("✅ Qualität")
        qual_layout = QVBoxLayout()
        self.qual_value = QLabel("0.0%")
        self.qual_value.setFont(QFont("Arial", 24, QFont.Bold))
        self.qual_value.setAlignment(Qt.AlignCenter)
        self.qual_value.setStyleSheet("color: #27ae60;")
        qual_layout.addWidget(self.qual_value)
        self.qual_bar = QProgressBar()
        self.qual_bar.setRange(0, 100)
        qual_layout.addWidget(self.qual_bar)
        qual_group.setLayout(qual_layout)
        metrics_layout.addWidget(qual_group)

        # OEE Gesamt
        oee_group = QGroupBox("🎯 OEE Gesamt")
        oee_layout = QVBoxLayout()
        self.oee_value = QLabel("0.0%")
        self.oee_value.setFont(QFont("Arial", 32, QFont.Bold))
        self.oee_value.setAlignment(Qt.AlignCenter)
        self.oee_value.setStyleSheet("color: #e74c3c;")
        oee_layout.addWidget(self.oee_value)
        self.oee_bar = QProgressBar()
        self.oee_bar.setRange(0, 100)
        oee_layout.addWidget(self.oee_bar)
        self.oee_rating = QLabel("Nicht berechnet")
        self.oee_rating.setAlignment(Qt.AlignCenter)
        self.oee_rating.setFont(QFont("Arial", 12))
        oee_layout.addWidget(self.oee_rating)
        oee_group.setLayout(oee_layout)
        metrics_layout.addWidget(oee_group)

        layout.addLayout(metrics_layout)

        # Six Big Losses Chart
        losses_group = QGroupBox("📊 Six Big Losses (Sechs große Verluste)")
        losses_layout = QVBoxLayout()

        self.losses_figure = Figure(figsize=(10, 4))
        self.losses_canvas = FigureCanvas(self.losses_figure)
        losses_layout.addWidget(self.losses_canvas)

        losses_group.setLayout(losses_layout)
        layout.addWidget(losses_group)

        # Report
        report_group = QGroupBox("📄 OEE-Bericht")
        report_layout = QVBoxLayout()

        from PyQt5.QtWidgets import QTextEdit
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setPlaceholderText("OEE-Bericht wird hier angezeigt...")
        report_layout.addWidget(self.report_text)

        report_group.setLayout(report_layout)
        layout.addWidget(report_group)

        self.setLayout(layout)

    def calculate_oee(self):
        """Berechnet OEE"""
        try:
            planned_time = float(self.planned_time_input.text())
            downtime = float(self.downtime_input.text())
            cycle_time = float(self.cycle_time_input.text())
            total_pieces = int(self.total_pieces_input.text())
            good_pieces = int(self.good_pieces_input.text())

            # OEE berechnen
            oee_result = OEECalculator.calculate_oee(
                planned_time,
                downtime,
                cycle_time,
                total_pieces,
                good_pieces
            )

            # Metriken anzeigen
            self.update_metrics(oee_result)

            # Six Big Losses Chart
            self.draw_losses_chart(oee_result)

            # Bericht
            self.display_report(oee_result)

        except ValueError:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Fehler", "Bitte gültige Zahlen eingeben!")

    def update_metrics(self, oee_result):
        """Aktualisiert OEE-Metriken"""
        # Verfügbarkeit
        avail_percent = oee_result.availability * 100
        self.avail_value.setText(f"{avail_percent:.1f}%")
        self.avail_bar.setValue(int(avail_percent))

        # Leistung
        perf_percent = oee_result.performance * 100
        self.perf_value.setText(f"{perf_percent:.1f}%")
        self.perf_bar.setValue(int(perf_percent))

        # Qualität
        qual_percent = oee_result.quality * 100
        self.qual_value.setText(f"{qual_percent:.1f}%")
        self.qual_bar.setValue(int(qual_percent))

        # OEE Gesamt
        oee_percent = oee_result.oee * 100
        self.oee_value.setText(f"{oee_percent:.1f}%")
        self.oee_bar.setValue(int(oee_percent))
        self.oee_rating.setText(oee_result.rating)

        # Farbe basierend auf Rating
        if oee_result.is_world_class:
            self.oee_value.setStyleSheet("color: #27ae60;")  # Grün
        elif oee_percent >= 60:
            self.oee_value.setStyleSheet("color: #f39c12;")  # Orange
        else:
            self.oee_value.setStyleSheet("color: #e74c3c;")  # Rot

    def draw_losses_chart(self, oee_result):
        """Zeichnet Six Big Losses Diagramm"""
        self.losses_figure.clear()
        ax = self.losses_figure.add_subplot(111)

        losses = oee_result.six_big_losses
        categories = list(losses.keys())
        values = [losses[cat] * 100 for cat in categories]  # In Prozent

        # Deutsche Beschriftungen
        labels_de = {
            'breakdowns': 'Ausfälle\n& Störungen',
            'setup': 'Rüst- &\nEinricht-\nzeiten',
            'small_stops': 'Kleinere\nStillstände',
            'reduced_speed': 'Reduzierte\nGeschwindig-\nkeit',
            'startup_rejects': 'Anlauf-\nAusschuss',
            'production_rejects': 'Produktions-\nAusschuss'
        }

        labels = [labels_de.get(cat, cat) for cat in categories]

        colors = ['#e74c3c', '#e67e22', '#f39c12', '#f1c40f', '#3498db', '#9b59b6']

        bars = ax.bar(labels, values, color=colors, alpha=0.7, edgecolor='black')

        # Werte auf Balken schreiben
        for i, (bar, value) in enumerate(zip(bars, values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f}%',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')

        ax.set_ylabel('Verlust (%)', fontweight='bold')
        ax.set_title('Six Big Losses - Verteilung der Verluste', fontweight='bold', fontsize=12)
        ax.set_ylim(0, max(values) * 1.2 if values else 100)
        ax.grid(axis='y', alpha=0.3)

        # X-Achsen-Labels lesbar machen
        ax.tick_params(axis='x', labelsize=8)

        self.losses_figure.tight_layout()
        self.losses_canvas.draw()

    def display_report(self, oee_result):
        """Zeigt OEE-Bericht"""
        report = OEECalculator.generate_report(oee_result)
        self.report_text.setText(report)
