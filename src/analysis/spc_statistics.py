"""
Statistical Process Control (SPC)
Statistische Prozessregelung nach Industriestandard
"""
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SPCResult:
    """SPC-Analyse Ergebnis"""
    # Prozessfähigkeit
    cp: float  # Process Capability
    cpk: float  # Process Capability Index
    pp: float  # Process Performance
    ppk: float  # Process Performance Index

    # Statistiken
    mean: float
    std_dev: float
    median: float
    range_value: float

    # Grenzen
    lower_spec_limit: float
    upper_spec_limit: float
    target_value: Optional[float]

    # Normalverteilung
    is_normal_distributed: bool
    normality_p_value: float

    # Bewertung
    capability_rating: str  # "Ausgezeichnet", "Gut", "Ausreichend", "Mangelhaft"

    # Out of Spec
    below_lsl_count: int
    above_usl_count: int
    out_of_spec_percent: float

    # Zusätzliche Metriken
    sigma_level: float


class SPCAnalyzer:
    """SPC-Analyse Tool"""

    @staticmethod
    def calculate_capability(
        data: List[float],
        lower_spec_limit: float,
        upper_spec_limit: float,
        target_value: Optional[float] = None
    ) -> SPCResult:
        """
        Berechnet Prozessfähigkeitskennzahlen

        Args:
            data: Messwerte
            lower_spec_limit: Untere Spezifikationsgrenze (USG)
            upper_spec_limit: Obere Spezifikationsgrenze (OSG)
            target_value: Sollwert (optional)

        Returns:
            SPCResult mit allen Kennzahlen
        """
        if len(data) < 30:
            raise ValueError("Mindestens 30 Messwerte für SPC erforderlich")

        data_array = np.array(data)

        # Grundlegende Statistiken
        mean = np.mean(data_array)
        std_dev = np.std(data_array, ddof=1)  # Stichproben-Standardabweichung
        median = np.median(data_array)
        range_value = np.max(data_array) - np.min(data_array)

        # Toleranzbereich
        tolerance = upper_spec_limit - lower_spec_limit

        # Cp - Process Capability (Prozessfähigkeit)
        # Cp = Toleranz / (6 * Sigma)
        cp = tolerance / (6 * std_dev) if std_dev > 0 else 0

        # Cpk - Process Capability Index (Prozessfähigkeitsindex)
        # Berücksichtigt die Lage des Prozesses
        cpu = (upper_spec_limit - mean) / (3 * std_dev) if std_dev > 0 else 0
        cpl = (mean - lower_spec_limit) / (3 * std_dev) if std_dev > 0 else 0
        cpk = min(cpu, cpl)

        # Pp und Ppk (langfristige Prozessleistung)
        # Verwendet Gesamtstandardabweichung
        pp = tolerance / (6 * std_dev) if std_dev > 0 else 0
        ppk = cpk  # Vereinfacht, normalerweise mit Langzeit-Sigma

        # Out of Spec zählen
        below_lsl = np.sum(data_array < lower_spec_limit)
        above_usl = np.sum(data_array > upper_spec_limit)
        out_of_spec_percent = (below_lsl + above_usl) / len(data) * 100

        # Sigma-Level
        sigma_level = cpk * 3

        # Normalverteilung prüfen (Shapiro-Wilk Test)
        from scipy import stats
        if len(data) <= 5000:
            _, p_value = stats.shapiro(data_array)
            is_normal = p_value > 0.05
        else:
            # Für große Datensätze: Anderson-Darling
            result = stats.anderson(data_array)
            is_normal = result.statistic < result.critical_values[2]  # 5% Signifikanz
            p_value = 0.05

        # Bewertung nach Cpk
        capability_rating = SPCAnalyzer._rate_capability(cpk)

        return SPCResult(
            cp=round(cp, 3),
            cpk=round(cpk, 3),
            pp=round(pp, 3),
            ppk=round(ppk, 3),
            mean=round(mean, 4),
            std_dev=round(std_dev, 4),
            median=round(median, 4),
            range_value=round(range_value, 4),
            lower_spec_limit=lower_spec_limit,
            upper_spec_limit=upper_spec_limit,
            target_value=target_value,
            is_normal_distributed=is_normal,
            normality_p_value=round(p_value, 4),
            capability_rating=capability_rating,
            below_lsl_count=int(below_lsl),
            above_usl_count=int(above_usl),
            out_of_spec_percent=round(out_of_spec_percent, 2),
            sigma_level=round(sigma_level, 2)
        )

    @staticmethod
    def _rate_capability(cpk: float) -> str:
        """Bewertet Prozessfähigkeit"""
        if cpk >= 2.0:
            return "Ausgezeichnet (Cpk ≥ 2.0)"
        elif cpk >= 1.67:
            return "Sehr gut (Cpk ≥ 1.67)"
        elif cpk >= 1.33:
            return "Gut (Cpk ≥ 1.33)"
        elif cpk >= 1.0:
            return "Ausreichend (Cpk ≥ 1.0)"
        else:
            return "Mangelhaft (Cpk < 1.0) - Prozess nicht fähig!"

    @staticmethod
    def calculate_control_limits(
        data: List[float],
        use_moving_range: bool = False
    ) -> Dict[str, float]:
        """
        Berechnet Regelkartengrenzen (Control Charts)

        Returns:
            Dictionary mit UCL, CL, LCL
        """
        data_array = np.array(data)
        mean = np.mean(data_array)
        std_dev = np.std(data_array, ddof=1)

        # Regelgrenzen (3-Sigma)
        ucl = mean + 3 * std_dev  # Upper Control Limit
        lcl = mean - 3 * std_dev  # Lower Control Limit

        # Warngrenzen (2-Sigma)
        uwl = mean + 2 * std_dev  # Upper Warning Limit
        lwl = mean - 2 * std_dev  # Lower Warning Limit

        return {
            'ucl': round(ucl, 4),
            'uwl': round(uwl, 4),
            'cl': round(mean, 4),  # Center Line
            'lwl': round(lwl, 4),
            'lcl': round(lcl, 4),
            'std_dev': round(std_dev, 4)
        }

    @staticmethod
    def check_control_rules(data: List[float]) -> List[str]:
        """
        Prüft Western Electric Rules / Nelson Rules

        Returns:
            Liste von Regelverstößen
        """
        violations = []
        data_array = np.array(data)

        if len(data) < 8:
            return violations

        mean = np.mean(data_array)
        std_dev = np.std(data_array, ddof=1)

        # Rule 1: Ein Punkt außerhalb 3-Sigma
        ucl = mean + 3 * std_dev
        lcl = mean - 3 * std_dev
        for i, value in enumerate(data_array):
            if value > ucl or value < lcl:
                violations.append(f"Regel 1: Punkt {i+1} außerhalb 3-Sigma")

        # Rule 2: 9 Punkte in Folge auf einer Seite
        if len(data) >= 9:
            for i in range(len(data) - 8):
                window = data_array[i:i+9]
                if np.all(window > mean) or np.all(window < mean):
                    violations.append(f"Regel 2: 9 Punkte ab Position {i+1} auf einer Seite")

        # Rule 3: 6 Punkte steigend oder fallend
        if len(data) >= 6:
            for i in range(len(data) - 5):
                window = data_array[i:i+6]
                diffs = np.diff(window)
                if np.all(diffs > 0):
                    violations.append(f"Regel 3: 6 steigende Punkte ab Position {i+1}")
                elif np.all(diffs < 0):
                    violations.append(f"Regel 3: 6 fallende Punkte ab Position {i+1}")

        # Rule 4: 14 Punkte alternierend auf/ab
        if len(data) >= 14:
            for i in range(len(data) - 13):
                window = data_array[i:i+14]
                diffs = np.diff(window)
                signs = np.sign(diffs)
                alternating = np.all(signs[:-1] * signs[1:] < 0)
                if alternating:
                    violations.append(f"Regel 4: 14 alternierende Punkte ab Position {i+1}")

        return violations

    @staticmethod
    def generate_spc_report(spc_result: SPCResult) -> str:
        """Generiert textuellen SPC-Bericht"""
        report = "=== SPC-ANALYSE BERICHT ===\n\n"

        report += "PROZESSFÄHIGKEIT:\n"
        report += f"  Cp  = {spc_result.cp:.3f}\n"
        report += f"  Cpk = {spc_result.cpk:.3f}\n"
        report += f"  Pp  = {spc_result.pp:.3f}\n"
        report += f"  Ppk = {spc_result.ppk:.3f}\n"
        report += f"  Bewertung: {spc_result.capability_rating}\n"
        report += f"  Sigma-Level: {spc_result.sigma_level:.2f}σ\n\n"

        report += "PROZESSSTATISTIKEN:\n"
        report += f"  Mittelwert:    {spc_result.mean:.4f}\n"
        report += f"  Standardabw.:  {spc_result.std_dev:.4f}\n"
        report += f"  Median:        {spc_result.median:.4f}\n"
        report += f"  Spannweite:    {spc_result.range_value:.4f}\n\n"

        report += "SPEZIFIKATIONSGRENZEN:\n"
        report += f"  USG (LSL):     {spc_result.lower_spec_limit:.4f}\n"
        report += f"  OSG (USL):     {spc_result.upper_spec_limit:.4f}\n"
        if spc_result.target_value:
            report += f"  Sollwert:      {spc_result.target_value:.4f}\n"
        report += "\n"

        report += "AUSSCHUSS:\n"
        report += f"  Unter USG:     {spc_result.below_lsl_count}\n"
        report += f"  Über OSG:      {spc_result.above_usl_count}\n"
        report += f"  Ausschussrate: {spc_result.out_of_spec_percent:.2f}%\n\n"

        report += "NORMALVERTEILUNG:\n"
        report += f"  Normal verteilt: {'Ja' if spc_result.is_normal_distributed else 'Nein'}\n"
        report += f"  p-Wert:         {spc_result.normality_p_value:.4f}\n\n"

        # Interpretation
        report += "INTERPRETATION:\n"
        if spc_result.cpk >= 1.33:
            report += "  ✓ Prozess ist fähig und unter Kontrolle.\n"
        elif spc_result.cpk >= 1.0:
            report += "  ⚠ Prozess ist grenzwertig fähig. Überwachung empfohlen.\n"
        else:
            report += "  ✗ Prozess ist NICHT fähig! Sofortige Maßnahmen erforderlich!\n"

        if spc_result.out_of_spec_percent > 0:
            report += f"  ⚠ {spc_result.out_of_spec_percent:.2f}% Ausschuss - Prozessoptimierung nötig!\n"

        if not spc_result.is_normal_distributed:
            report += "  ⚠ Daten sind nicht normalverteilt - SPC-Kennzahlen nur begrenzt aussagekräftig!\n"

        return report
