"""
Remaining Time Predictor - Predicts remaining test time
"""
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from collections import deque

from ..models.component import TestRun


class RemainingTimePredictor:
    """Predicts remaining time for running tests"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.cycle_times = deque(maxlen=window_size)
        self.last_update = None
        self.start_time = None
        self.total_cycles = 0
        self.completed_cycles = 0

    def start(self, total_cycles: int):
        """Start prediction for a new test"""
        self.start_time = datetime.now()
        self.total_cycles = total_cycles
        self.completed_cycles = 0
        self.cycle_times.clear()
        self.last_update = None

    def update(self, cycle_time_ms: float):
        """Update with new cycle time"""
        self.cycle_times.append(cycle_time_ms)
        self.completed_cycles += 1
        self.last_update = datetime.now()

    def predict(self) -> Dict[str, Any]:
        """Predict remaining time"""
        if not self.cycle_times or self.completed_cycles == 0:
            return {
                'status': 'insufficient_data',
                'remaining_cycles': self.total_cycles,
                'remaining_time_seconds': None,
                'estimated_completion': None
            }

        # Calculate average cycle time
        avg_cycle_time_ms = sum(self.cycle_times) / len(self.cycle_times)

        # Remaining cycles
        remaining_cycles = self.total_cycles - self.completed_cycles

        # Remaining time in seconds
        remaining_time_seconds = (remaining_cycles * avg_cycle_time_ms) / 1000.0

        # Estimated completion time
        estimated_completion = datetime.now() + timedelta(seconds=remaining_time_seconds)

        # Calculate confidence based on data stability
        if len(self.cycle_times) >= 10:
            import numpy as np
            std_dev = np.std(list(self.cycle_times))
            mean = np.mean(list(self.cycle_times))
            cv = std_dev / mean if mean > 0 else 1
            confidence = max(0, min(100, (1 - cv) * 100))
        else:
            confidence = 50.0  # Low confidence with few data points

        # Progress percentage
        progress = (self.completed_cycles / self.total_cycles * 100) if self.total_cycles > 0 else 0

        return {
            'status': 'ok',
            'completed_cycles': self.completed_cycles,
            'remaining_cycles': remaining_cycles,
            'total_cycles': self.total_cycles,
            'progress_percent': round(progress, 2),
            'average_cycle_time_ms': round(avg_cycle_time_ms, 2),
            'remaining_time_seconds': round(remaining_time_seconds, 1),
            'remaining_time_formatted': self._format_time(remaining_time_seconds),
            'estimated_completion': estimated_completion,
            'estimated_completion_formatted': estimated_completion.strftime("%d.%m.%Y %H:%M:%S"),
            'confidence': round(confidence, 1),
            'elapsed_time_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }

    def _format_time(self, seconds: float) -> str:
        """Format time in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)} Sekunden"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes} Min {secs} Sek"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours} Std {minutes} Min"
