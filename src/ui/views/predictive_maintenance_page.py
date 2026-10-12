"""
SPARC-PM: Predictive Maintenance & 72h Failure Risk Page
=========================================================
PyTorch 1D-CNN + LSTM component failure probability P_fail forecast conditioned on
space weather stress. Features direct 'ADD TO A* QUEUE' action dispatcher.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui.components.kpi_cards import render_kpi_card
from src.ui.components.mission_header import render_mission_header
from src.ui.components.status_badge import render_status_badge


def render_predictive_maintenance_page() -> None:
    """Renders the Predictive Maintenance page."""
    render_mission_header(
        page_title="SPARC-PM : PREDICTIVE MAINTENANCE & SUBSYSTEM DEGRADATION",
        subtitle="PyTorch 1D-CNN + LSTM 72-Hour Failure Probability P_fail Forecast",
    )

    results = st.session_state.get("pipeline_results", {})
    maint = results.get("fleet_maintenance", [])
    df_m = pd.DataFrame(maint)

    if df_m.empty:
        st.warning("No maintenance telemetry available.")
        return

    high_risk_count = len(df_m[df_m["p_fail_72h"] >= 0.70])
    elev_risk_count = len(df_m[(df_m["p_fail_72h"] >= 0.40) & (df_m["p_fail_72h"] < 0.70)])
    opt_count = len(df_m[df_m["p_fail_72h"] < 0.20])

    # KPI Breakdown
    p1, p2, p3 = st.columns(3)
    with p1:
        render_kpi_card("Critical Degradation (P_fail ≥ 0.70)", f"{high_risk_count} Satellites", "Immediate Overhaul", "CRITICAL", "CRITICAL")
    with p2:
        render_kpi_card("Elevated Risk (0.40 ≤ P_fail < 0.70)", f"{elev_risk_count} Satellites", "Schedule Maintenance", "WARNING", "WARNING")
    with p3:
        render_kpi_card("Optimal Subsystem Health (P_fail < 0.20)", f"{opt_count} Satellites", "Nominal Routine", "NOMINAL", "NOMINAL")

    st.write("")

    # Top At-Risk Component Failure Forecast Chart
    top_assets = df_m.head(10)

    with st.container(border=True):
        st.markdown(
            '<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.95rem; color: #f8fafc; text-transform: uppercase; margin-bottom: 8px;">'
            '📊 TOP-10 HIGHEST 72-HOUR COMPONENT FAILURE PROBABILITY'
            '</div>',
            unsafe_allow_html=True,
        )

        fig_top = px.bar(
            top_assets,
            x="sat_id",
            y="p_fail_72h",
            color="p_fail_72h",
            color_continuous_scale="Reds",
            labels={"p_fail_72h": "Failure Probability P_fail", "sat_id": "Spacecraft ID"},
        )
        fig_top.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(15, 23, 42, 0.9)",
            plot_bgcolor="rgba(15, 23, 42, 0.9)",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_top, use_container_width=True)

    st.write("")

    # Operational Dispatch Table with [ ADD TO A* QUEUE ] Button
    with st.container(border=True):
        st.markdown(
            '<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.95rem; color: #f8fafc; text-transform: uppercase; margin-bottom: 8px;">'
            '🛠️ OPERATIONAL SUBSYSTEM DISPATCH & MAINTENANCE ACTIONS'
            '</div>',
            unsafe_allow_html=True,
        )

        for idx, row in top_assets.iterrows():
            sat_id = row["sat_id"]
            p_fail = row["p_fail_72h"]
            status = row["health_status"]

            rec_act = "ENTER_SAFE_MODE" if p_fail >= 0.70 else "POWER_DOWN_PAYLOAD" if p_fail >= 0.40 else "ENHANCED_TELEMETRY_POLL"
            urgency = "CRITICAL" if p_fail >= 0.70 else "WARNING" if p_fail >= 0.40 else "NOMINAL"

            col_sat, col_risk, col_act = st.columns([2, 2, 1.5])
            with col_sat:
                st.markdown(f"**{sat_id}** | Status: {render_status_badge(status, urgency)}", unsafe_allow_html=True)
                st.markdown(f"Battery: `{row['battery_voltage_v']}V` | Temp: `{row['subsystem_temp_c']}°C` | Gyro: `{row['gyro_drift_deg_hr']}°/hr`")
            with col_risk:
                st.markdown(f"72h Failure Risk P_fail: **{p_fail:.4f}**")
                st.markdown(f"Recommended Response: `{rec_act}`")
            with col_act:
                if st.button(f"➕ ADD TO A* QUEUE", key=f"btn_maint_queue_{sat_id}"):
                    queue = st.session_state.get("manual_command_queue", [])
                    queue.append({
                        "satellite": sat_id,
                        "action": rec_act,
                        "urgency": urgency,
                        "timestamp": results.get("timestamp", "NOW"),
                    })
                    st.session_state["manual_command_queue"] = queue
                    st.success(f"✅ Telecommand [{rec_act}] queued for {sat_id}!")

            st.markdown("<hr style='border:none; border-top:1px solid #1e293b; margin: 8px 0;'/>", unsafe_allow_html=True)
