"""
SPARC-PM: Mission Control Page
===============================
Full-screen immersive mission control interface with interactive 3D Earth globe,
floating panels, satellite selection, WHY/RESPONSE explanations, and A* command queue.

This page uses the authoritative backend pipeline data without duplication.
"""

from __future__ import annotations

import streamlit as st

from src.ui.components.globe_renderer import generate_globe_html
from src.ui.pipeline import get_spatial_engine


def render_mission_control_page() -> None:
    """Renders the full-screen mission control globe interface."""
    results = st.session_state.get("pipeline_results", {})
    if not results:
        st.warning("Pipeline not initialized. Running default scenario...")
        return

    hazard_report = results.get("hazard_report", {})
    severity_report = results.get("severity_report", {})
    telemetry = results.get("telemetry", {})
    scheduled_commands = results.get("scheduled_commands", {})
    dosimetry_report = results.get("dosimetry_report", {})
    scenario_name = results.get("scenario_name", "")
    pipeline_latency_ms = results.get("pipeline_latency_ms", 0)
    timestamp = results.get("timestamp", "")

    fleet = hazard_report.get("fleet_hazard_profile", [])
    if not fleet:
        st.warning("No fleet hazard data available.")
        return

    # Compute orbit trajectories using the authoritative SpatialHazardEngine
    spatial_eng = get_spatial_engine()
    orbit_trajectories = []
    drawn_orbits = set()
    for sat in fleet:
        orbit_sig = f"{sat.get('altitude_km', 0):.0f}_{sat.get('orbit_type', '')}"
        if orbit_sig in drawn_orbits:
            orbit_trajectories.append(None)
            continue
        drawn_orbits.add(orbit_sig)
        traj = spatial_eng.propagate_orbit_trajectory(sat, n_points=60)
        orbit_trajectories.append(traj)

    # Generate the Three.js globe HTML
    globe_html = generate_globe_html(
        hazard_report=hazard_report,
        severity_report=severity_report,
        telemetry=telemetry,
        scheduled_commands=scheduled_commands,
        dosimetry_report=dosimetry_report,
        orbit_trajectories=orbit_trajectories,
        scenario_name=scenario_name,
        pipeline_latency_ms=pipeline_latency_ms,
        timestamp=timestamp,
        height=900,
    )

    # Render the Three.js globe in an iframe.
    # Uses native st.iframe if available (Streamlit 1.33+), falling back to components.html.
    if hasattr(st, "iframe"):
        st.iframe(globe_html, height=900)
    else:
        import streamlit.components.v1 as components
        components.html(globe_html, height=900, scrolling=False)
