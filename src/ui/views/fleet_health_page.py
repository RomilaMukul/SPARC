"""
SPARC-PM: Spacecraft Fleet Operations & Health Page
===================================================
Provides constellation-wide telemetry, alert distributions, component degradation,
and direct routing to Orbital Monitor & Command Center for selected spacecraft.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui.components.kpi_cards import render_kpi_card
from src.ui.components.mission_header import render_mission_header
from src.ui.components.status_badge import render_status_badge


def render_fleet_health_page() -> None:
    """Renders the Fleet Health & Operations page."""
    render_mission_header(
        page_title="SPARC-PM : SPACECRAFT FLEET OPERATIONS & HEALTH",
        subtitle="ISRO Active Constellation Telemetry • Subsystem Health • Multi-Sensor Diagnostics",
    )

    results = st.session_state.get("pipeline_results", {})
    haz = results.get("hazard_report", {})
    maint = results.get("fleet_maintenance", [])

    total_sats = haz.get("total_satellites", 50)
    crit_count = haz.get("critical_count", 0)
    warn_count = haz.get("warning_count", 0)
    elev_count = haz.get("elevated_count", 0)
    nom_count = haz.get("nominal_count", total_sats - (crit_count + warn_count + elev_count))

    # KPI Breakdown Row
    f1, f2, f3, f4, f5 = st.columns(5)

    with f1:
        render_kpi_card("Total Tracked", f"{total_sats} Satellites", "ISRO Fleet", "INFO")
    with f2:
        render_kpi_card("Critical Risk", f"{crit_count}", "Immediate Action Required", "CRITICAL", "CRITICAL")
    with f3:
        render_kpi_card("Warning Risk", f"{warn_count}", "Elevated Stress", "WARNING", "WARNING")
    with f4:
        render_kpi_card("Elevated Risk", f"{elev_count}", "Proximity Hazard", "INFO", "ELEVATED")
    with f5:
        render_kpi_card("Nominal", f"{nom_count}", "Optimal Operations", "NOMINAL", "NOMINAL")

    st.write("")

    # Constellation Subsystem Maintenance & Telemetry Dataframe
    df_m = pd.DataFrame(maint)

    with st.container(border=True):
        st.markdown(
            '<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.95rem; color: #f8fafc; text-transform: uppercase; margin-bottom: 8px;">'
            '📊 CONSTELLATION MULTI-SENSOR HOUSEKEEPING DIAGNOSTICS'
            '</div>',
            unsafe_allow_html=True,
        )

        if not df_m.empty:
            st.dataframe(
                df_m[["sat_id", "p_fail_72h", "health_status", "battery_voltage_v", "subsystem_temp_c", "gyro_drift_deg_hr", "dosimeter_count"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "sat_id": "Spacecraft ID",
                    "p_fail_72h": st.column_config.ProgressColumn("72h Failure Risk", min_value=0.0, max_value=1.0, format="%.4f"),
                    "health_status": "Health State",
                    "battery_voltage_v": st.column_config.NumberColumn("Battery Voltage (V)", format="%.2f"),
                    "subsystem_temp_c": st.column_config.NumberColumn("Subsystem Temp (°C)", format="%.1f"),
                    "gyro_drift_deg_hr": st.column_config.NumberColumn("Gyro Drift (°/hr)", format="%.4f"),
                    "dosimeter_count": st.column_config.NumberColumn("Dosimeter (counts)", format="%.1f"),
                },
            )
