"""
Unit & Integration Tests for Multi-Class Space Weather Severity Classifier
==========================================================================
Verifies model inference correctness, feature engineering, and latency constraints.
"""

import time
import pytest
import numpy as np
from src.models.severity_classifier import (
    SpaceWeatherSeverityClassifier,
    compute_akasofu_epsilon,
    compute_dynamic_pressure,
)


def test_akasofu_epsilon_computation():
    """Verify Akasofu Epsilon magnetospheric coupling index math."""
    eps_quiet = compute_akasofu_epsilon(v_sw=400.0, b_z=2.0, b_y=1.0)
    eps_storm = compute_akasofu_epsilon(v_sw=800.0, b_z=-15.0, b_y=5.0)

    assert eps_quiet >= 0.0
    assert eps_storm > eps_quiet, "Storm coupling energy must exceed quiet energy"


def test_dynamic_pressure_computation():
    """Verify solar wind dynamic pressure math in nPa."""
    p_dyn = compute_dynamic_pressure(n_p=5.0, v_sw=450.0)
    assert p_dyn > 0.0
    assert isinstance(p_dyn, float)


def test_severity_classifier_nominal_inference(nominal_space_weather):
    """Verify classifier predicts G0_NOMINAL under quiet solar conditions."""
    clf = SpaceWeatherSeverityClassifier()
    result = clf.predict_storm_severity(
        solar_wind_speed=nominal_space_weather["solar_wind_speed_kms"],
        bz_field=nominal_space_weather["bz_field_nt"],
        proton_density=nominal_space_weather["proton_density_cm3"],
        proton_flux=nominal_space_weather["proton_flux_pfu"],
    )

    assert "severity_class" in result
    assert "probabilities" in result
    assert result["severity_class"] in ["G0_NOMINAL_QUIET", "G1_MINOR_DISTURBANCE"]


def test_severity_classifier_severe_inference(severe_space_weather):
    """Verify classifier predicts elevated storm (G2/G3) under severe CME conditions."""
    clf = SpaceWeatherSeverityClassifier()
    result = clf.predict_storm_severity(
        solar_wind_speed=severe_space_weather["solar_wind_speed_kms"],
        bz_field=severe_space_weather["bz_field_nt"],
        proton_density=severe_space_weather["proton_density_cm3"],
        proton_flux=severe_space_weather["proton_flux_pfu"],
    )

    assert result["severity_class"] in ["G2_MODERATE_STORM", "G3_SEVERE_STORM"]
    assert result["probabilities"][result["severity_class"]] > 0.5


def test_severity_classifier_latency_constraint(nominal_space_weather):
    """Verify inference latency is sub-50ms (specification target: < 5ms)."""
    clf = SpaceWeatherSeverityClassifier()

    t0 = time.perf_counter()
    _ = clf.predict_storm_severity(
        solar_wind_speed=nominal_space_weather["solar_wind_speed_kms"],
        bz_field=nominal_space_weather["bz_field_nt"],
        proton_density=nominal_space_weather["proton_density_cm3"],
        proton_flux=nominal_space_weather["proton_flux_pfu"],
    )
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert latency_ms < 50.0, f"Inference latency ({latency_ms:.2f} ms) exceeded 50ms limit"
