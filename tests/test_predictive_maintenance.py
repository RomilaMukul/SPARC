"""
Unit Tests for CNN-LSTM Predictive Maintenance Model
===================================================
Tests 72-hour failure risk scoring (P_fail) and sensor diagnostic telemetry triage.
"""

import pytest
from src.models.predictive_maint import PredictiveMaintenanceEngine


def test_predictive_maint_diagnostics():
    """Verify fleet diagnostic evaluation returns structured risk telemetry."""
    engine = PredictiveMaintenanceEngine()
    fleet_diag = engine.diagnose_fleet()

    assert isinstance(fleet_diag, list)
    assert len(fleet_diag) > 0

    for item in fleet_diag:
        assert "sat_id" in item
        assert "p_fail_72h" in item
        assert 0.0 <= item["p_fail_72h"] <= 1.0
        assert "health_status" in item


def test_predictive_maint_anomaly_detection():
    """Verify high sensor noise spikes trigger elevated failure probability."""
    engine = PredictiveMaintenanceEngine()
    high_risk_eval = engine.evaluate_single_satellite(
        sat_id="GAGANYAAN-1",
        sensor_telemetry={
            "temp_c": 85.0,
            "bus_voltage_v": 21.0,  # Under-voltage
            "gyro_drift_deg_h": 0.45,  # High drift
            "thruster_pressure_bar": 1.2,
            "solar_array_current_a": 4.5,
        },
    )

    assert "p_fail_72h" in high_risk_eval
    assert high_risk_eval["p_fail_72h"] >= 0.10
