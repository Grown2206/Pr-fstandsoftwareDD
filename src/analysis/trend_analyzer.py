"""
Trend Analyzer - Detects trends and anomalies in test data
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from scipy import stats
from sklearn.linear_model import LinearRegression

from ..models.component import TestRun, TestMeasurement
from ..database.db_manager import DatabaseManager


class TrendAnalyzer:
    """Analyzes trends in component test data"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def analyze_component_trends(self, component_id: int) -> Dict[str, Any]:
        """Analyze trends for a specific component"""
        test_runs = self.db.get_test_runs_for_component(component_id)

        if not test_runs:
            return {
                'status': 'no_data',
                'message': 'Keine Testdaten verfügbar'
            }

        # Extract time series data
        cycle_times = []
        temperatures = []
        pressures = []
        dates = []

        for test_run in test_runs:
            if test_run.average_cycle_time_ms > 0:
                cycle_times.append(test_run.average_cycle_time_ms)
                dates.append(test_run.start_time)

        if len(cycle_times) < 3:
            return {
                'status': 'insufficient_data',
                'message': 'Zu wenige Testdurchläufe für Trendanalyse'
            }

        # Calculate trends
        cycle_time_trend = self._calculate_trend(cycle_times)
        degradation_rate = self._calculate_degradation_rate(cycle_times, dates)
        anomalies = self._detect_anomalies(cycle_times)

        # Performance assessment
        performance_score = self._calculate_performance_score(cycle_times, anomalies)

        # Predictions
        predicted_failure_cycles = self._predict_failure_point(cycle_times)

        return {
            'status': 'success',
            'total_test_runs': len(test_runs),
            'cycle_time_trend': {
                'direction': cycle_time_trend['direction'],
                'slope': cycle_time_trend['slope'],
                'correlation': cycle_time_trend['correlation'],
                'description': self._describe_trend(cycle_time_trend)
            },
            'degradation_rate': {
                'rate_ms_per_day': degradation_rate,
                'description': self._describe_degradation(degradation_rate)
            },
            'anomalies': {
                'count': len(anomalies),
                'indices': anomalies,
                'description': f'{len(anomalies)} Anomalien erkannt' if anomalies else 'Keine Anomalien'
            },
            'performance_score': {
                'score': performance_score,
                'rating': self._rate_performance(performance_score)
            },
            'predictions': {
                'estimated_failure_cycles': predicted_failure_cycles,
                'description': self._describe_prediction(predicted_failure_cycles)
            }
        }

    def analyze_test_run_details(self, test_run_id: int) -> Dict[str, Any]:
        """Detailed analysis of a single test run"""
        test_run = self.db.get_test_run(test_run_id)
        if not test_run:
            return {'status': 'error', 'message': 'Testlauf nicht gefunden'}

        measurements = self.db.get_measurements_for_test_run(test_run_id)

        if not measurements:
            return {'status': 'error', 'message': 'Keine Messdaten verfügbar'}

        # Extract measurement data
        cycle_times = [m.switching_time_ms for m in measurements if m.successful]
        temperatures = [m.temperature for m in measurements if m.temperature is not None]
        pressures = [m.pressure for m in measurements if m.pressure is not None]

        # Statistical analysis
        stats_analysis = {
            'cycle_time': self._calculate_statistics(cycle_times),
            'temperature': self._calculate_statistics(temperatures) if temperatures else None,
            'pressure': self._calculate_statistics(pressures) if pressures else None
        }

        # Trend during test
        cycle_trend = self._calculate_trend(cycle_times)

        # Error analysis
        errors = [m for m in measurements if not m.successful]
        error_rate = len(errors) / len(measurements) * 100 if measurements else 0

        # Stability analysis
        stability_score = self._calculate_stability(cycle_times)

        return {
            'status': 'success',
            'test_run_id': test_run_id,
            'statistics': stats_analysis,
            'trend': {
                'direction': cycle_trend['direction'],
                'strength': abs(cycle_trend['correlation']),
                'description': self._describe_trend(cycle_trend)
            },
            'errors': {
                'count': len(errors),
                'rate': round(error_rate, 2),
                'error_messages': [e.error_message for e in errors if e.error_message]
            },
            'stability': {
                'score': stability_score,
                'rating': self._rate_stability(stability_score)
            }
        }

    def _calculate_trend(self, data: List[float]) -> Dict[str, Any]:
        """Calculate trend using linear regression"""
        if len(data) < 2:
            return {'direction': 'unknown', 'slope': 0, 'correlation': 0}

        x = np.array(range(len(data))).reshape(-1, 1)
        y = np.array(data)

        model = LinearRegression()
        model.fit(x, y)

        slope = model.coef_[0]
        correlation, _ = stats.pearsonr(x.flatten(), y)

        if abs(correlation) < 0.3:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'

        return {
            'direction': direction,
            'slope': float(slope),
            'correlation': float(correlation)
        }

    def _calculate_degradation_rate(self, cycle_times: List[float],
                                    dates: List[datetime]) -> float:
        """Calculate degradation rate per day"""
        if len(cycle_times) < 2 or len(dates) < 2:
            return 0.0

        # Time span in days
        time_span = (dates[-1] - dates[0]).total_seconds() / 86400
        if time_span == 0:
            return 0.0

        # Cycle time change
        cycle_time_change = cycle_times[-1] - cycle_times[0]

        return cycle_time_change / time_span

    def _detect_anomalies(self, data: List[float]) -> List[int]:
        """Detect anomalies using statistical methods"""
        if len(data) < 5:
            return []

        data_array = np.array(data)
        mean = np.mean(data_array)
        std = np.std(data_array)

        # Points beyond 2 standard deviations are anomalies
        anomalies = []
        for i, value in enumerate(data):
            if abs(value - mean) > 2 * std:
                anomalies.append(i)

        return anomalies

    def _calculate_performance_score(self, cycle_times: List[float],
                                     anomalies: List[int]) -> float:
        """Calculate overall performance score (0-100)"""
        if not cycle_times:
            return 0.0

        # Base score from stability
        cv = np.std(cycle_times) / np.mean(cycle_times) if np.mean(cycle_times) > 0 else 1
        stability_score = max(0, 100 - cv * 100)

        # Penalty for anomalies
        anomaly_penalty = (len(anomalies) / len(cycle_times)) * 30

        # Penalty for trend
        trend = self._calculate_trend(cycle_times)
        trend_penalty = abs(trend['slope']) / np.mean(cycle_times) * 100

        score = max(0, min(100, stability_score - anomaly_penalty - trend_penalty))
        return round(score, 2)

    def _predict_failure_point(self, cycle_times: List[float]) -> int:
        """Predict when component might fail"""
        if len(cycle_times) < 3:
            return -1

        # Use linear regression to predict
        x = np.array(range(len(cycle_times))).reshape(-1, 1)
        y = np.array(cycle_times)

        model = LinearRegression()
        model.fit(x, y)

        # Define failure threshold (e.g., 150% of initial cycle time)
        failure_threshold = cycle_times[0] * 1.5
        current_avg = np.mean(cycle_times)

        if model.coef_[0] <= 0:  # Not degrading
            return -1

        # Estimate cycles until failure
        cycles_remaining = (failure_threshold - current_avg) / model.coef_[0]

        if cycles_remaining < 0:
            return 0

        return int(cycles_remaining * len(cycle_times))

    def _calculate_statistics(self, data: List[float]) -> Dict[str, float]:
        """Calculate basic statistics"""
        if not data:
            return {}

        return {
            'mean': round(np.mean(data), 2),
            'median': round(np.median(data), 2),
            'std': round(np.std(data), 2),
            'min': round(min(data), 2),
            'max': round(max(data), 2),
            'range': round(max(data) - min(data), 2)
        }

    def _calculate_stability(self, data: List[float]) -> float:
        """Calculate stability score (coefficient of variation inverted)"""
        if not data or np.mean(data) == 0:
            return 0.0

        cv = np.std(data) / np.mean(data)
        stability = max(0, min(100, (1 - cv) * 100))
        return round(stability, 2)

    def _describe_trend(self, trend: Dict[str, Any]) -> str:
        """Describe trend in German"""
        direction = trend['direction']
        correlation = abs(trend['correlation'])

        if direction == 'stable':
            return "Stabile Leistung, keine signifikante Änderung"
        elif direction == 'increasing':
            if correlation > 0.7:
                return "Starke Verschlechterung: Schaltzeiten nehmen deutlich zu"
            elif correlation > 0.4:
                return "Moderate Verschlechterung: Schaltzeiten steigen"
            else:
                return "Leichte Verschlechterung erkennbar"
        else:  # decreasing
            if correlation > 0.7:
                return "Starke Verbesserung: Schaltzeiten nehmen deutlich ab"
            elif correlation > 0.4:
                return "Moderate Verbesserung: Schaltzeiten sinken"
            else:
                return "Leichte Verbesserung erkennbar"

    def _describe_degradation(self, rate: float) -> str:
        """Describe degradation rate"""
        if abs(rate) < 0.1:
            return "Vernachlässigbare Verschleißrate"
        elif rate > 1.0:
            return "Hohe Verschleißrate - Überwachung empfohlen"
        elif rate > 0.5:
            return "Moderate Verschleißrate"
        elif rate > 0:
            return "Niedrige Verschleißrate"
        else:
            return "Keine Verschlechterung festgestellt"

    def _describe_prediction(self, cycles: int) -> str:
        """Describe failure prediction"""
        if cycles < 0:
            return "Keine Verschlechterung prognostiziert"
        elif cycles == 0:
            return "Kritischer Zustand - sofortige Wartung empfohlen"
        elif cycles < 10000:
            return f"Geschätzte Restlaufzeit: ~{cycles:,} Zyklen - baldige Wartung empfohlen"
        elif cycles < 100000:
            return f"Geschätzte Restlaufzeit: ~{cycles:,} Zyklen - normale Überwachung"
        else:
            return "Sehr lange Restlaufzeit prognostiziert"

    def _rate_performance(self, score: float) -> str:
        """Rate performance score"""
        if score >= 90:
            return "Ausgezeichnet"
        elif score >= 75:
            return "Gut"
        elif score >= 60:
            return "Befriedigend"
        elif score >= 40:
            return "Ausreichend"
        else:
            return "Mangelhaft - Wartung erforderlich"

    def _rate_stability(self, score: float) -> str:
        """Rate stability score"""
        if score >= 90:
            return "Sehr stabil"
        elif score >= 75:
            return "Stabil"
        elif score >= 60:
            return "Mäßig stabil"
        else:
            return "Instabil"
