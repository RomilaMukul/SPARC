"""
Unit Tests for Gaganyaan Crew Dosimetry Engine
===============================================
Tests 6-hour proton flux forecast, 3.5 g/cm² aluminum shielding dose math, and EVA alerts.
"""

import pytest
from src.models.crew_dosimetry import CrewDosimetryEngine


def test_crew_dosimetry_nominal_eval(nominal_space_weather):
    """Verify dosimetry calculations under nominal space environment."""
    engine = CrewDosimetryEngine()
    dosimetry = engine.predict_dosimetry(
        current_proton_flux=nominal_space_weather["proton_flux_pfu"],
        kp_index=nominal_space_weather["kp_index"],
    )

    assert "predicted_6h_accumulated_dose_msv" in dosimetry
    assert "eva_status" in dosimetry
    assert "safety_tier" in dosimetry

    # Under nominal conditions, EVA status should be SAFE / GREEN
    assert dosimetry["eva_status"] in ["SAFE_NOMINAL", "GREEN"]


def test_crew_dosimetry_severe_eval(severe_space_weather):
    """Verify dosimetry triggers EVA suspension alert under high proton flux."""
    engine = CrewDosimetryEngine()
    dosimetry = engine.predict_dosimetry(
        current_proton_flux=severe_space_weather["proton_flux_pfu"],
        kp_index=severe_space_weather["kp_index"],
    )

    assert dosimetry["predicted_6h_accumulated_dose_msv"] > 0.0
    # Under 1000+ pfu, EVA should be SUSPENDED / RED
    assert "SUSPEND" in dosimetry["eva_status"] or dosimetry["safety_tier"] in [
        "WARNING",
        "CRITICAL",
        "RED",
    ]


def test_dosimetry_shielding_mitigation():
    """Verify aluminum shielding reduces effective absorbed dose."""
    engine = CrewDosimetryEngine()
    dose_thin = engine.calculate_absorbed_dose(proton_flux=1000.0, shielding_g_cm2=1.0)
    dose_thick = engine.calculate_absorbed_dose(
        proton_flux=1000.0, shielding_g_cm2=3.5
    )

    assert dose_thick < dose_thin, "Thicker aluminum shielding must decrease absorbed dose"
