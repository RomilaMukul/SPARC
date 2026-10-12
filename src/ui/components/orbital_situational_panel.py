"""
SPARC-PM: Orbital Situational Awareness Panel
=============================================
Renders real-time SGP4 satellite ground positions, DSN ground stations,
and dynamic solar storm corridor proximities using Plotly geographic projection.
Synchronized with the active A* command queue selection.
Uses render_html to prevent CommonMark code-block rendering bugs.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.components.html_utils import render_html


# Authentic ISRO Ground Station Network Coordinates
GROUND_STATIONS = [
    {"name": "ISTRAC (Bangalore)", "lat": 12.9716, "lon": 77.5946, "code": "BLR-01", "type": "TTC Master"},
    {"name": "MCF (Hassan)", "lat": 13.0620, "lon": 76.1025, "code": "HSN-01", "type": "GEO Prime"},
    {"name": "Port Blair Ground Station", "lat": 11.6234, "lon": 92.7265, "code": "PBR-01", "type": "LEO Tracking"},
    {"name": "Svalbard Satellite Station (Polar)", "lat": 78.2298, "lon": 15.4078, "code": "SGS-01", "type": "Polar Relay"},
]


def render_orbital_situational_panel(
    fleet_hazard_profile: List[Dict[str, Any]],
    selected_sat_id: Optional[str] = None,
    storm_radius_km: float = 45000.0,
) -> None:
    """Renders the 2D Equirectangular Situational Awareness map with ground tracks and ground stations."""
    if not fleet_hazard_profile:
        render_html(
            """
            <div style="background: #111B2B; border: 1px solid rgba(66, 217, 245, 0.15); border-radius: 6px; padding: 20px; text-align: center; color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
                ⚠️ SGP4 FLEET TELEMETRY NOT INITIALIZED
            </div>
            """
        )
        return

    # Extract coordinates
    records = []
    selected_record: Optional[Dict[str, Any]] = None

    for sat in fleet_hazard_profile:
        sid = sat.get("sat_id", sat.get("name", "SAT"))
        lat = sat.get("latitude", 0.0)
        lon = sat.get("longitude", 0.0)
        alt = sat.get("altitude_km", 0.0)
        hazard = sat.get("hazard_ratio", 0.0)
        alert = sat.get("alert_level", "NOMINAL")
        name = sat.get("name", sid)
        orbit = sat.get("orbit_type", "LEO")

        rec = {
            "sat_id": sid,
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "altitude_km": alt,
            "hazard_ratio": hazard,
            "alert_level": alert,
            "orbit_type": orbit,
            "dist_to_storm_km": sat.get("dist_to_storm_km", 0.0),
            "speed_kms": sat.get("speed_kms", 7.5),
        }
        records.append(rec)
        if selected_sat_id and (sid == selected_sat_id or name == selected_sat_id):
            selected_record = rec

    if not selected_record and records:
        selected_record = records[0]

    df_fleet = pd.DataFrame(records)

    # Plotly Geographic Figure
    fig = go.Figure()

    # 1. Base Coastlines and Earth Grid
    fig.update_geos(
        projection_type="equirectangular",
        showcoastlines=True,
        coastlinecolor="rgba(148, 163, 184, 0.25)",
        showland=True,
        landcolor="#0D1624",
        showocean=True,
        oceancolor="#080D17",
        showlakes=True,
        lakecolor="#080D17",
        showcountries=True,
        countrycolor="rgba(148, 163, 184, 0.12)",
        bgcolor="#080D17",
    )

    # 2. Ground Station Markers
    gs_df = pd.DataFrame(GROUND_STATIONS)
    fig.add_trace(
        go.Scattergeo(
            lat=gs_df["lat"],
            lon=gs_df["lon"],
            mode="markers+text",
            text=[f"📡 {code}" for code in gs_df["code"]],
            textposition="top center",
            textfont=dict(family="JetBrains Mono", size=9, color="#94a3b8"),
            marker=dict(size=8, color="#42D9F5", symbol="diamond", line=dict(width=1, color="#ffffff")),
            name="Ground Stations (DSN)",
            hoverinfo="text",
            hovertext=[f"<b>{name}</b><br/>Type: {t}<br/>Lat: {lat:.2f}°, Lon: {lon:.2f}°" for name, t, lat, lon in zip(gs_df["name"], gs_df["type"], gs_df["lat"], gs_df["lon"])],
        )
    )

    # 3. Fleet Assets (Color-coded by Hazard Level)
    sel_id = selected_record["sat_id"] if selected_record else None
    unselected_df = df_fleet[df_fleet["sat_id"] != sel_id]

    color_map = {
        "CRITICAL": "#FF647C",
        "WARNING": "#FFBD59",
        "ELEVATED": "#42D9F5",
        "NOMINAL": "#45D6A0",
    }
    marker_colors = [color_map.get(lvl, "#45D6A0") for lvl in unselected_df["alert_level"]]

    fig.add_trace(
        go.Scattergeo(
            lat=unselected_df["latitude"],
            lon=unselected_df["longitude"],
            mode="markers",
            marker=dict(
                size=7,
                color=marker_colors,
                opacity=0.75,
                line=dict(width=0.5, color="rgba(255, 255, 255, 0.4)"),
            ),
            name="Constellation Assets",
            hoverinfo="text",
            hovertext=[
                f"<b>{row['name']}</b> ({row['orbit_type']})<br/>"
                f"Lat: {row['latitude']:.2f}°, Lon: {row['longitude']:.2f}°<br/>"
                f"Alt: {row['altitude_km']:,.0f} km | Hazard: {row['hazard_ratio']*100:.1f}%"
                for _, row in unselected_df.iterrows()
            ],
        )
    )

    # 4. Simulated Orbit Ground Track for Selected Asset
    if selected_record:
        inc = float(selected_record.get("inclination_deg", 51.6 if selected_record["orbit_type"] == "LEO" else 0.1))
        # Generate representative ground track points
        import numpy as np
        theta = np.linspace(-np.pi, np.pi, 80)
        track_lats = [float(inc * math.sin(t)) for t in theta]
        # Shift longitudes relative to current target sub-satellite point
        target_lon = float(selected_record["longitude"])
        track_lons = [float(((target_lon + math.degrees(t) + 180) % 360) - 180) for t in theta]
        
        fig.add_trace(
            go.Scattergeo(
                lat=track_lats,
                lon=track_lons,
                mode="lines",
                line=dict(color="rgba(66, 217, 245, 0.5)", width=1.8, dash="dot"),
                name=f"{selected_record['name']} Track",
                hoverinfo="none",
            )
        )

        fig.add_trace(
            go.Scattergeo(
                lat=[selected_record["latitude"]],
                lon=[selected_record["longitude"]],
                mode="markers+text",
                text=[f"  🎯 {selected_record['name']}"],
                textposition="bottom right",
                textfont=dict(family="JetBrains Mono", size=11, color="#42D9F5"),
                marker=dict(
                    size=13,
                    color="#42D9F5",
                    symbol="circle",
                    line=dict(width=2, color="#ffffff"),
                ),
                name="Selected Target",
                hoverinfo="text",
                hovertext=[
                    f"<b>SELECTED TARGET: {selected_record['name']}</b><br/>"
                    f"Latitude: {selected_record['latitude']:.4f}°<br/>"
                    f"Longitude: {selected_record['longitude']:.4f}°<br/>"
                    f"Altitude: {selected_record['altitude_km']:,.1f} km<br/>"
                    f"Speed: {selected_record['speed_kms']:.2f} km/s<br/>"
                    f"Hazard Ratio: {selected_record['hazard_ratio']*100:.1f}%"
                ],
            )
        )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=385,
        paper_bgcolor="#080D17",
        plot_bgcolor="#080D17",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.02,
            xanchor="left",
            x=0.02,
            font=dict(family="JetBrains Mono", size=9, color="#94a3b8"),
            bgcolor="rgba(8, 13, 23, 0.85)",
            bordercolor="rgba(66, 217, 245, 0.2)",
            borderwidth=1,
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Telemetry Strip for Selected Target using clean sanitized HTML
    if selected_record:
        dist_color = '#FF647C' if selected_record['hazard_ratio'] > 0.6 else '#FFBD59'
        hazard_color = '#FF647C' if selected_record['hazard_ratio'] > 0.6 else '#45D6A0'

        hud_html = (
            f'<div style="background: #0B132B; border: 1px solid rgba(66, 217, 245, 0.2); border-radius: 6px; padding: 10px 14px; margin-top: 6px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; font-family: \'JetBrains Mono\', monospace; font-size: 0.72rem;">'
            f'<div>'
            f'<div style="color: #64748b; font-size: 0.65rem; text-transform: uppercase;">TARGET COORD</div>'
            f'<div style="color: #42D9F5; font-weight: 700; margin-top: 2px;">{selected_record["latitude"]:.2f}°, {selected_record["longitude"]:.2f}°</div>'
            f'</div>'
            f'<div>'
            f'<div style="color: #64748b; font-size: 0.65rem; text-transform: uppercase;">ALTITUDE</div>'
            f'<div style="color: #f8fafc; font-weight: 700; margin-top: 2px;">{selected_record["altitude_km"]:,.1f} km</div>'
            f'</div>'
            f'<div>'
            f'<div style="color: #64748b; font-size: 0.65rem; text-transform: uppercase;">ORBITAL VELOCITY</div>'
            f'<div style="color: #f8fafc; font-weight: 700; margin-top: 2px;">{selected_record["speed_kms"]:.2f} km/s</div>'
            f'</div>'
            f'<div>'
            f'<div style="color: #64748b; font-size: 0.65rem; text-transform: uppercase;">CORRIDOR RANGE</div>'
            f'<div style="color: {dist_color}; font-weight: 700; margin-top: 2px;">{selected_record["dist_to_storm_km"]:,.0f} km</div>'
            f'</div>'
            f'<div>'
            f'<div style="color: #64748b; font-size: 0.65rem; text-transform: uppercase;">HAZARD RATIO H_j</div>'
            f'<div style="color: {hazard_color}; font-weight: 700; margin-top: 2px;">{selected_record["hazard_ratio"]*100:.1f}%</div>'
            f'</div>'
            f'</div>'
        )
        render_html(hud_html)
