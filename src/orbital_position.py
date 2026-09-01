
import os
import json
import math
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sgp4.api import Satrec, jday

TLE_INPUT = "data/processed/satellites_tle.json"
RISK_OUTPUT = "data/processed/satellite_risk.json"
EARTH_RADIUS_KM = 6378.137
EARTH_FLATTENING = 1 / 298.257223563
STORM_CORRIDORS = [
    {"name": "South Atlantic Anomaly", "lat": -25.0, "lon": -45.0, "base_radius_km": 1500.0},
    {"name": "Northern Auroral Oval",  "lat": 70.0,  "lon": 0.0,   "base_radius_km": 1800.0},
    {"name": "Southern Auroral Oval",  "lat": -70.0, "lon": 0.0,   "base_radius_km": 1800.0},
]

SEVERITY_RADIUS_MULTIPLIER = {
    "Calm": 0.6,
    "Watch": 1.0,
    "Warning": 1.4,
    "Emergency": 2.0,
}


def _gmst_radians(dt: datetime) -> float:
    """Greenwich Mean Sidereal Time, in radians, for a UTC datetime."""
    jd = (
        367 * dt.year
        - int(7 * (dt.year + int((dt.month + 9) / 12)) / 4)
        + int(275 * dt.month / 9)
        + dt.day
        + 1721013.5
        + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24
    )
    t = (jd - 2451545.0) / 36525.0
    gmst_sec = (
        67310.54841
        + (876600 * 3600 + 8640184.812866) * t
        + 0.093104 * t * t
        - 6.2e-6 * t * t * t
    )
    gmst_deg = (gmst_sec % 86400.0) / 240.0  # seconds -> degrees
    return math.radians(gmst_deg % 360.0)


def teme_to_ecef(x, y, z, dt: datetime):
    theta = _gmst_radians(dt)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    x_ecef = cos_t * x + sin_t * y
    y_ecef = -sin_t * x + cos_t * y
    z_ecef = z
    return x_ecef, y_ecef, z_ecef


def ecef_to_geodetic(x, y, z):
    """Convert ECEF (km) to geodetic latitude/longitude/altitude (deg, deg, km)."""
    a = EARTH_RADIUS_KM
    f = EARTH_FLATTENING
    b = a * (1 - f)
    e2 = 1 - (b ** 2) / (a ** 2)

    lon = math.atan2(y, x)
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1 - e2))  # initial guess

    for _ in range(5):  # iterative refinement
        sin_lat = math.sin(lat)
        n = a / math.sqrt(1 - e2 * sin_lat * sin_lat)
        alt = p / math.cos(lat) - n
        lat = math.atan2(z + e2 * n * sin_lat, p)

    sin_lat = math.sin(lat)
    n = a / math.sqrt(1 - e2 * sin_lat * sin_lat)
    alt = p / math.cos(lat) - n

    return math.degrees(lat), math.degrees(lon), alt


def latlonalt_to_ecef(lat_deg, lon_deg, alt_km):
    """Convert geodetic lat/lon/alt back to ECEF (km) — used to place the
    fixed storm-corridor centers in the same 3D frame as the satellites."""
    a = EARTH_RADIUS_KM
    f = EARTH_FLATTENING
    e2 = 2 * f - f * f
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    n = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    x = (n + alt_km) * math.cos(lat) * math.cos(lon)
    y = (n + alt_km) * math.cos(lat) * math.sin(lon)
    z = (n * (1 - e2) + alt_km) * math.sin(lat)
    return np.array([x, y, z])


def propagate_satellite(line1: str, line2: str, when: datetime = None):
    """Run SGP4 for one TLE at a given UTC time, return ECEF position (km)
    plus geodetic lat/lon/alt."""
    if when is None:
        when = datetime.now(timezone.utc)

    sat = Satrec.twoline2rv(line1, line2)
    jd, fr = jday(when.year, when.month, when.day, when.hour, when.minute, when.second)
    error_code, pos_teme, _vel = sat.sgp4(jd, fr)

    if error_code != 0:
        raise ValueError(f"SGP4 propagation error code {error_code}")

    x_ecef, y_ecef, z_ecef = teme_to_ecef(*pos_teme, when)
    lat, lon, alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)

    return {
        "ecef_km": np.array([x_ecef, y_ecef, z_ecef]),
        "lat": lat,
        "lon": lon,
        "alt_km": alt,
    }


def nearest_storm_corridor(sat_ecef: np.ndarray, sat_alt_km: float, severity: str = "Watch"):
    """Find the closest storm corridor to a satellite and classify risk."""
    multiplier = SEVERITY_RADIUS_MULTIPLIER.get(severity, 1.0)

    best = None
    for corridor in STORM_CORRIDORS:
        corridor_ecef = latlonalt_to_ecef(corridor["lat"], corridor["lon"], sat_alt_km)
        distance_km = float(np.linalg.norm(sat_ecef - corridor_ecef))
        effective_radius = corridor["base_radius_km"] * multiplier

        if best is None or distance_km < best["distance_km"]:
            best = {
                "corridor": corridor["name"],
                "distance_km": round(distance_km, 1),
                "effective_radius_km": round(effective_radius, 1),
            }

    if best["distance_km"] <= best["effective_radius_km"]:
        best["risk_level"] = "CRITICAL"
    elif best["distance_km"] <= best["effective_radius_km"] * 1.3:
        best["risk_level"] = "WARNING"
    else:
        best["risk_level"] = "NOMINAL"

    return best


def compute_fleet_risk(severity: str = "Watch") -> pd.DataFrame:
    """Load TLEs, propagate every satellite, and compute storm-corridor risk
    for each one. `severity` should come from the Naive Bayes classifier's
    current output, so the danger-zone size reacts to live conditions."""

    if not os.path.exists(TLE_INPUT):
        raise FileNotFoundError(
            f"'{TLE_INPUT}' not found. Run fetch_celestrak.py first."
        )

    with open(TLE_INPUT) as f:
        satellites = json.load(f)

    now = datetime.now(timezone.utc)
    rows = []
    for sat in satellites:
        try:
            pos = propagate_satellite(sat["line1"], sat["line2"], now)
            risk = nearest_storm_corridor(pos["ecef_km"], pos["alt_km"], severity)
            rows.append({
                "name": sat["name"],
                "norad_id": sat["norad_id"],
                "lat": round(pos["lat"], 2),
                "lon": round(pos["lon"], 2),
                "alt_km": round(pos["alt_km"], 1),
                "nearest_corridor": risk["corridor"],
                "distance_km": risk["distance_km"],
                "risk_level": risk["risk_level"],
            })
        except Exception as e:
            print(f"Skipping {sat.get('name', '?')}: {e}")

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(RISK_OUTPUT), exist_ok=True)
    df.to_json(RISK_OUTPUT, orient="records", indent=2)
    print(f"Computed 3D risk for {len(df)} satellites -> '{RISK_OUTPUT}'")
    return df


if __name__ == "__main__":
    table = compute_fleet_risk(severity="Watch")
    print(table.to_string(index=False))