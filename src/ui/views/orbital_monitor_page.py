"""
SPARC-PM: 3D Mission Globe & Orbital Operations Monitor
=========================================================
Visual centerpiece implementing the exact SPARC architecture:
Scenario Engine ➔ Authoritative Orbit State ➔ 3D Mission Globe
(Spacecraft + Storm Hazards + ISRO/DSN Ground Stations + Ground Tracks)
➔ Selected Asset ➔ WHY / RESPONSE ➔ A* COMMAND
"""

import math
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.components.mission_header import render_mission_header
from src.ui.components.satellite_panel import render_satellite_panel
from src.ui.pipeline import get_spatial_engine

# Restrained Mission Control Palette
_COLORS = {
    "CRITICAL": "#ef4444",   # Red
    "WARNING":  "#f59e0b",   # Amber
    "ELEVATED": "#3b82f6",   # Blue
    "NOMINAL":  "#10b981",   # Green
}

_TRAIL_COLORS = {
    "CRITICAL": "rgba(239, 68, 68, 0.35)",
    "WARNING":  "rgba(245, 158, 11, 0.30)",
    "ELEVATED": "rgba(59, 130, 246, 0.25)",
    "NOMINAL":  "rgba(16, 185, 129, 0.20)",
}

# ISRO & NASA Ground Station Network Registry
GROUND_STATIONS = [
    {"name": "ISTRAC Bengaluru (MOC)", "code": "ISTRAC-BLR", "lat": 12.9716, "lon": 77.5946, "agency": "ISRO", "status": "ACTIVE_PRIMARY"},
    {"name": "MCF Hassan", "code": "MCF-HSN", "lat": 13.0068, "lon": 76.0996, "agency": "ISRO", "status": "ACTIVE_GEO_RELAY"},
    {"name": "SDSC Sriharikota", "code": "SDSC-SHAR", "lat": 13.7199, "lon": 80.2304, "agency": "ISRO", "status": "ACTIVE_LAUNCH"},
    {"name": "NASA DSN Goldstone", "code": "DSN-GDS", "lat": 35.4267, "lon": -116.8900, "agency": "NASA", "status": "ACTIVE_DEEP_SPACE"},
    {"name": "NASA DSN Madrid", "code": "DSN-MAD", "lat": 40.4272, "lon": -4.2497, "agency": "NASA", "status": "ACTIVE_DEEP_SPACE"},
    {"name": "NASA DSN Canberra", "code": "DSN-CBR", "lat": -35.4014, "lon": 148.9817, "agency": "NASA", "status": "ACTIVE_DEEP_SPACE"},
]


def lla_to_ecef(lat_deg: float, lon_deg: float, alt_km: float = 0.0) -> np.ndarray:
    """Transforms Latitude, Longitude, Altitude to 3D ECEF cartesian coordinates (km)."""
    r_earth = 6378.137 + alt_km
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)

    x = r_earth * math.cos(lat_rad) * math.cos(lon_rad)
    y = r_earth * math.cos(lat_rad) * math.sin(lon_rad)
    z = r_earth * math.sin(lat_rad)
    return np.array([x, y, z])


def render_earth_mesh(resolution: int = 48) -> go.Surface:
    """Generates visible Earth sphere with ocean and continental contrast."""
    u = np.linspace(0, 2 * np.pi, resolution)
    v = np.linspace(0, np.pi, resolution)
    r = 6378.137

    x = r * np.outer(np.cos(u), np.sin(v))
    y = r * np.outer(np.sin(u), np.sin(v))
    z = r * np.outer(np.ones_like(u), np.cos(v))

    # Procedural elevation texture for oceans and continents
    elevation = np.sin(3 * np.outer(np.cos(u), np.sin(v))) * np.cos(4 * np.outer(np.sin(u), np.sin(v)))

    return go.Surface(
        x=x, y=y, z=z,
        surfacecolor=elevation,
        colorscale=[
            [0.0, "rgb(12, 42, 92)"],     # Deep Ocean
            [0.4, "rgb(24, 75, 140)"],    # Shallow Ocean
            [0.6, "rgb(32, 105, 68)"],    # Land / Forest
            [0.85, "rgb(125, 105, 65)"],  # Desert / Mountain
            [1.0, "rgb(220, 235, 250)"],  # Polar Ice Cap
        ],
        showscale=False,
        opacity=0.92,
        hoverinfo="skip",
        name="Earth",
    )


def render_storm_corridor_mesh(center_ecef: List[float], radius_km: float) -> go.Surface:
    """Generates visible translucent 3D storm hazard corridor sphere."""
    u = np.linspace(0, 2 * np.pi, 24)
    v = np.linspace(0, np.pi, 24)
    cx, cy, cz = center_ecef

    x = cx + radius_km * np.outer(np.cos(u), np.sin(v))
    y = cy + radius_km * np.outer(np.sin(u), np.sin(v))
    z = cz + radius_km * np.outer(np.ones_like(u), np.cos(v))

    return go.Surface(
        x=x, y=y, z=z,
        colorscale=[[0, "rgba(239, 68, 68, 0.25)"], [1, "rgba(239, 68, 68, 0.45)"]],
        showscale=False,
        opacity=0.35,
        hoverinfo="skip",
        name="Storm Corridor",
    )


from src.ui.components.html_utils import render_html


def render_orbital_monitor_page() -> None:
    """Renders the 3D Mission Globe & Orbital Operations visualization page."""
    render_mission_header(
        page_title="SPARC-PM : 3D MISSION GLOBE & ORBITAL OPERATIONS MONITOR",
        subtitle="Scenario Engine • Authoritative Orbit State • 3D ECEF Globe • Situational Telemetry Inspector",
    )

    results = st.session_state.get("pipeline_results", {})
    haz = results.get("hazard_report", {})
    sev = results.get("severity_report", {})
    telemetry = results.get("telemetry", {})
    fleet = haz.get("fleet_hazard_profile", [])

    if not fleet:
        st.warning("No satellite fleet hazard data available. Run simulation from Scenario Simulator.")
        return

    # 1. Fleet Telemetry Ribbon HUD
    crit_count = sum(1 for s in fleet if s.get("alert_level") == "CRITICAL")
    warn_count = sum(1 for s in fleet if s.get("alert_level") == "WARNING")
    elev_count = sum(1 for s in fleet if s.get("alert_level") == "ELEVATED")
    nom_count = sum(1 for s in fleet if s.get("alert_level") == "NOMINAL")
    corridor_radius = haz.get("storm_corridor_radius_km", 0.0)
    sev_label = sev.get("severity_label", "NOMINAL")
    triage = sev.get("triage", "GREEN")

    render_html(f"""
        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 14px;">
            <div style="background: #0b132b; border: 1px solid rgba(66, 217, 245, 0.2); border-radius: 6px; padding: 10px 12px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #64748b; text-transform: uppercase;">TRACKED FLEET</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.15rem; color: #f8fafc;">
                    {len(fleet)} <span style="font-size: 0.7rem; color: #64748b;">UNITS</span>
                </div>
            </div>
            <div style="background: #0b132b; border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 6px; padding: 10px 12px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #ef4444; text-transform: uppercase;">CRITICAL RISK</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.15rem; color: {'#ef4444' if crit_count > 0 else '#64748b'};">
                    {crit_count} <span style="font-size: 0.7rem; color: #64748b;">ASSETS</span>
                </div>
            </div>
            <div style="background: #0b132b; border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 6px; padding: 10px 12px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #f59e0b; text-transform: uppercase;">WARNING / ELEVATED</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.15rem; color: {'#f59e0b' if (warn_count + elev_count) > 0 else '#64748b'};">
                    {warn_count + elev_count} <span style="font-size: 0.7rem; color: #64748b;">ASSETS</span>
                </div>
            </div>
            <div style="background: #0b132b; border: 1px solid rgba(52, 211, 153, 0.25); border-radius: 6px; padding: 10px 12px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #34d399; text-transform: uppercase;">GROUND STATIONS</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.15rem; color: #34d399;">
                    {len(GROUND_STATIONS)} <span style="font-size: 0.7rem; color: #64748b;">ONLINE</span>
                </div>
            </div>
            <div style="background: #0b132b; border: 1px solid rgba(66, 217, 245, 0.2); border-radius: 6px; padding: 10px 12px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #42d9f5; text-transform: uppercase;">STORM ENVELOPE</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.15rem; color: #f8fafc;">
                    {corridor_radius:,.0f} <span style="font-size: 0.7rem; color: #64748b;">km</span>
                </div>
            </div>
        </div>
    """)

    # 2. Controls Toolbar
    with st.container(border=True):
        col_lbl, col_toggles, col_filter, col_select = st.columns([1.5, 2.8, 1.6, 2.1])

        with col_lbl:
            render_html("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; font-weight: 700; color: #42d9f5; letter-spacing: 0.8px; margin-top: 6px;">
                    ORBITAL CONTROLS
                </div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.68rem; color: #64748b;">
                    Multi-layer ECEF projection
                </div>
            """)

        with col_toggles:
            t1, t2, t3 = st.columns(3)
            with t1:
                show_trails = st.checkbox("Orbit Trails", value=True, key="om_page_trails")
            with t2:
                show_ground_tracks = st.checkbox("Ground Tracks", value=True, key="om_page_gtracks")
            with t3:
                show_storm = st.checkbox("Storm Hazard", value=True, key="om_page_storm")

        with col_filter:
            risk_filter = st.selectbox(
                "Filter Fleet State:",
                ["ALL", "CRITICAL", "WARNING", "ELEVATED", "NOMINAL"],
                index=0,
                key="om_page_risk_filter",
            )

        with col_select:
            sat_names = [s["name"] for s in fleet]
            default_idx = 0
            # Sync with session state selection if available
            saved_sat = st.session_state.get("selected_sat_name")
            if saved_sat in sat_names:
                default_idx = sat_names.index(saved_sat)

            selected_sat_name = st.selectbox(
                "Target Spacecraft Focus:",
                sat_names,
                index=default_idx,
                key="om_page_sat_select",
            )
            st.session_state["selected_sat_name"] = selected_sat_name

    # Filter fleet based on risk filter
    if risk_filter != "ALL":
        filtered_fleet = [s for s in fleet if s.get("alert_level") == risk_filter]
    else:
        filtered_fleet = fleet

    spatial_eng = get_spatial_engine()

    # 3. Build Plotly 3D Figure
    fig = go.Figure()

    # (A) Earth Surface Mesh
    fig.add_trace(render_earth_mesh())

    # (B) Storm Envelope Sphere (Hazards)
    corridor_center = haz.get("storm_center_ecef")
    if show_storm and corridor_center and corridor_radius > 0:
        fig.add_trace(render_storm_corridor_mesh(corridor_center, corridor_radius))

    # (C) Ground Stations Network
    gs_coords = np.array([lla_to_ecef(gs["lat"], gs["lon"]) for gs in GROUND_STATIONS])
    gs_hovers = [f"<b>{gs['name']}</b><br>Agency: {gs['agency']}<br>Lat/Lon: {gs['lat']}°, {gs['lon']}°<br>Status: {gs['status']}" for gs in GROUND_STATIONS]

    fig.add_trace(go.Scatter3d(
        x=gs_coords[:, 0],
        y=gs_coords[:, 1],
        z=gs_coords[:, 2],
        mode="markers+text",
        name=f"Ground Stations ({len(GROUND_STATIONS)})",
        text=[gs["code"] for gs in GROUND_STATIONS],
        textposition="top center",
        hovertext=gs_hovers,
        hoverinfo="text",
        marker=dict(size=7, color="#34d399", symbol="diamond", line=dict(width=1, color="#ffffff")),
    ))

    # (D) Orbit Trails & Ground Tracks
    if show_trails or show_ground_tracks:
        drawn_orbits = set()
        for sat in filtered_fleet:
            if sat.get("altitude_km", 0) > 45000:
                continue
            sat_name = sat.get("name", "")
            traj = spatial_eng.propagate_orbit_trajectory(sat, n_points=60)
            if traj is None:
                continue

            orbit_sig = f"{sat.get('altitude_km', 0):.0f}_{sat.get('orbit_type', '')}"
            if orbit_sig in drawn_orbits:
                continue
            drawn_orbits.add(orbit_sig)

            alert = sat.get("alert_level", "NOMINAL")
            trail_col = _TRAIL_COLORS.get(alert, _TRAIL_COLORS["NOMINAL"])

            # 3D Orbit Trajectory Line
            if show_trails:
                fig.add_trace(go.Scatter3d(
                    x=traj["x"],
                    y=traj["y"],
                    z=traj["z"],
                    mode="lines",
                    line=dict(color=trail_col, width=1.5),
                    hoverinfo="skip",
                    showlegend=False,
                ))

            # Sub-Satellite Ground Track Projection on Earth surface
            if show_ground_tracks:
                gt_x, gt_y, gt_z = [], [], []
                r_earth = 6385.0
                for tx, ty, tz in zip(traj["x"], traj["y"], traj["z"]):
                    mag = math.sqrt(tx**2 + ty**2 + tz**2) + 1e-6
                    gt_x.append((tx / mag) * r_earth)
                    gt_y.append((ty / mag) * r_earth)
                    gt_z.append((tz / mag) * r_earth)

                fig.add_trace(go.Scatter3d(
                    x=gt_x,
                    y=gt_y,
                    z=gt_z,
                    mode="lines",
                    line=dict(color="rgba(148, 163, 184, 0.35)", width=1.2, dash="dash"),
                    hoverinfo="skip",
                    showlegend=False,
                ))

    # (E) Satellite Markers by Risk Tier
    for tier in ["CRITICAL", "WARNING", "ELEVATED", "NOMINAL"]:
        tier_sats = [s for s in filtered_fleet if s.get("alert_level") == tier]
        if not tier_sats:
            continue

        coords = []
        hover_texts = []
        for s in tier_sats:
            pos = np.array(s.get("r_ecef", [0, 0, 0]), dtype=float)
            norm = np.linalg.norm(pos)
            # Clamp deep-space assets (e.g. Aditya-L1 at 1.5M km) to GEO boundary so Earth is never shrunken to a sub-pixel
            if norm > 45000:
                pos = (pos / norm) * 42000.0
            coords.append(pos)
            is_deep = norm > 45000
            hover_texts.append(
                f"<b>{s['name']}</b><br>"
                f"Alert: {s.get('alert_level')}<br>"
                f"Alt: {s.get('altitude_km', 0):,.1f} km<br>"
                f"Hazard H_j: {s.get('hazard_ratio', 0):.4f}<br>"
                f"Dist to Storm: {s.get('dist_to_storm_km', 0):,.1f} km"
                + ("<br><i>[Deep Space Asset: Clamped to GEO]</i>" if is_deep else "")
            )
        coords = np.array(coords)

        marker_size = 8.0 if tier == "CRITICAL" else 6.5 if tier == "WARNING" else 5.0
        marker_color = _COLORS[tier]

        fig.add_trace(go.Scatter3d(
            x=coords[:, 0],
            y=coords[:, 1],
            z=coords[:, 2],
            mode="markers+text",
            name=f"{tier} ({len(tier_sats)})",
            text=[s["name"] if s["name"] == selected_sat_name else "" for s in tier_sats],
            textposition="top center",
            hovertext=hover_texts,
            hoverinfo="text",
            marker=dict(
                size=marker_size,
                color=marker_color,
                opacity=0.92,
                line=dict(width=1.5, color="#ffffff" if tier == "CRITICAL" else "rgba(255,255,255,0.4)"),
            ),
        ))

    # (F) Target Spacecraft Glowing Reticle Ring
    sel_sat_obj = next((s for s in fleet if s["name"] == selected_sat_name), None)
    if sel_sat_obj:
        sel_pos = np.array(sel_sat_obj.get("r_ecef", [0, 0, 0]), dtype=float)
        sel_norm = np.linalg.norm(sel_pos)
        if sel_norm > 45000:
            sel_pos = (sel_pos / sel_norm) * 42000.0

        fig.add_trace(go.Scatter3d(
            x=[sel_pos[0]],
            y=[sel_pos[1]],
            z=[sel_pos[2]],
            mode="markers+text",
            name=f"TARGET: {selected_sat_name}",
            text=[f"⬡ {selected_sat_name}"],
            textposition="top center",
            hoverinfo="skip",
            marker=dict(
                size=13,
                color="rgba(66, 217, 245, 0.2)",
                symbol="circle-open",
                line=dict(width=3, color="#42d9f5"),
            ),
            showlegend=False,
        ))

    # Plotly Layout
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#080d17",
        plot_bgcolor="#080d17",
        height=660,
        margin=dict(l=0, r=0, t=10, b=10),
        scene=dict(
            xaxis=dict(title="", showticklabels=False, showgrid=False, zeroline=False, range=[-45000, 45000], backgroundcolor="#080d17"),
            yaxis=dict(title="", showticklabels=False, showgrid=False, zeroline=False, range=[-45000, 45000], backgroundcolor="#080d17"),
            zaxis=dict(title="", showticklabels=False, showgrid=False, zeroline=False, range=[-45000, 45000], backgroundcolor="#080d17"),
            aspectmode="cube",
            camera=dict(eye=dict(x=1.65, y=1.25, z=0.85)),
        ),
        legend=dict(
            x=0.01, y=0.98,
            bgcolor="rgba(11, 19, 43, 0.88)",
            bordercolor="rgba(66, 217, 245, 0.25)",
            borderwidth=1,
            font=dict(family="JetBrains Mono, monospace", size=10, color="#f8fafc"),
        ),
    )

    # 4. Split 2-Column Responsive Layout: Globe + Telemetry HUD
    col_globe, col_details = st.columns([7, 5])

    with col_globe:
        try:
            st.plotly_chart(fig, width="stretch")
        except TypeError:
            st.plotly_chart(fig, use_container_width=True)

    with col_details:
        selected_sat = next((s for s in fleet if s["name"] == selected_sat_name), fleet[0])
        render_satellite_panel(selected_sat, sev, telemetry)

    # 5. Collapsible Full Fleet Table
    with st.expander("📋 Full Spacecraft Fleet Orbital Roster & Hazard Table", expanded=False):
        fleet_rows = []
        for s in fleet:
            fleet_rows.append({
                "Spacecraft": s.get("name", "N/A"),
                "Sat ID": s.get("sat_id", "N/A"),
                "Orbit Type": s.get("orbit_type", "N/A"),
                "Altitude (km)": f"{s.get('altitude_km', 0):,.1f}",
                "Velocity (km/s)": f"{s.get('speed_kms', 0):.3f}",
                "Hazard H_j": f"{s.get('hazard_ratio', 0):.4f}",
                "Dist to Storm (km)": f"{s.get('dist_to_storm_km', 0):,.1f}",
                "Criticality": f"{s.get('criticality', 0.5):.2f}",
                "Alert Tier": s.get("alert_level", "NOMINAL"),
            })
        try:
            st.dataframe(pd.DataFrame(fleet_rows), width="stretch", hide_index=True)
        except TypeError:
            st.dataframe(pd.DataFrame(fleet_rows), use_container_width=True, hide_index=True)

