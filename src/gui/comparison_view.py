"""
Comparison View - Vergleich mehrerer Komponenten und Testläufe
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QDateEdit, QCheckBox, QSplitter, QListWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any


class ComparisonCanvas(FigureCanvasQTAgg):
    """Matplotlib Canvas für Vergleichsdiagramme"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8))
        super().__init__(self.figure)
        self.setParent(parent)

    def clear_figure(self):
        """Alle Subplots löschen"""
        self.figure.clear()
        self.draw()


class ComparisonView(QWidget):
    """Widget für Komponenten- und Test-Vergleich"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.selected_components = []
        self.comparison_data = {}
        self.init_ui()

    def init_ui(self):
        """UI initialisieren"""
        main_layout = QVBoxLayout()

        # Header
        header_label = QLabel("📊 Komponenten & Test-Vergleich")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        main_layout.addWidget(header_label)

        # Splitter für Auswahl und Anzeige
        splitter = QSplitter(Qt.Horizontal)

        # Linke Seite: Auswahl-Panel
        selection_panel = self.create_selection_panel()
        splitter.addWidget(selection_panel)

        # Rechte Seite: Vergleichsdiagramme
        comparison_panel = self.create_comparison_panel()
        splitter.addWidget(comparison_panel)

        splitter.setStretchFactor(0, 1)  # Selection Panel
        splitter.setStretchFactor(1, 3)  # Comparison Panel

        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    def create_selection_panel(self) -> QWidget:
        """Auswahl-Panel erstellen"""
        panel = QWidget()
        layout = QVBoxLayout()

        # Komponenten-Auswahl
        components_group = QGroupBox("🔧 Komponenten auswählen")
        components_layout = QVBoxLayout()

        # Multi-Select Liste
        self.component_list = QListWidget()
        self.component_list.setSelectionMode(QAbstractItemView.MultiSelection)
        components_layout.addWidget(self.component_list)

        # Alle auswählen/abwählen
        select_buttons = QHBoxLayout()
        btn_select_all = QPushButton("Alle")
        btn_select_all.clicked.connect(self.select_all_components)
        btn_deselect_all = QPushButton("Keine")
        btn_deselect_all.clicked.connect(self.deselect_all_components)
        select_buttons.addWidget(btn_select_all)
        select_buttons.addWidget(btn_deselect_all)
        components_layout.addLayout(select_buttons)

        components_group.setLayout(components_layout)
        layout.addWidget(components_group)

        # Zeitbereich
        timeframe_group = QGroupBox("📅 Zeitbereich")
        timeframe_layout = QVBoxLayout()

        # Von-Datum
        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel("Von:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        from_layout.addWidget(self.date_from)
        timeframe_layout.addLayout(from_layout)

        # Bis-Datum
        to_layout = QHBoxLayout()
        to_layout.addWidget(QLabel("Bis:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        to_layout.addWidget(self.date_to)
        timeframe_layout.addLayout(to_layout)

        # Schnellauswahl
        quick_buttons = QVBoxLayout()
        btn_7days = QPushButton("Letzte 7 Tage")
        btn_7days.clicked.connect(lambda: self.set_timeframe(7))
        btn_30days = QPushButton("Letzte 30 Tage")
        btn_30days.clicked.connect(lambda: self.set_timeframe(30))
        btn_90days = QPushButton("Letzte 90 Tage")
        btn_90days.clicked.connect(lambda: self.set_timeframe(90))
        quick_buttons.addWidget(btn_7days)
        quick_buttons.addWidget(btn_30days)
        quick_buttons.addWidget(btn_90days)
        timeframe_layout.addLayout(quick_buttons)

        timeframe_group.setLayout(timeframe_layout)
        layout.addWidget(timeframe_group)

        # Optionen
        options_group = QGroupBox("⚙️ Optionen")
        options_layout = QVBoxLayout()

        self.chk_show_outliers = QCheckBox("Ausreißer anzeigen")
        self.chk_show_outliers.setChecked(True)
        options_layout.addWidget(self.chk_show_outliers)

        self.chk_normalize = QCheckBox("Daten normalisieren")
        self.chk_normalize.setChecked(False)
        options_layout.addWidget(self.chk_normalize)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Vergleich starten
        btn_compare = QPushButton("🔍 Vergleich durchführen")
        btn_compare.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_compare.clicked.connect(self.perform_comparison)
        layout.addWidget(btn_compare)

        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def create_comparison_panel(self) -> QWidget:
        """Vergleichs-Panel erstellen"""
        panel = QWidget()
        layout = QVBoxLayout()

        # Tabs für verschiedene Ansichten
        self.tabs = QTabWidget()

        # Tab 1: Overlay-Diagramm
        self.overlay_canvas = ComparisonCanvas()
        self.tabs.addTab(self.overlay_canvas, "📈 Overlay-Vergleich")

        # Tab 2: Box-Plot Vergleich
        self.boxplot_canvas = ComparisonCanvas()
        self.tabs.addTab(self.boxplot_canvas, "📊 Box-Plot Vergleich")

        # Tab 3: Trend-Vergleich
        self.trend_canvas = ComparisonCanvas()
        self.tabs.addTab(self.trend_canvas, "📉 Trend-Vergleich")

        # Tab 4: Statistik-Tabelle
        self.stats_table = QTableWidget()
        self.tabs.addTab(self.stats_table, "📋 Statistik-Tabelle")

        layout.addWidget(self.tabs)

        panel.setLayout(layout)
        return panel

    def refresh_component_list(self):
        """Komponenten-Liste aktualisieren"""
        self.component_list.clear()
        components = self.db_manager.get_all_components()

        for comp in components:
            item = QListWidgetItem(f"{comp.name} (ID: {comp.id})")
            item.setData(Qt.UserRole, comp.id)
            self.component_list.addItem(item)

    def select_all_components(self):
        """Alle Komponenten auswählen"""
        for i in range(self.component_list.count()):
            self.component_list.item(i).setSelected(True)

    def deselect_all_components(self):
        """Alle Komponenten abwählen"""
        self.component_list.clearSelection()

    def set_timeframe(self, days: int):
        """Zeitbereich setzen"""
        self.date_to.setDate(QDate.currentDate())
        self.date_from.setDate(QDate.currentDate().addDays(-days))

    def perform_comparison(self):
        """Vergleich durchführen"""
        # Ausgewählte Komponenten sammeln
        selected_items = self.component_list.selectedItems()
        if not selected_items:
            return

        self.selected_components = []
        for item in selected_items:
            comp_id = item.data(Qt.UserRole)
            self.selected_components.append(comp_id)

        # Zeitbereich
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()

        # Daten laden
        self.load_comparison_data(date_from, date_to)

        # Diagramme erstellen
        self.create_overlay_chart()
        self.create_boxplot_chart()
        self.create_trend_chart()
        self.create_statistics_table()

    def load_comparison_data(self, date_from, date_to):
        """Vergleichsdaten aus Datenbank laden"""
        self.comparison_data = {}

        for comp_id in self.selected_components:
            # Komponenten-Info
            component = self.db_manager.get_component(comp_id)
            if not component:
                continue

            # Test-Läufe im Zeitbereich
            test_runs = self.db_manager.get_test_runs_by_component(
                comp_id, date_from, date_to
            )

            if test_runs:
                # Schaltzeiten extrahieren
                cycle_times = [run['avg_cycle_time'] for run in test_runs if run['avg_cycle_time']]
                timestamps = [
                    datetime.fromisoformat(run['timestamp'])
                    for run in test_runs if run['avg_cycle_time']
                ]

                if cycle_times:
                    self.comparison_data[comp_id] = {
                        'name': component.name,
                        'cycle_times': cycle_times,
                        'timestamps': timestamps,
                        'test_runs': test_runs,
                        'stats': self.calculate_statistics(cycle_times)
                    }

    def calculate_statistics(self, data: List[float]) -> Dict[str, float]:
        """Statistiken berechnen"""
        if not data:
            return {}

        arr = np.array(data)
        return {
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'mean': float(np.mean(arr)),
            'median': float(np.median(arr)),
            'std': float(np.std(arr)),
            'q1': float(np.percentile(arr, 25)),
            'q3': float(np.percentile(arr, 75)),
            'count': len(data)
        }

    def create_overlay_chart(self):
        """Overlay-Diagramm erstellen"""
        self.overlay_canvas.clear_figure()

        if not self.comparison_data:
            return

        fig = self.overlay_canvas.figure
        ax = fig.add_subplot(111)

        colors = plt.cm.tab10(np.linspace(0, 1, len(self.comparison_data)))

        for idx, (comp_id, data) in enumerate(self.comparison_data.items()):
            cycle_times = data['cycle_times']

            if self.chk_normalize.isChecked():
                # Normalisieren auf 0-1
                min_val = min(cycle_times)
                max_val = max(cycle_times)
                if max_val > min_val:
                    cycle_times = [(x - min_val) / (max_val - min_val) for x in cycle_times]

            ax.plot(
                range(len(cycle_times)),
                cycle_times,
                label=data['name'],
                color=colors[idx],
                marker='o',
                markersize=4,
                alpha=0.7
            )

        ax.set_xlabel('Messung Nr.', fontsize=12)
        ylabel = 'Normalisierte Schaltzeit' if self.chk_normalize.isChecked() else 'Schaltzeit (ms)'
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title('Overlay-Vergleich der Komponenten', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        self.overlay_canvas.draw()

    def create_boxplot_chart(self):
        """Box-Plot Vergleich erstellen"""
        self.boxplot_canvas.clear_figure()

        if not self.comparison_data:
            return

        fig = self.boxplot_canvas.figure
        ax = fig.add_subplot(111)

        # Daten für Box-Plot vorbereiten
        data_list = []
        labels = []
        colors_list = []
        colors = plt.cm.tab10(np.linspace(0, 1, len(self.comparison_data)))

        for idx, (comp_id, data) in enumerate(self.comparison_data.items()):
            data_list.append(data['cycle_times'])
            labels.append(data['name'])
            colors_list.append(colors[idx])

        # Box-Plot erstellen
        bp = ax.boxplot(
            data_list,
            labels=labels,
            patch_artist=True,
            showmeans=True,
            showfliers=self.chk_show_outliers.isChecked()
        )

        # Farben setzen
        for patch, color in zip(bp['boxes'], colors_list):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_ylabel('Schaltzeit (ms)', fontsize=12)
        ax.set_title('Box-Plot Vergleich', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        # X-Achsen-Labels rotieren wenn viele Komponenten
        if len(labels) > 3:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        fig.tight_layout()
        self.boxplot_canvas.draw()

    def create_trend_chart(self):
        """Trend-Vergleich über Zeit erstellen"""
        self.trend_canvas.clear_figure()

        if not self.comparison_data:
            return

        fig = self.trend_canvas.figure
        ax = fig.add_subplot(111)

        colors = plt.cm.tab10(np.linspace(0, 1, len(self.comparison_data)))

        for idx, (comp_id, data) in enumerate(self.comparison_data.items()):
            timestamps = data['timestamps']
            cycle_times = data['cycle_times']

            # Nach Datum sortieren
            sorted_data = sorted(zip(timestamps, cycle_times))
            timestamps_sorted, cycle_times_sorted = zip(*sorted_data) if sorted_data else ([], [])

            ax.plot(
                timestamps_sorted,
                cycle_times_sorted,
                label=data['name'],
                color=colors[idx],
                marker='o',
                markersize=3,
                alpha=0.7
            )

            # Trend-Linie (lineare Regression)
            if len(timestamps_sorted) > 1:
                x_numeric = [(t - timestamps_sorted[0]).total_seconds() for t in timestamps_sorted]
                z = np.polyfit(x_numeric, cycle_times_sorted, 1)
                p = np.poly1d(z)
                ax.plot(
                    timestamps_sorted,
                    p(x_numeric),
                    "--",
                    color=colors[idx],
                    alpha=0.5,
                    linewidth=2
                )

        ax.set_xlabel('Zeitpunkt', fontsize=12)
        ax.set_ylabel('Schaltzeit (ms)', fontsize=12)
        ax.set_title('Trend-Vergleich über Zeit', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        # Datum-Formatierung
        fig.autofmt_xdate()

        fig.tight_layout()
        self.trend_canvas.draw()

    def create_statistics_table(self):
        """Statistik-Tabelle erstellen"""
        if not self.comparison_data:
            self.stats_table.setRowCount(0)
            self.stats_table.setColumnCount(0)
            return

        # Spalten: Komponente, Anzahl, Min, Max, Mittelwert, Median, Std.Abw, Q1, Q3
        columns = ['Komponente', 'Anzahl Tests', 'Min (ms)', 'Max (ms)',
                   'Mittelwert (ms)', 'Median (ms)', 'Std.Abw. (ms)',
                   'Q1 (ms)', 'Q3 (ms)']

        self.stats_table.setColumnCount(len(columns))
        self.stats_table.setHorizontalHeaderLabels(columns)
        self.stats_table.setRowCount(len(self.comparison_data))

        for row, (comp_id, data) in enumerate(self.comparison_data.items()):
            stats = data['stats']

            items = [
                data['name'],
                str(stats['count']),
                f"{stats['min']:.2f}",
                f"{stats['max']:.2f}",
                f"{stats['mean']:.2f}",
                f"{stats['median']:.2f}",
                f"{stats['std']:.2f}",
                f"{stats['q1']:.2f}",
                f"{stats['q3']:.2f}"
            ]

            for col, item_text in enumerate(items):
                item = QTableWidgetItem(item_text)
                item.setTextAlignment(Qt.AlignCenter)
                self.stats_table.setItem(row, col, item)

        # Spaltenbreite anpassen
        self.stats_table.resizeColumnsToContents()

        # Hervorhebung: Beste Werte (niedrigste Mittelwerte)
        if len(self.comparison_data) > 1:
            means = [data['stats']['mean'] for data in self.comparison_data.values()]
            best_idx = means.index(min(means))

            for col in range(self.stats_table.columnCount()):
                item = self.stats_table.item(best_idx, col)
                if item:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setBackground(Qt.green)
