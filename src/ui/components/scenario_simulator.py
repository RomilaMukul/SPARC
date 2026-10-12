"""
SPARC-PM: Interactive Scenario Simulator Component
===================================================
First-class simulation control panel for loading space weather event presets,
modifying physical sensor feeds, and triggering end-to-end pipeline execution.
"""

from __future__ import annotations

from typing import Any, Dict
import streamlit as st

from src.ui.pipeline import SCENARIOS, execute_pipeline
from src.ui.components.html_utils import render_html
from src.ui.components.status_badge import render_status_badge


def render_scenario_simulator() -> None:
    """Renders the Scenario Simulator control interface and execution flow."""
    with st.container(border=True):
        render_html("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="font-family: 'Inter', sans-serif; font-weight: 700; font-size: 0.95rem; color: #f8fafc; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; gap: 8px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#42D9F5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                        <polyline points="2 17 12 22 22 17"></polyline>
                        <polyline points="2 12 12 17 22 12"></polyline>
                    </svg>
                    SCENARIO SIMULATOR & SPACE WEATHER INGEST
                </div>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #42D9F5; background: rgba(66, 217, 245, 0.1); border: 1px solid rgba(66, 217, 245, 0.3); padding: 2px 8px; border-radius: 4px; font-weight: 700;">
                    LIVE INGEST ENGINE
                </span>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #94a3b8; margin-bottom: 14px;">
                Inject Space Weather Telemetry vectors into the 5-tier SPARC predictive pipeline.
            </div>
        """)

        scen_keys = list(SCENARIOS.keys()) + ["CUSTOM TELEMETRY OVERRIDE"]

        col_sel, col_btn = st.columns([3, 1])

        with col_sel:
            render_html("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; font-weight: 700; color: #42D9F5; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#42D9F5" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    SELECT SPACE WEATHER EVENT PRESET:
                </div>
            """)
            selected_scen = st.selectbox(
                "Select Space Weather Event Preset:",
                scen_keys,
                index=3,  # Default G3_SEVERE
                key="scen_simulator_select",
                label_visibility="collapsed",
            )

        # Initialize sliders if custom or preset selected
        if selected_scen == "CUSTOM TELEMETRY OVERRIDE":
            preset_vals = {
                "proton_flux_pfu": 150.0,
                "proton_speed_kms": 640.0,
                "mag_bz_field": -14.5,
                "proton_density_cm3": 12.5,
                "solar_wind_dyn_pressure_npa": 4.8,
            }
        else:
            preset_vals = SCENARIOS[selected_scen]

        with st.expander("🛠️ Inspect & Modify Aditya-L1 / DSN Sensor Feeds", expanded=(selected_scen == "CUSTOM TELEMETRY OVERRIDE")):
            if selected_scen != "CUSTOM TELEMETRY OVERRIDE":
                st.info(f"**Scenario Description:** {preset_vals['description']}")

            c1, c2, c3 = st.columns(3)
            with c1:
                flux_val = st.slider("Solar Proton Flux (pfu)", 0.1, 3000.0, float(preset_vals["proton_flux_pfu"]), step=1.0, key="sim_flux")
                speed_val = st.slider("Solar Wind Velocity (km/s)", 250.0, 1200.0, float(preset_vals["proton_speed_kms"]), step=10.0, key="sim_speed")
            with c2:
                bz_val = st.slider("IMF Bz Field (nT)", -50.0, 30.0, float(preset_vals["mag_bz_field"]), step=0.5, key="sim_bz")
                density_val = st.slider("Proton Density (cm⁻³)", 1.0, 60.0, float(preset_vals["proton_density_cm3"]), step=0.5, key="sim_density")
            with c3:
                pressure_val = st.slider("Dynamic Pressure (nPa)", 0.5, 30.0, float(preset_vals["solar_wind_dyn_pressure_npa"]), step=0.5, key="sim_pressure")

        active_telemetry = {
            "proton_flux_pfu": flux_val if "sim_flux" in st.session_state else preset_vals["proton_flux_pfu"],
            "proton_speed_kms": speed_val if "sim_speed" in st.session_state else preset_vals["proton_speed_kms"],
            "mag_bz_field": bz_val if "sim_bz" in st.session_state else preset_vals["mag_bz_field"],
            "proton_density_cm3": density_val if "sim_density" in st.session_state else preset_vals["proton_density_cm3"],
            "solar_wind_dyn_pressure_npa": pressure_val if "sim_pressure" in st.session_state else preset_vals["solar_wind_dyn_pressure_npa"],
        }

        with col_btn:
            render_html("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; font-weight: 700; color: transparent; margin-bottom: 6px;">
                    EXECUTE
                </div>
            """)
            if st.button("🚀 RUN SIMULATION", use_container_width=True, type="primary", key="btn_run_sim"):
                with st.spinner("Executing 5-Engine Pipeline..."):
                    results = execute_pipeline(active_telemetry, selected_scen)
                    st.session_state["pipeline_results"] = results
                    st.success(f"Pipeline executed in {results['pipeline_latency_ms']} ms!")

        # Pipeline Flow Visualizer Component
        st.write("")
        render_pipeline_flow_diagram()


def render_pipeline_flow_diagram() -> None:
    """Renders the step-by-step pipeline execution flow visualizer."""
    results = st.session_state.get("pipeline_results", {})
    lat = results.get("pipeline_latency_ms", "N/A")

    render_html(f"""
        <div style="background: #1e293b; border-radius: 4px; padding: 10px 14px; font-family: 'Space Mono', monospace; font-size: 0.75rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; color: #94a3b8; margin-bottom: 6px;">
                <span>PIPELINE EXECUTION GRAPH</span>
                <span style="color: #34d399;">TOTAL LATENCY: {lat} ms</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; color: #e2e8f0; text-align: center; flex-wrap: wrap; gap: 4px;">
                <span style="background: #0f172a; padding: 4px 8px; border-radius: 4px; border: 1px solid #334155;">1. Telemetry Ingest</span>
                <span style="color: #64748b;">➔</span>
                <span style="background: #0f172a; padding: 4px 8px; border-radius: 4px; border: 1px solid #334155;">2. Severity Classifier</span>
                <span style="color: #64748b;">➔</span>
                <span style="background: #0f172a; padding: 4px 8px; border-radius: 4px; border: 1px solid #334155;">3. Crew Dosimetry</span>
                <span style="color: #64748b;">➔</span>
                <span style="background: #0f172a; padding: 4px 8px; border-radius: 4px; border: 1px solid #334155;">4. Spatial Hazard</span>
                <span style="color: #64748b;">➔</span>
                <span style="background: #0f172a; padding: 4px 8px; border-radius: 4px; border: 1px solid #334155;">5. Predictive Maint</span>
                <span style="color: #64748b;">➔</span>
                <span style="background: #0f172a; padding: 4px 8px; border-radius: 4px; border: 1px solid #334155;">6. A* Scheduler</span>
                <span style="color: #64748b;">➔</span>
                <span style="background: #064e3b; color: #34d399; padding: 4px 8px; border-radius: 4px; border: 1px solid #10b981;">7. Command Queue</span>
            </div>
        </div>
    """)
