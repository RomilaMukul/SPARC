"""
Unit & Integration Tests for 3D Spatial Hazard Engine & Fleet Propagation
========================================================================
Tests SGP4 orbit propagation, coordinate transformations, and hazard scoring.
"""

import pytest
from src.models.spatial_hazard import (
    SpatialHazardEngine,
    load_fleet_config,
    calculate_gst_rad,
)


def test_load_fleet_config():
    """Verify fleet configuration loading returns active satellites."""
    fleet = load_fleet_config()
    assert isinstance(fleet, list)
    assert len(fleet) > 0

    sat = fleet[0]
    assert "name" in sat
    assert "norad_id" in sat
    assert "orbit" in sat


def test_calculate_gst_rad():
    """Verify Greenwich Sidereal Time calculation in radians."""
    from datetime import datetime, timezone

    dt = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
    gst = calculate_gst_rad(dt)

    assert 0.0 <= gst <= 2 * 3.141592653589793


def test_spatial_hazard_engine_evaluation(nominal_space_weather):
    """Verify hazard evaluation generates valid satellite threat vectors."""
    engine = SpatialHazardEngine()
    report = engine.evaluate_storm_hazards(
        solar_wind_speed_kms=nominal_space_weather["solar_wind_speed_kms"],
        bz_field_nt=nominal_space_weather["bz_field_nt"],
    )

    assert "fleet_hazard_profile" in report
    assert "active_satellites_count" in report
    assert report["active_satellites_count"] > 0

    for sat in report["fleet_hazard_profile"]:
        assert "hazard_ratio" in sat
        assert 0.0 <= sat["hazard_ratio"] <= 1.0
        assert "criticality" in sat
        assert "orbit_type" in sat


def test_spatial_hazard_high_storm_impact(severe_space_weather):
    """Verify hazard ratio increases under severe CME conditions."""
    engine = SpatialHazardEngine()
    quiet_report = engine.evaluate_storm_hazards(
        solar_wind_speed_kms=400.0, bz_field_nt=2.0
    )
    storm_report = engine.evaluate_storm_hazards(
        solar_wind_speed_kms=severe_space_weather["solar_wind_speed_kms"],
        bz_field_nt=severe_space_weather["bz_field_nt"],
    )

    avg_quiet_hazard = sum(
        s["hazard_ratio"] for s in quiet_report["fleet_hazard_profile"]
    ) / len(quiet_report["fleet_hazard_profile"])
    avg_storm_hazard = sum(
        s["hazard_ratio"] for s in storm_report["fleet_hazard_profile"]
    ) / len(storm_report["fleet_hazard_profile"])

    assert avg_storm_hazard >= avg_quiet_hazard
