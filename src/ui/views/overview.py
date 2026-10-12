"""
SPARC-PM: Operations Overview Page
==================================
Landing page for mission control. Communicates current space weather severity,
crew risk, fleet risk, affected spacecraft, operational constraints, priority events,
next recommended response, and a compact orbital situation view.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.ui.components.kpi_cards import render_kpi_card
from src.ui.components.mission_header import render_mission_header
from src.ui.components.scenario_simulator import render_scenario_simulator
from src.ui.components.status_badge import render_status_badge, render_led
from src.ui.components.why_panel import render_why_panel


def render_overview_page() -> None:
    """Renders the Operations Overview landing page."""
    render_mission_header(
        page_title="SPARC-PM : OPERATIONS OVERVIEW",
        subtitle="ISRO Mission Operations Center (ISTRAC / MCF) • Space Weather Alert & Response System",
    )

    # 1. Interactive Scenario Simulator (Top Control)
    render_scenario_simulator()

    results = st.session_state.get("pipeline_results", {})
    if not results:
        st.warning("Pipeline results not initialized.")
        return

    sev = results.get("severity_report", {})
    dos = results.get("dosimetry_report", {})
    haz = results.get("hazard_report", {})
    maint = results.get("fleet_maintenance", [])
    cmds = results.get("scheduled_commands", {})
    telemetry = results.get("telemetry", {})

    triage = sev.get("triage", "GREEN")

    # 2. Executive Status KPIs Row
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        render_kpi_card(
            label="Space Weather Level",
            value=sev.get("severity_label", "G0_NOMINAL_QUIET"),
            subtext=f"FSM Triage: {triage}",
            status_level=triage,
            badge_text=triage,
        )
    with k2:
        render_kpi_card(
            label="Crew Radiation Rate",
            value=f"{dos.get('peak_dose_rate_usv_hr', 0.0):.1f} μSv/hr",
            subtext=f"EVA Clearance: {dos.get('eva_status', 'N/A')}",
            status_level=dos.get("alert_color", "GREEN"),
            badge_text=dos.get("alert_color", "GREEN"),
        )
    with k3:
        render_kpi_card(
            label="High Hazard Spacecraft",
            value=f"{haz.get('critical_count', 0)} / {haz.get('total_satellites', 50)}",
            subtext=f"{haz.get('warning_count', 0)} Elevated Proximate Assets",
            status_level="CRITICAL" if haz.get("critical_count", 0) > 0 else "NOMINAL",
            badge_text="CRITICAL" if haz.get("critical_count", 0) > 0 else "NOMINAL",
        )
    with k4:
        queue_len = len(cmds.get("command_queue", []))
        render_kpi_card(
            label="Queued Telecommands",
            value=f"{queue_len} Commands",
            subtext=f"Allocated Power: {cmds.get('allocated_power_w', 0)} W",
            status_level="WARNING" if queue_len > 0 else "NOMINAL",
            badge_text="SCHEDULED" if queue_len > 0 else "NOMINAL",
        )

    st.write("")

    # 3. Active Operations & Recommended Response Banner
    triage_action = sev.get("action", "NOMINAL_OPERATIONS")
    triage_desc = sev.get("action_description", "")
    border_triage = '#ef4444' if triage == 'RED' else '#f59e0b' if triage == 'YELLOW' else '#10b981'

    st.markdown(
        f'<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 4px solid {border_triage}; border-radius: 6px; padding: 14px 16px; margin-bottom: 16px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center;">'
        f'<span style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 1.0rem; color: #f8fafc;">'
        f'{render_led(triage)} GROUND DIRECTIVE & RECOMMENDED RESPONSE: {triage_action}'
        f'</span>'
        f'{render_status_badge(triage_action, triage)}'
        f'</div>'
        f'<div style="font-family: \'Space Mono\', monospace; font-size: 0.82rem; color: #cbd5e1; margin-top: 6px;">'
        f'<b>Directive Details:</b> {triage_desc} | <b>Crew Guidance:</b> {dos.get("crew_action", "N/A")}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 4. Main 2-Column Dashboard Split
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        # Compact Orbital Situation View
        with st.container(border=True):
            st.markdown(
                '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
                '<span style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.9rem; color: #f8fafc; text-transform: uppercase;">'
                '🌐 COMPACT ORBITAL SITUATION VIEW'
                '</span>'
                '<span style="font-family: \'Space Mono\', monospace; font-size: 0.72rem; color: #60a5fa;">'
                'Click \'Orbital Monitor\' in sidebar for full 3D view'
                '</span>'
                '</div>',
                unsafe_allow_html=True,
            )

            fleet_table = pd.DataFrame(haz.get("fleet_hazard_profile", []))
            if not fleet_table.empty:
                fig_compact = px.scatter(
                    fleet_table,
                    x="longitude",
                    y="latitude",
                    color="alert_level",
                    size="hazard_ratio",
                    hover_name="name",
                    hover_data=["altitude_km", "dist_to_storm_km", "alert_level"],
                    color_discrete_map={"CRITICAL": "#ef4444", "WARNING": "#f59e0b", "ELEVATED": "#3b82f6", "NOMINAL": "#10b981"},
                    title=None,
                )
                fig_compact.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(15, 23, 42, 0.9)",
                    plot_bgcolor="rgba(15, 23, 42, 0.9)",
                    height=260,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(title="Longitude (°)", range=[-180, 180]),
                    yaxis=dict(title="Latitude (°)", range=[-90, 90]),
                    showlegend=True,
                    legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0.5)"),
                )
                st.plotly_chart(fig_compact, use_container_width=True)

    with col_right:
        # Bayesian Severity Posterior Distribution Chart
        with st.container(border=True):
            st.markdown(
                '<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.9rem; color: #f8fafc; text-transform: uppercase; margin-bottom: 8px;">'
                '🎯 SEVERITY POSTERIOR PROBABILITY'
                '</div>',
                unsafe_allow_html=True,
            )

            prob_df = pd.DataFrame([
                {"Severity Class": k, "Posterior (%)": v * 100.0}
                for k, v in sev.get("probabilities", {}).items()
            ])
            fig_prob = px.bar(
                prob_df,
                x="Severity Class",
                y="Posterior (%)",
                color="Posterior (%)",
                color_continuous_scale="Blues",
                text_auto=".1f",
            )
            fig_prob.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(15, 23, 42, 0.9)",
                plot_bgcolor="rgba(15, 23, 42, 0.9)",
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_prob, use_container_width=True)

    # 5. High-Risk Spacecraft Table Summary
    with st.container(border=True):
        st.markdown(
            '<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.95rem; color: #f8fafc; text-transform: uppercase; margin-bottom: 8px;">'
            '📋 TOP AT-RISK SPACECRAFT & FLEET HAZARDS'
            '</div>',
            unsafe_allow_html=True,
        )

        fleet_table = pd.DataFrame(haz.get("fleet_hazard_profile", []))
        if not fleet_table.empty:
            top_risk = fleet_table.head(8)
            st.dataframe(
                top_risk[["name", "orbit_type", "altitude_km", "dist_to_storm_km", "hazard_ratio", "alert_level"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "name": "Spacecraft Name",
                    "orbit_type": "Orbit Type",
                    "altitude_km": st.column_config.NumberColumn("Altitude (km)", format="%.1f"),
                    "dist_to_storm_km": st.column_config.NumberColumn("Distance to Corridor (km)", format="%.1f"),
                    "hazard_ratio": st.column_config.ProgressColumn("Hazard Ratio H_j", min_value=0.0, max_value=1.0, format="%.4f"),
                    "alert_level": "Alert Status",
                },
            )
