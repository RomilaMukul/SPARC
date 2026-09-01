"""
Module: 3D Orbital Fleet & Hazard Corridor Visualization (Plotly)

Renders an interactive 3D Earth sphere with real-time SGP4 satellite position markers
and translucent 3D storm hazard corridors (South Atlantic Anomaly & Auroral Ovals)
scaled by live Naive Bayes space weather severity.

Wireframe alignment: docs/wireframes/03_3d_fleet_hazard.svg
"""

import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from orbital_position import latlonalt_to_ecef, EARTH_RADIUS_KM, STORM_CORRIDORS, SEVERITY_RADIUS_MULTIPLIER


def create_earth_sphere(resolution: int = 50):
    """Generate 3D mesh sphere coordinates for Earth in ECEF frame (km)."""
    phi = np.linspace(0, np.pi, resolution)
    theta = np.linspace(0, 2 * np.pi, resolution)
    phi, theta = np.meshgrid(phi, theta)

    r = EARTH_RADIUS_KM
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)

    # 3D surface trace representing Earth
    earth_surface = go.Surface(
        x=x, y=y, z=z,
        colorscale=[
            [0.0, "#081b33"],
            [0.5, "#0e2f56"],
            [1.0, "#194a82"]
        ],
        showscale=False,
        opacity=0.88,
        hoverinfo="none",
        name="Earth (ECEF Frame)"
    )
    return earth_surface


def create_storm_corridor_sphere(corridor: dict, severity: str = "Watch", resolution: int = 30):
    """Generate translucent 3D sphere mesh representing space weather storm corridors."""
    multiplier = SEVERITY_RADIUS_MULTIPLIER.get(severity, 1.0)
    radius_km = corridor["base_radius_km"] * multiplier
    center_ecef = latlonalt_to_ecef(corridor["lat"], corridor["lon"], alt_km=500.0)

    phi = np.linspace(0, np.pi, resolution)
    theta = np.linspace(0, 2 * np.pi, resolution)
    phi, theta = np.meshgrid(phi, theta)

    x = center_ecef[0] + radius_km * np.sin(phi) * np.cos(theta)
    y = center_ecef[1] + radius_km * np.sin(phi) * np.sin(theta)
    z = center_ecef[2] + radius_km * np.cos(phi)

    if "SAA" in corridor["name"] or "South Atlantic" in corridor["name"]:
        color = "#FF0055"  # High radiation anomaly
    else:
        color = "#FF9900"  # Auroral precipitation oval

    mesh = go.Mesh3d(
        x=x.flatten(),
        y=y.flatten(),
        z=z.flatten(),
        color=color,
        opacity=0.22,
        alphahull=0,
        name=f"Hazard: {corridor['name']} ({radius_km:.0f} km)",
        hoverinfo="name"
    )
    return mesh


def generate_3d_fleet_hazard_globe(risk_df: pd.DataFrame, severity: str = "Watch") -> go.Figure:
    """Build complete 3D Plotly visualization figure according to wireframe 03_3d_fleet_hazard.svg."""
    fig = go.Figure()

    # 1. Add Earth Sphere
    fig.add_trace(create_earth_sphere())

    # 2. Add Storm Corridors (translucent 3D volumes)
    for corridor in STORM_CORRIDORS:
        fig.add_trace(create_storm_corridor_sphere(corridor, severity=severity))

    # 3. Add Satellite Markers grouped by Risk Level
    if not risk_df.empty:
        color_map = {
            "CRITICAL": "#FF0055",
            "WARNING": "#FF9900",
            "NOMINAL": "#00FF66"
        }

        for risk_lvl, color in color_map.items():
            sub_df = risk_df[risk_df["risk_level"] == risk_lvl]
            if sub_df.empty:
                continue

            ecef_coords = []
            hover_texts = []
            for _, row in sub_df.iterrows():
                pos = latlonalt_to_ecef(row["lat"], row["lon"], row["alt_km"])
                ecef_coords.append(pos)
                hover_texts.append(
                    f"<b>{row['name']}</b> (NORAD {row['norad_id']})<br/>"
                    f"Latitude: {row['lat']}° | Longitude: {row['lon']}°<br/>"
                    f"Altitude: {row['alt_km']} km<br/>"
                    f"Risk Status: <b>{row['risk_level']}</b><br/>"
                    f"Nearest Corridor: {row['nearest_corridor']} ({row['distance_km']} km)"
                )

            if ecef_coords:
                ecef_arr = np.array(ecef_coords)
                fig.add_trace(
                    go.Scatter3d(
                        x=ecef_arr[:, 0],
                        y=ecef_arr[:, 1],
                        z=ecef_arr[:, 2],
                        mode="markers+text",
                        name=f"Satellites ({risk_lvl})",
                        text=sub_df["name"],
                        textposition="top center",
                        textfont=dict(size=9, color=color),
                        hoverinfo="text",
                        hovertext=hover_texts,
                        marker=dict(
                            size=7 if risk_lvl == "CRITICAL" else 5,
                            color=color,
                            symbol="diamond" if risk_lvl == "CRITICAL" else "circle",
                            line=dict(color="#ffffff", width=1),
                            opacity=0.95
                        )
                    )
                )

    # 4. Set 3D Layout
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15,23,42,0.95)",
        plot_bgcolor="rgba(15,23,42,0.95)",
        title=dict(
            text=f"3D Orbital Fleet Hazard Map & Storm Corridors (Severity: {severity.upper()})",
            font=dict(family="Inter, sans-serif", size=15, color="#f8fafc")
        ),
        scene=dict(
            xaxis=dict(title="ECEF X (km)", showgrid=True, gridcolor="rgba(148,163,184,0.2)", backgroundcolor="#0f172a"),
            yaxis=dict(title="ECEF Y (km)", showgrid=True, gridcolor="rgba(148,163,184,0.2)", backgroundcolor="#0f172a"),
            zaxis=dict(title="ECEF Z (km)", showgrid=True, gridcolor="rgba(148,163,184,0.2)", backgroundcolor="#0f172a"),
            camera=dict(
                eye=dict(x=1.8, y=1.8, z=1.2)
            ),
            aspectmode="cube"
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(
            font=dict(family="Roboto Mono, monospace", size=11, color="#e2e8f0"),
            bgcolor="rgba(30,41,59,0.8)",
            bordercolor="rgba(148,163,184,0.3)",
            borderwidth=1
        )
    )

    return fig


if __name__ == "__main__":
    from orbital_position import compute_fleet_risk
    df_risk = compute_fleet_risk(severity="Warning")
    fig = generate_3d_fleet_hazard_globe(df_risk, severity="Warning")
    print("Created 3D Plotly Globe Figure.")
