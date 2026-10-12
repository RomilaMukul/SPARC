"""
SPARC-PM: Gaganyaan Crew Radiation Dosimetry Page
=================================================
Monitors human astronaut radiation exposure inside the Gaganyaan crew module
behind 3.5 g/cm² Aluminum equivalent shielding using PyTorch LSTM forecasting.
"""

import plotly.graph_objects as go
import streamlit as st

from src.models.crew_dosimetry import (
    EVA_CAUTION_THRESHOLD_USV_HR,
    EVA_SAFE_THRESHOLD_USV_HR,
    GAGANYAAN_SHIELDING_G_CM2,
    MISSION_CAREER_LIMIT_MSV,
    SHELTER_ALERT_THRESHOLD_USV_HR,
)
from src.ui.components.kpi_cards import render_kpi_card
from src.ui.components.mission_header import render_mission_header
from src.ui.components.status_badge import render_status_badge


def render_crew_dosimetry_page() -> None:
    """Renders the Gaganyaan Crew Dosimetry page."""
    render_mission_header(
        page_title="SPARC-PM : GAGANYAAN CREW DOSIMETRY & RADIATION FORECAST",
        subtitle="PyTorch LSTM 6-Hour Solar Proton Flux Projection • Absorbed Dose behind 3.5 g/cm² Al Shielding",
    )

    results = st.session_state.get("pipeline_results", {})
    dos = results.get("dosimetry_report", {})
    telemetry = results.get("telemetry", {})

    alert_color = dos.get("alert_color", "GREEN")

    # KPI Metrics Row
    d1, d2, d3, d4 = st.columns(4)

    with d1:
        render_kpi_card(
            label="Peak Cabin Dose Rate",
            value=f"{dos.get('peak_dose_rate_usv_hr', 0.0):.1f} μSv/hr",
            subtext=f"Proton Flux: {telemetry.get('proton_flux_pfu', 0.0):.1f} pfu",
            status_level=alert_color,
            badge_text=alert_color,
        )
    with d2:
        render_kpi_card(
            label="6h Cumulative Dose",
            value=f"{dos.get('total_6h_dose_msv', 0.0):.4f} mSv",
            subtext="Absorbed Energy: 0.145 Attenuation",
            status_level=alert_color,
        )
    with d3:
        render_kpi_card(
            label="Career Limit Budget",
            value=f"{dos.get('career_limit_percentage', 0.0):.2f}%",
            subtext=f"Limit: {MISSION_CAREER_LIMIT_MSV:.1f} mSv (ISRO/NASA)",
            status_level="WARNING" if dos.get("career_limit_percentage", 0.0) > 10 else "NOMINAL",
        )
    with d4:
        render_kpi_card(
            label="EVA Clearance State",
            value=dos.get("eva_status", "NOMINAL"),
            subtext="Threshold: 50.0 μSv/hr Safe Limit",
            status_level=alert_color,
            badge_text=dos.get("eva_status", "NOMINAL"),
        )

    st.write("")

    # Crew Directive Banner
    border_col = '#ef4444' if alert_color == 'RED' else '#10b981'
    st.markdown(
        f'<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 4px solid {border_col}; border-radius: 6px; padding: 14px 16px; margin-bottom: 16px;">'
        f'<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 1.0rem; color: #f8fafc;">'
        f'👨‍🚀 GAGANYAAN FLIGHT DIRECTIVE: {dos.get("crew_action", "N/A")}'
        f'</div>'
        f'<div style="font-family: \'Space Mono\', monospace; font-size: 0.82rem; color: #cbd5e1; margin-top: 6px;">'
        f'<b>Guidance:</b> {dos.get("action_guidance", "")} | <b>Shielding Context:</b> {GAGANYAAN_SHIELDING_G_CM2} g/cm² Aluminum'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 6-Hour High Resolution Plotly Forecast Chart
    with st.container(border=True):
        st.markdown(
            '<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.95rem; color: #f8fafc; text-transform: uppercase; margin-bottom: 8px;">'
            '📈 PYTORCH LSTM 6-HOUR RADIATION FORECAST CURVE'
            '</div>',
            unsafe_allow_html=True,
        )

        timestamps = [f"+{int(m)}m" for m in dos.get("timestamps_min", [])]
        dose_rates = dos.get("dose_rate_usv_hr", [])
        forecast_flux = dos.get("forecast_flux_pfu", [])

        fig_dos = go.Figure()

        fig_dos.add_trace(go.Scatter(
            x=timestamps,
            y=dose_rates,
            mode="lines+markers",
            name="Cabin Dose Rate (μSv/hr)",
            line=dict(color="#60a5fa", width=3),
            fill="tozeroy",
            fillcolor="rgba(96, 165, 250, 0.1)",
        ))

        fig_dos.add_trace(go.Scatter(
            x=timestamps,
            y=forecast_flux,
            mode="lines",
            name="External Solar Proton Flux (pfu)",
            line=dict(color="#fbbf24", width=2, dash="dash"),
            yaxis="y2",
        ))

        # Threshold Lines
        fig_dos.add_hline(y=EVA_SAFE_THRESHOLD_USV_HR, line_dash="dot", line_color="#10b981", annotation_text="EVA Safe Limit (50 μSv/hr)")
        fig_dos.add_hline(y=EVA_CAUTION_THRESHOLD_USV_HR, line_dash="dot", line_color="#ef4444", annotation_text="EVA Abort Threshold (250 μSv/hr)")

        fig_dos.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(15, 23, 42, 0.9)",
            plot_bgcolor="rgba(15, 23, 42, 0.9)",
            height=400,
            margin=dict(l=40, r=40, t=30, b=30),
            yaxis=dict(title="Cabin Dose Rate (μSv/hr)", color="#60a5fa"),
            yaxis2=dict(title="Proton Flux (pfu)", color="#fbbf24", overlaying="y", side="right"),
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0.5)"),
        )

        st.plotly_chart(fig_dos, use_container_width=True)
