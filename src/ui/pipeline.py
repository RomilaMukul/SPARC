"""
SPARC-PM: Master Pipeline Execution Engine
===========================================
Connects live scenario telemetry to the 5 SPARC model engines:
1. SpaceWeatherSeverityClassifier
2. CrewDosimetryEngine
3. SpatialHazardEngine
4. PredictiveMaintenanceEngine
5. AStarActionScheduler

Maintains single-source-of-truth calculations without duplicating backend code.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from src.models.crew_dosimetry import CrewDosimetryEngine
from src.models.predictive_maint import PredictiveMaintenanceEngine
from src.models.severity_classifier import SpaceWeatherSeverityClassifier
from src.models.spatial_hazard import SpatialHazardEngine
from src.scheduler.a_star_scheduler import AStarActionScheduler

# Preset Scenarios
SCENARIOS: Dict[str, Dict[str, Any]] = {
    "NOMINAL (Quiet Solar Min)": {
        "proton_flux_pfu": 1.2,
        "proton_speed_kms": 380.0,
        "mag_bz_field": 3.2,
        "proton_density_cm3": 4.0,
        "solar_wind_dyn_pressure_npa": 1.2,
        "description": "Background solar wind under quiet solar minimum conditions.",
    },
    "G1_MINOR (August 2024 Event)": {
        "proton_flux_pfu": 15.0,
        "proton_speed_kms": 520.0,
        "mag_bz_field": -4.5,
        "proton_density_cm3": 8.0,
        "solar_wind_dyn_pressure_npa": 2.5,
        "description": "Minor geomagnetic disturbance with elevated solar wind speed.",
    },
    "G2_MODERATE (CME Shock)": {
        "proton_flux_pfu": 85.0,
        "proton_speed_kms": 580.0,
        "mag_bz_field": -9.2,
        "proton_density_cm3": 11.5,
        "solar_wind_dyn_pressure_npa": 4.1,
        "description": "Moderate CME shock front impacting magnetosphere.",
    },
    "G3_SEVERE (October 2024 SPE)": {
        "proton_flux_pfu": 420.0,
        "proton_speed_kms": 740.0,
        "mag_bz_field": -21.0,
        "proton_density_cm3": 18.2,
        "solar_wind_dyn_pressure_npa": 9.6,
        "description": "Severe solar proton event front causing polar cap absorption.",
    },
    "G5_EXTREME (May 2024 Super-Storm)": {
        "proton_flux_pfu": 1850.0,
        "proton_speed_kms": 890.0,
        "mag_bz_field": -34.5,
        "proton_density_cm3": 28.4,
        "solar_wind_dyn_pressure_npa": 14.8,
        "description": "G5 Extreme geomagnetic super-storm event (May 10-12, 2024 benchmark).",
    },
}

# Cached Engine Singletons
@st.cache_resource
def get_classifier() -> SpaceWeatherSeverityClassifier:
    return SpaceWeatherSeverityClassifier.load_model()

@st.cache_resource
def get_spatial_engine() -> SpatialHazardEngine:
    return SpatialHazardEngine()

@st.cache_resource
def get_dosimetry_engine() -> CrewDosimetryEngine:
    return CrewDosimetryEngine()

@st.cache_resource
def get_maint_engine() -> PredictiveMaintenanceEngine:
    return PredictiveMaintenanceEngine()

@st.cache_resource
def get_scheduler() -> AStarActionScheduler:
    return AStarActionScheduler()


def execute_pipeline(
    telemetry: Dict[str, float],
    scenario_name: str = "G3_SEVERE (October 2024 SPE)",
) -> Dict[str, Any]:
    """
    Executes the end-to-end 5-engine SPARC pipeline deterministically.
    
    Returns structured results dictionary containing exact outputs from:
    - severity_report
    - dosimetry_report
    - hazard_report
    - fleet_maintenance
    - scheduled_commands
    """
    t_start = time.perf_counter()

    # 1. Severity Classification Engine
    clf = get_classifier()
    severity_report = clf.predict_single(telemetry)

    # 2. Gaganyaan Crew Dosimetry Forecast
    dosimetry_eng = get_dosimetry_engine()
    flux = float(telemetry.get("proton_flux_pfu", 10.0))
    speed = float(telemetry.get("proton_speed_kms", 400.0))
    bz = float(telemetry.get("mag_bz_field", 0.0))
    hist_flux = [flux * (0.85 + 0.03 * i) for i in range(15)]
    dosimetry_report = dosimetry_eng.forecast_6h_radiation_curve(
        hist_flux, speed, bz
    )

    # 3. 3D Spatial Orbital Hazard Assessment Engine
    spatial_eng = get_spatial_engine()
    hazard_report = spatial_eng.evaluate_storm_hazards(
        solar_wind_speed_kms=speed,
        bz_field_nt=bz,
        proton_flux_pfu=flux,
    )

    # 4. Predictive Maintenance Engine
    maint_eng = get_maint_engine()
    fleet_maintenance = maint_eng.evaluate_fleet_telemetry()

    # 5. A* Telecommand Action Scheduler
    scheduler = get_scheduler()
    scheduled_commands = scheduler.schedule_telecommands(
        hazard_report["fleet_hazard_profile"], fleet_maintenance
    )

    t_total_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    return {
        "scenario_name": scenario_name,
        "telemetry": telemetry,
        "severity_report": severity_report,
        "dosimetry_report": dosimetry_report,
        "hazard_report": hazard_report,
        "fleet_maintenance": fleet_maintenance,
        "scheduled_commands": scheduled_commands,
        "pipeline_latency_ms": t_total_ms,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }
