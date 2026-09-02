"""
SPARC Test Suite Configuration & Shared Fixtures
=================================================
Provides standard mock data, telemetry vectors, and fleet definitions for pytest execution.
"""

import os
import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def nominal_space_weather():
    """Nominal solar wind conditions (quiet sun)."""
    return {
        "solar_wind_speed_kms": 380.0,
        "bz_field_nt": 2.5,
        "proton_density_cm3": 4.0,
        "proton_flux_pfu": 1.2,
        "kp_index": 1.0,
    }


@pytest.fixture
def severe_space_weather():
    """Severe CME space weather event (G3+ storm)."""
    return {
        "solar_wind_speed_kms": 850.0,
        "bz_field_nt": -18.5,
        "proton_density_cm3": 45.0,
        "proton_flux_pfu": 1250.0,
        "kp_index": 7.5,
    }


@pytest.fixture
def sample_fleet_hazard_profile():
    """Sample satellite hazard input profile for scheduler testing."""
    return [
        {
            "sat_id": "99001",
            "name": "GAGANYAAN-1 (CREW SIM)",
            "orbit_type": "CREW_MODULE",
            "hazard_ratio": 0.78,
            "criticality": 1.0,
            "time_to_corridor_sec": 450.0,
        },
        {
            "sat_id": "44804",
            "name": "CARTOSAT-3",
            "orbit_type": "SSO",
            "hazard_ratio": 0.52,
            "criticality": 0.7,
            "time_to_corridor_sec": 1200.0,
        },
        {
            "sat_id": "52899",
            "name": "GSAT-24",
            "orbit_type": "GEO",
            "hazard_ratio": 0.12,
            "criticality": 0.5,
            "time_to_corridor_sec": 3600.0,
        },
    ]
