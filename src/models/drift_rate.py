"""
SPARC-PM: Telemetry Drift Rate Computation Engine
==================================================
Computes rolling drift rates for satellite subsensors
(battery voltage, subsystem temperature, gyroscope drift)
over configurable time windows to detect degradation trends.
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SYNTHETIC_DATA_PATH = (
    PROJECT_ROOT / "data" / "processed" / "synthetic_fleet_telemetry.csv"
)

# Drift rate thresholds (per hour, normalized)
DRIFT_THRESHOLD_VOLTAGE = 0.05  # V/hr — above this indicates battery degradation
DRIFT_THRESHOLD_TEMP = 0.5  # °C/hr — above this indicates thermal anomaly
DRIFT_THRESHOLD_GYRO = 0.01  # °/hr² — above this indicates gyro instability

# Anomaly severity tiers
DRIFT_SEVERITY_MAP = {
    "NOMINAL": 0,
    "ELEVATED": 1,
    "WARNING": 2,
    "CRITICAL": 3,
}


class DriftRateEngine:
    """
    Computes real-time and cumulative drift rates for satellite subsensors.
    Analyzes telemetry time-series to detect degradation trends before
    they manifest as component failures.
    """

    FEATURE_NAMES = [
        "battery_voltage",
        "subsystem_temp_c",
        "gyro_drift_deg_hr",
    ]

    def __init__(self, data_path: Optional[Union[str, Path]] = None):
        self.data_path = Path(data_path) if data_path else SYNTHETIC_DATA_PATH
        self.df: Optional[pd.DataFrame] = None
        if self.data_path.exists():
            self.df = pd.read_csv(self.data_path)

    def _get_satellite_timeseries(self, sat_id: str) -> Optional[pd.DataFrame]:
        """Returns chronological telemetry for a single satellite."""
        if self.df is None:
            return None
        sat_df = (
            self.df[self.df["sat_id"] == sat_id]
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        return sat_df if len(sat_df) > 1 else None

    def compute_drift_rate(
        self,
        sat_id: str,
        window_minutes: int = 60,
    ) -> Dict[str, Any]:
        """
        Computes drift rate for a single satellite over a time window.

        Args:
            sat_id: Satellite identifier.
            window_minutes: Rolling window size in minutes.

        Returns:
            Dict containing drift rates for each sensor and severity assessment.
        """
        sat_df = self._get_satellite_timeseries(sat_id)
        if sat_df is None or len(sat_df) < 2:
            return {"sat_id": sat_id, "drift_rates": {}, "severity": "UNKNOWN"}

        drift_rates: Dict[str, float] = {}
        sensor_columns: Dict[str, str] = {
            "battery_voltage_drift": "battery_voltage",
            "subsystem_temp_drift": "subsystem_temp_c",
            "gyro_drift_rate": "gyro_drift_deg_hr",
        }

        for metric_name, col_name in sensor_columns.items():
            if col_name not in sat_df.columns:
                drift_rates[metric_name] = 0.0
                continue

            values = sat_df[col_name].values
            if len(values) < 2:
                drift_rates[metric_name] = 0.0
                continue

            # Compute drift as slope over the window using linear regression
            # Normalize by time delta to get per-hour drift rate
            n = len(values)
            timestamps = np.arange(n)
            slope = np.polyfit(timestamps, values, 1)[0]
            # Scale: data is per-minute, drift = slope * 60 for per-hour rate
            drift_rates[metric_name] = round(float(slope * 60.0), 4)

        # Determine overall severity
        severity = self._assess_drift_severity(drift_rates)

        return {
            "sat_id": sat_id,
            "drift_rates": drift_rates,
            "severity": severity,
            "window_minutes": window_minutes,
        }

    def compute_fleet_drift(
        self,
        window_minutes: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Computes drift rates across the entire fleet.

        Args:
            window_minutes: Rolling window size in minutes.

        Returns:
            List of drift reports sorted by severity (highest first).
        """
        if self.df is None:
            return []

        sat_ids = self.df["sat_id"].unique()
        results = []

        for sat_id in sat_ids:
            report = self.compute_drift_rate(sat_id, window_minutes)
            results.append(report)

        results.sort(
            key=lambda x: DRIFT_SEVERITY_MAP.get(x["severity"], 0), reverse=True
        )
        return results

    def _assess_drift_severity(self, drift_rates: Dict[str, float]) -> str:
        """
        Assesses overall drift severity based on individual sensor drifts.
        """
        voltage_drift = abs(drift_rates.get("battery_voltage_drift", 0.0))
        temp_drift = abs(drift_rates.get("subsystem_temp_drift", 0.0))
        gyro_drift = abs(drift_rates.get("gyro_drift_rate", 0.0))

        critical_count = 0
        warning_count = 0

        if voltage_drift > DRIFT_THRESHOLD_VOLTAGE * 3:
            critical_count += 1
        elif voltage_drift > DRIFT_THRESHOLD_VOLTAGE:
            warning_count += 1

        if temp_drift > DRIFT_THRESHOLD_TEMP * 3:
            critical_count += 1
        elif temp_drift > DRIFT_THRESHOLD_TEMP:
            warning_count += 1

        if gyro_drift > DRIFT_THRESHOLD_GYRO * 3:
            critical_count += 1
        elif gyro_drift > DRIFT_THRESHOLD_GYRO:
            warning_count += 1

        if critical_count >= 2:
            return "CRITICAL"
        elif warning_count >= 2:
            return "WARNING"
        elif warning_count >= 1:
            return "ELEVATED"
        else:
            return "NOMINAL"

    def detect_anomaly_satellites(
        self,
        threshold: str = "WARNING",
    ) -> List[str]:
        """
        Returns list of satellite IDs exceeding the drift threshold.

        Args:
            threshold: Minimum severity level to flag ("ELEVATED", "WARNING", "CRITICAL").

        Returns:
            List of satellite IDs with anomalous drift rates.
        """
        fleet_drift = self.compute_fleet_drift()
        threshold_level = DRIFT_SEVERITY_MAP.get(threshold, 2)
        return [
            r["sat_id"]
            for r in fleet_drift
            if DRIFT_SEVERITY_MAP.get(r["severity"], 0) >= threshold_level
        ]

    def save_report(
        self,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """Saves drift analysis report to CSV."""
        save_path = (
            Path(output_path)
            if output_path
            else PROJECT_ROOT / "data" / "processed" / "drift_rate_report.csv"
        )
        save_path.parent.mkdir(parents=True, exist_ok=True)

        results = self.compute_fleet_drift()
        df_report = pd.DataFrame(results)
        df_report.to_csv(save_path, index=False)
        print(f"[SAVE] Drift rate report saved -> {save_path}")
        return save_path


if __name__ == "__main__":
    print("📊 Initializing SPARC Telemetry Drift Rate Engine...")
    engine = DriftRateEngine()
    fleet_drift = engine.compute_fleet_drift()
    print(f"Analyzed {len(fleet_drift)} satellites.")
    anomalies = engine.detect_anomaly_satellites(threshold="WARNING")
    print(f"Anomalous satellites: {anomalies}")
    engine.save_report()
