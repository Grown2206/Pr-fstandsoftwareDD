"""
Report Generator - Creates detailed HTML and PDF reports
"""
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

from ..database.db_manager import DatabaseManager
from ..analysis.trend_analyzer import TrendAnalyzer


class ReportGenerator:
    """Generates comprehensive test reports"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.analyzer = TrendAnalyzer(db_manager)
        self.output_dir = Path("data/exports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_component_report(self, component_id: int) -> str:
        """Generate comprehensive report for a component"""
        component = self.db.get_component(component_id)
        if not component:
            raise ValueError("Component not found")

        # Get analysis
        trend_analysis = self.analyzer.analyze_component_trends(component_id)
        test_runs = self.db.get_test_runs_for_component(component_id)

        # Generate plots
        plot_files = self._generate_plots(component_id, test_runs)

        # Generate HTML report
        html_content = self._generate_html_report(component, trend_analysis, test_runs, plot_files)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"report_{component.material_number}_{timestamp}.html"
        report_path = self.output_dir / report_filename

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(report_path)

    def generate_test_run_report(self, test_run_id: int) -> str:
        """Generate detailed report for a single test run"""
        test_run = self.db.get_test_run(test_run_id)
        if not test_run:
            raise ValueError("Test run not found")

        component = self.db.get_component(test_run.component_id)
        measurements = self.db.get_measurements_for_test_run(test_run_id)
        analysis = self.analyzer.analyze_test_run_details(test_run_id)

        # Generate plots
        plot_files = self._generate_test_run_plots(test_run, measurements)

        # Generate HTML
        html_content = self._generate_test_run_html(component, test_run, measurements, analysis, plot_files)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"test_run_{test_run_id}_{timestamp}.html"
        report_path = self.output_dir / report_filename

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(report_path)

    def _generate_plots(self, component_id: int, test_runs: List) -> Dict[str, str]:
        """Generate visualization plots"""
        plot_files = {}

        if not test_runs:
            return plot_files

        # Extract data
        dates = [tr.start_time for tr in test_runs if tr.average_cycle_time_ms > 0]
        cycle_times = [tr.average_cycle_time_ms for tr in test_runs if tr.average_cycle_time_ms > 0]

        if not cycle_times:
            return plot_files

        # Plot 1: Cycle time over test runs
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(range(len(cycle_times)), cycle_times, marker='o', linestyle='-', linewidth=2, markersize=6)
        ax.set_xlabel('Testlauf Nummer', fontsize=12)
        ax.set_ylabel('Durchschnittliche Schaltzeit (ms)', fontsize=12)
        ax.set_title('Schaltzeit-Entwicklung über Testläufe', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plot_path = self.output_dir / f"cycle_time_trend_{component_id}.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        plot_files['cycle_time_trend'] = str(plot_path)

        # Plot 2: Cycle distribution histogram
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(cycle_times, bins=20, edgecolor='black', alpha=0.7, color='#3498db')
        ax.set_xlabel('Schaltzeit (ms)', fontsize=12)
        ax.set_ylabel('Häufigkeit', fontsize=12)
        ax.set_title('Verteilung der Schaltzeiten', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        # Add statistical lines
        import numpy as np
        mean_val = np.mean(cycle_times)
        std_val = np.std(cycle_times)
        ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mittelwert: {mean_val:.2f} ms')
        ax.axvline(mean_val + std_val, color='orange', linestyle=':', linewidth=2, label=f'+1σ: {mean_val + std_val:.2f} ms')
        ax.axvline(mean_val - std_val, color='orange', linestyle=':', linewidth=2, label=f'-1σ: {mean_val - std_val:.2f} ms')
        ax.legend()

        plot_path = self.output_dir / f"cycle_time_dist_{component_id}.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        plot_files['cycle_time_distribution'] = str(plot_path)

        # Plot 3: Box Plot für Schaltzeiten
        fig, ax = plt.subplots(figsize=(10, 6))
        bp = ax.boxplot(cycle_times, vert=True, patch_artist=True)
        bp['boxes'][0].set_facecolor('#3498db')
        bp['boxes'][0].set_alpha(0.7)
        ax.set_ylabel('Schaltzeit (ms)', fontsize=12)
        ax.set_title('Box-Plot: Schaltzeit-Verteilung & Ausreißer', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        # Add statistics as text
        q1, median, q3 = np.percentile(cycle_times, [25, 50, 75])
        stats_text = f'Min: {min(cycle_times):.2f} ms\n'
        stats_text += f'Q1: {q1:.2f} ms\n'
        stats_text += f'Median: {median:.2f} ms\n'
        stats_text += f'Q3: {q3:.2f} ms\n'
        stats_text += f'Max: {max(cycle_times):.2f} ms\n'
        stats_text += f'Mittelwert: {mean_val:.2f} ms\n'
        stats_text += f'Std.Abw.: {std_val:.2f} ms'
        ax.text(1.15, 0.5, stats_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plot_path = self.output_dir / f"cycle_time_boxplot_{component_id}.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        plot_files['cycle_time_boxplot'] = str(plot_path)

        return plot_files

    def _generate_test_run_plots(self, test_run, measurements: List) -> Dict[str, str]:
        """Generate plots for single test run"""
        plot_files = {}

        if not measurements:
            return plot_files

        cycles = [m.cycle_number for m in measurements]
        cycle_times = [m.switching_time_ms for m in measurements]
        temperatures = [m.temperature for m in measurements if m.temperature is not None]
        pressures = [m.pressure for m in measurements if m.pressure is not None]

        # Plot 1: Cycle time progression
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(cycles, cycle_times, linewidth=1, alpha=0.7)
        ax.set_xlabel('Zyklus Nummer', fontsize=12)
        ax.set_ylabel('Schaltzeit (ms)', fontsize=12)
        ax.set_title('Schaltzeit während des Tests', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plot_path = self.output_dir / f"test_run_{test_run.id}_cycles.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        plot_files['cycle_progression'] = str(plot_path)

        # Plot 2: Temperature and Pressure (if available)
        if temperatures and pressures:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

            temp_cycles = [m.cycle_number for m in measurements if m.temperature is not None]
            ax1.plot(temp_cycles, temperatures, color='red', linewidth=1)
            ax1.set_ylabel('Temperatur (°C)', fontsize=12)
            ax1.set_title('Temperaturverlauf', fontsize=12, fontweight='bold')
            ax1.grid(True, alpha=0.3)

            press_cycles = [m.cycle_number for m in measurements if m.pressure is not None]
            ax2.plot(press_cycles, pressures, color='blue', linewidth=1)
            ax2.set_xlabel('Zyklus Nummer', fontsize=12)
            ax2.set_ylabel('Druck (bar)', fontsize=12)
            ax2.set_title('Druckverlauf', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            plot_path = self.output_dir / f"test_run_{test_run.id}_sensors.png"
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
            plot_files['sensor_data'] = str(plot_path)

        return plot_files

    def _generate_html_report(self, component, trend_analysis: Dict, test_runs: List, plot_files: Dict) -> str:
        """Generate HTML report for component"""
        html = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prüfbericht - {component.material_number}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #2c3e50;
            margin: 0;
        }}
        .meta-info {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .section {{
            margin: 30px 0;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        .info-card {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
        }}
        .info-card .label {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .info-card .value {{
            font-size: 18px;
            color: #3498db;
        }}
        .trend-box {{
            background-color: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin: 20px 0;
        }}
        .warning-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
        }}
        .success-box {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
        }}
        .plot-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .plot-container img {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #34495e;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-badge {{
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }}
        .status-completed {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status-running {{
            background-color: #cce5ff;
            color: #004085;
        }}
        .status-aborted {{
            background-color: #f8d7da;
            color: #721c24;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Prüfstandsbericht Pneumatik-Komponente</h1>
            <div class="meta-info">
                Erstellt am: {datetime.now().strftime("%d.%m.%Y um %H:%M:%S")}
            </div>
        </div>

        <div class="section">
            <h2>Komponenten-Informationen</h2>
            <div class="info-grid">
                <div class="info-card">
                    <div class="label">Bezeichnung 1:</div>
                    <div class="value">{component.designation_1}</div>
                </div>
                <div class="info-card">
                    <div class="label">Bezeichnung 2:</div>
                    <div class="value">{component.designation_2}</div>
                </div>
                <div class="info-card">
                    <div class="label">Materialnummer:</div>
                    <div class="value">{component.material_number}</div>
                </div>
                <div class="info-card">
                    <div class="label">Herstellernummer:</div>
                    <div class="value">{component.manufacturer_number}</div>
                </div>
                <div class="info-card">
                    <div class="label">Komponententyp:</div>
                    <div class="value">{component.component_type.value}</div>
                </div>
                <div class="info-card">
                    <div class="label">Status:</div>
                    <div class="value">{component.status.value}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Gesamt-Statistiken</h2>
            <div class="info-grid">
                <div class="info-card">
                    <div class="label">Anzahl Tests:</div>
                    <div class="value">{component.total_tests}</div>
                </div>
                <div class="info-card">
                    <div class="label">Gesamt-Schaltzyklen:</div>
                    <div class="value">{component.total_switching_cycles:,}</div>
                </div>
                <div class="info-card">
                    <div class="label">Gesamt-Stunden:</div>
                    <div class="value">{component.total_hours:.2f} h</div>
                </div>
                <div class="info-card">
                    <div class="label">Gesamt-Minuten:</div>
                    <div class="value">{component.total_minutes:.2f} min</div>
                </div>
            </div>
        </div>
"""

        # Add trend analysis
        if trend_analysis.get('status') == 'success':
            trend = trend_analysis['cycle_time_trend']
            perf = trend_analysis['performance_score']

            box_class = 'success-box' if perf['score'] >= 75 else 'warning-box'

            html += f"""
        <div class="section">
            <h2>Trend-Analyse</h2>
            <div class="{box_class}">
                <h3>Performance-Bewertung: {perf['rating']} ({perf['score']}/100)</h3>
                <p><strong>Trend:</strong> {trend['description']}</p>
                <p><strong>Degradation:</strong> {trend_analysis['degradation_rate']['description']}</p>
                <p><strong>Anomalien:</strong> {trend_analysis['anomalies']['description']}</p>
                <p><strong>Prognose:</strong> {trend_analysis['predictions']['description']}</p>
            </div>
        </div>
"""

        # Add plots
        if plot_files:
            html += """
        <div class="section">
            <h2>Visualisierungen</h2>
"""
            for plot_name, plot_path in plot_files.items():
                html += f"""
            <div class="plot-container">
                <img src="{plot_path}" alt="{plot_name}">
            </div>
"""
            html += """
        </div>
"""

        # Add test runs table
        if test_runs:
            html += """
        <div class="section">
            <h2>Testläufe</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Startzeit</th>
                        <th>Zyklen</th>
                        <th>Ø Schaltzeit (ms)</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
            for tr in test_runs[:10]:  # Show last 10
                status_class = f"status-{tr.status.lower()}"
                html += f"""
                    <tr>
                        <td>{tr.id}</td>
                        <td>{tr.start_time.strftime("%d.%m.%Y %H:%M")}</td>
                        <td>{tr.completed_cycles:,} / {tr.target_cycles:,}</td>
                        <td>{tr.average_cycle_time_ms:.2f}</td>
                        <td><span class="status-badge {status_class}">{tr.status}</span></td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""
        return html

    def _generate_test_run_html(self, component, test_run, measurements: List, analysis: Dict, plot_files: Dict) -> str:
        """Generate HTML for test run report"""
        duration = (test_run.end_time - test_run.start_time).total_seconds() / 60 if test_run.end_time else 0

        html = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Testlauf-Bericht #{test_run.id}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .info-card {{ background: #ecf0f1; padding: 15px; border-radius: 5px; }}
        .label {{ font-weight: bold; color: #2c3e50; }}
        .value {{ font-size: 18px; color: #3498db; }}
        .plot-container {{ margin: 20px 0; text-align: center; }}
        .plot-container img {{ max-width: 100%; border: 1px solid #ddd; }}
        .stats-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .stats-table th, .stats-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .stats-table th {{ background: #34495e; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Testlauf-Bericht #{test_run.id}</h1>
        <p>Komponente: {component.designation_1} ({component.material_number})</p>
        <p>Erstellt am: {datetime.now().strftime("%d.%m.%Y um %H:%M:%S")}</p>

        <h2>Test-Informationen</h2>
        <div class="info-grid">
            <div class="info-card">
                <div class="label">Startzeit:</div>
                <div class="value">{test_run.start_time.strftime("%d.%m.%Y %H:%M")}</div>
            </div>
            <div class="info-card">
                <div class="label">Dauer:</div>
                <div class="value">{duration:.2f} min</div>
            </div>
            <div class="info-card">
                <div class="label">Status:</div>
                <div class="value">{test_run.status}</div>
            </div>
            <div class="info-card">
                <div class="label">Zyklen:</div>
                <div class="value">{test_run.completed_cycles:,} / {test_run.target_cycles:,}</div>
            </div>
            <div class="info-card">
                <div class="label">Fortschritt:</div>
                <div class="value">{(test_run.completed_cycles/test_run.target_cycles*100):.1f}%</div>
            </div>
            <div class="info-card">
                <div class="label">Ø Schaltzeit:</div>
                <div class="value">{test_run.average_cycle_time_ms:.2f} ms</div>
            </div>
        </div>
"""

        # Add statistics
        if analysis.get('status') == 'success' and analysis.get('statistics'):
            stats = analysis['statistics']
            html += """
        <h2>Statistische Auswertung</h2>
        <table class="stats-table">
            <thead>
                <tr>
                    <th>Metrik</th>
                    <th>Mittelwert</th>
                    <th>Median</th>
                    <th>Std. Abw.</th>
                    <th>Min</th>
                    <th>Max</th>
                </tr>
            </thead>
            <tbody>
"""
            if stats.get('cycle_time'):
                ct = stats['cycle_time']
                html += f"""
                <tr>
                    <td><strong>Schaltzeit (ms)</strong></td>
                    <td>{ct['mean']}</td>
                    <td>{ct['median']}</td>
                    <td>{ct['std']}</td>
                    <td>{ct['min']}</td>
                    <td>{ct['max']}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
"""

        # Add plots
        for plot_name, plot_path in plot_files.items():
            html += f"""
        <div class="plot-container">
            <img src="{plot_path}" alt="{plot_name}">
        </div>
"""

        html += """
    </div>
</body>
</html>
"""
        return html
