"""
Comparison View - Vergleich mehrerer Komponenten und Testläufe
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QDateEdit, QCheckBox, QSplitter, QListWidgetItem, QAbstractItemView,
    QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
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

        # Zeige leere Diagramme und Tabelle beim Start
        self.create_overlay_chart()
        self.create_boxplot_chart()
        self.create_trend_chart()
        self.create_statistics_table()

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
            # Komponenten-Name aus designation_1 und designation_2
            comp_name = f"{comp.designation_1}"
            if comp.designation_2:
                comp_name += f" / {comp.designation_2}"
            item = QListWidgetItem(f"{comp_name} (ID: {comp.id})")
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
            QMessageBox.warning(
                self,
                "Keine Auswahl",
                "Bitte wählen Sie mindestens eine Komponente aus."
            )
            return

        self.selected_components = []
        for item in selected_items:
            comp_id = item.data(Qt.UserRole)
            self.selected_components.append(comp_id)

        # Zeitbereich
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()

        # Validierung des Zeitbereichs
        if date_from > date_to:
            QMessageBox.warning(
                self,
                "Ungültiger Zeitbereich",
                "Das Von-Datum muss vor dem Bis-Datum liegen."
            )
            return

        # Daten laden
        try:
            self.load_comparison_data(date_from, date_to)

            # Prüfen ob Daten gefunden wurden
            if not self.comparison_data:
                QMessageBox.information(
                    self,
                    "Keine Daten",
                    f"Keine Test-Daten im Zeitbereich {date_from.strftime('%d.%m.%Y')} - {date_to.strftime('%d.%m.%Y')} gefunden.\n\n"
                    "Bitte wählen Sie einen anderen Zeitbereich oder führen Sie zunächst Tests durch."
                )
                return

            # Diagramme erstellen
            self.create_overlay_chart()
            self.create_boxplot_chart()
            self.create_trend_chart()
            self.create_statistics_table()

            # Erfolgs-Nachricht
            total_tests = sum(data['stats']['count'] for data in self.comparison_data.values())
            QMessageBox.information(
                self,
                "Vergleich erfolgreich",
                f"Vergleich für {len(self.comparison_data)} Komponenten erstellt.\n"
                f"Insgesamt {total_tests} Tests analysiert."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler beim Vergleich",
                f"Ein Fehler ist aufgetreten:\n\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def load_comparison_data(self, date_from, date_to):
        """Vergleichsdaten aus Datenbank laden"""
        self.comparison_data = {}

        for comp_id in self.selected_components:
            try:
                # Komponenten-Info
                component = self.db_manager.get_component(comp_id)
                if not component:
                    print(f"WARNUNG: Komponente {comp_id} nicht gefunden")
                    continue

                # Test-Läufe im Zeitbereich
                test_runs = self.db_manager.get_test_runs_by_component(
                    comp_id, date_from, date_to
                )

                if test_runs:
                    # Schaltzeiten extrahieren (nur gültige Werte)
                    cycle_times = []
                    timestamps = []

                    for run in test_runs:
                        avg_time = run.get('avg_cycle_time')
                        timestamp = run.get('timestamp')

                        if avg_time is not None and avg_time > 0 and timestamp:
                            try:
                                cycle_times.append(float(avg_time))
                                timestamps.append(datetime.fromisoformat(timestamp))
                            except (ValueError, TypeError) as e:
                                print(f"WARNUNG: Ungültiger Wert in Test {run.get('id')}: {e}")
                                continue

                    if cycle_times:
                        # Komponenten-Name aus designation_1 und designation_2
                        comp_name = f"{component.designation_1}"
                        if component.designation_2:
                            comp_name += f" / {component.designation_2}"

                        self.comparison_data[comp_id] = {
                            'name': comp_name,
                            'cycle_times': cycle_times,
                            'timestamps': timestamps,
                            'test_runs': test_runs,
                            'stats': self.calculate_statistics(cycle_times)
                        }
                        print(f"INFO: {len(cycle_times)} Tests geladen für Komponente '{comp_name}'")
                    else:
                        print(f"INFO: Keine gültigen Test-Daten für Komponente {comp_id}")

            except Exception as e:
                print(f"FEHLER beim Laden der Daten für Komponente {comp_id}: {e}")
                import traceback
                traceback.print_exc()
                continue

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
            # Zeige Hinweis-Text
            fig = self.overlay_canvas.figure
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, 'Keine Daten zum Anzeigen\n\nBitte wählen Sie Komponenten aus und\nklicken Sie auf "Vergleich durchführen"',
                    ha='center', va='center', fontsize=14, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.overlay_canvas.draw()
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
            # Zeige Hinweis-Text
            fig = self.boxplot_canvas.figure
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, 'Keine Daten zum Anzeigen\n\nBitte wählen Sie Komponenten aus und\nklicken Sie auf "Vergleich durchführen"',
                    ha='center', va='center', fontsize=14, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.boxplot_canvas.draw()
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
            # Zeige Hinweis-Text
            fig = self.trend_canvas.figure
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, 'Keine Daten zum Anzeigen\n\nBitte wählen Sie Komponenten aus und\nklicken Sie auf "Vergleich durchführen"',
                    ha='center', va='center', fontsize=14, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.trend_canvas.draw()
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
            # Zeige Hinweis in Tabelle
            self.stats_table.setRowCount(1)
            self.stats_table.setColumnCount(1)
            self.stats_table.setHorizontalHeaderLabels([''])
            hint_item = QTableWidgetItem('Keine Daten zum Anzeigen\n\nBitte wählen Sie Komponenten aus und klicken Sie auf "Vergleich durchführen"')
            hint_item.setTextAlignment(Qt.AlignCenter)
            hint_item.setForeground(QColor('gray'))
            self.stats_table.setItem(0, 0, hint_item)
            self.stats_table.horizontalHeader().setStretchLastSection(True)
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

            # Grüne Hintergrundfarbe für beste Komponente
            green_color = QColor(144, 238, 144)  # Light green

            for col in range(self.stats_table.columnCount()):
                item = self.stats_table.item(best_idx, col)
                if item:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setBackground(green_color)
