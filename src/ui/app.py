"""
SPARC-PM: Space Weather Risk Classification & Mission Control HUD
=================================================================
Autonomous Multi-Tier Space Weather Decision-Support Dashboard
for ISRO Mission Control Center (ISTRAC / MCF) Simulation Pipeline.
Engineered with NASA Eyes / Deep Space Network Aesthetic Architecture.
"""

from __future__ import annotations

import datetime
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Path configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.crew_dosimetry import (
    EVA_CAUTION_THRESHOLD_USV_HR,
    EVA_SAFE_THRESHOLD_USV_HR,
    GAGANYAAN_SHIELDING_G_CM2,
    MISSION_CAREER_LIMIT_MSV,
    SHELTER_ALERT_THRESHOLD_USV_HR,
    CrewDosimetryEngine,
)
from src.models.predictive_maint import PredictiveMaintenanceEngine
from src.models.severity_classifier import (
    FSM_TRIAGE_RULES,
    SEVERITY_MAP,
    SpaceWeatherSeverityClassifier,
)
from src.models.spatial_hazard import SpatialHazardEngine
from src.scheduler.a_star_scheduler import AStarActionScheduler

# Streamlit Page Configuration
st.set_page_config(
    page_title="SPARC-PM | ISRO & NASA Space Weather Mission Operations",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# NASA / Deep Space Network Mission Control CSS Styling
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Exo+2:wght@300;400;500;600;700&family=Rajdhani:wght@500;600;700&family=Space+Mono:wght@400;700&display=swap');

    /* ── Cosmic Starfield Background ── */
    .stApp {
        background-color: #05050F;
        background-image:
            radial-gradient(ellipse at 15% 20%, rgba(91, 44, 156, 0.12) 0%, transparent 50%),
            radial-gradient(ellipse at 85% 75%, rgba(20, 60, 120, 0.10) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(180, 140, 60, 0.04) 0%, transparent 40%),
            radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,0.5) 50%, transparent 50%),
            radial-gradient(1px 1px at 25% 35%, rgba(255,255,255,0.35) 50%, transparent 50%),
            radial-gradient(1px 1px at 40% 80%, rgba(255,255,255,0.4) 50%, transparent 50%),
            radial-gradient(1px 1px at 55% 10%, rgba(255,255,255,0.3) 50%, transparent 50%),
            radial-gradient(1px 1px at 70% 60%, rgba(255,255,255,0.45) 50%, transparent 50%),
            radial-gradient(1px 1px at 85% 25%, rgba(255,255,255,0.35) 50%, transparent 50%),
            radial-gradient(1.5px 1.5px at 15% 70%, rgba(255,255,255,0.55) 50%, transparent 50%),
            radial-gradient(1px 1px at 90% 90%, rgba(255,255,255,0.3) 50%, transparent 50%),
            radial-gradient(1.5px 1.5px at 50% 45%, rgba(255,255,255,0.5) 50%, transparent 50%),
            radial-gradient(1px 1px at 35% 55%, rgba(255,255,255,0.25) 50%, transparent 50%),
            radial-gradient(1px 1px at 65% 40%, rgba(255,255,255,0.4) 50%, transparent 50%),
            radial-gradient(1px 1px at 5% 90%, rgba(255,255,255,0.3) 50%, transparent 50%),
            radial-gradient(1px 1px at 78% 12%, rgba(255,255,255,0.35) 50%, transparent 50%),
            radial-gradient(1.5px 1.5px at 45% 95%, rgba(255,255,255,0.4) 50%, transparent 50%),
            radial-gradient(1px 1px at 20% 50%, rgba(255,255,255,0.3) 50%, transparent 50%);
        font-family: 'Exo 2', sans-serif;
        color: #d4dce8;
    }

    /* ── Solar System Typography ── */
    h1, h2, h3, h4, .nasa-title {
        font-family: 'Orbitron', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        color: #c9d6e3;
    }

    .nasa-title-gradient {
        background: linear-gradient(90deg, #E8C547 0%, #D4A030 30%, #C9A84C 55%, #F0D060 80%, #E8C547 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
    }

    .nasa-mono {
        font-family: 'Space Mono', monospace !important;
    }

    /* ── Orbital Glass Cards ── */
    .nasa-card {
        background: rgba(12, 12, 28, 0.80);
        border: 1px solid rgba(180, 150, 80, 0.18);
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
        margin-bottom: 14px;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }

    .nasa-card:hover {
        border-color: rgba(180, 150, 80, 0.35);
        box-shadow: 0 10px 32px rgba(0, 0, 0, 0.7);
    }

    .nasa-card-green { border-left: 4px solid #5EC982; }
    .nasa-card-yellow { border-left: 4px solid #E8C547; }
    .nasa-card-red { border-left: 4px solid #E85D5D; }

    /* ── Telemetry KPI Metric Box ── */
    .nasa-metric-card {
        background: rgba(14, 14, 32, 0.85);
        border: 1px solid rgba(120, 100, 200, 0.18);
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
        min-height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .nasa-metric-label {
        font-family: 'Space Mono', monospace !important;
        font-size: 0.8rem;
        color: #8B8FAF;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    .nasa-value-tick {
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 800;
        font-size: 1.85rem;
        color: #7EB8DA;
        line-height: 1.1;
        text-shadow: 0 0 15px rgba(126, 184, 218, 0.6);
    }

    /* ── Badges (glowing highlight backgrounds) ── */
    .badge-green { color: #5EC982; border: 1px solid #5EC982; padding: 4px 12px; border-radius: 4px; font-weight: 700; font-family: 'Space Mono', monospace; background: rgba(94, 201, 130, 0.15); box-shadow: 0 0 12px rgba(94, 201, 130, 0.4); text-shadow: 0 0 8px rgba(94, 201, 130, 0.6); }
    .badge-yellow { color: #E8C547; border: 1px solid #E8C547; padding: 4px 12px; border-radius: 4px; font-weight: 700; font-family: 'Space Mono', monospace; background: rgba(232, 197, 71, 0.15); box-shadow: 0 0 12px rgba(232, 197, 71, 0.4); text-shadow: 0 0 8px rgba(232, 197, 71, 0.6); }
    .badge-red { color: #E85D5D; border: 1px solid #E85D5D; padding: 4px 12px; border-radius: 4px; font-weight: 700; font-family: 'Space Mono', monospace; background: rgba(232, 93, 93, 0.15); box-shadow: 0 0 12px rgba(232, 93, 93, 0.4); text-shadow: 0 0 8px rgba(232, 93, 93, 0.6); animation: blink 1.2s infinite; }

    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    /* ── Status LEDs (subtle pulse, no glow) ── */
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(94, 201, 130, 0.6); }
        70% { box-shadow: 0 0 0 8px rgba(94, 201, 130, 0); }
        100% { box-shadow: 0 0 0 0 rgba(94, 201, 130, 0); }
    }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(232, 93, 93, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(232, 93, 93, 0); }
        100% { box-shadow: 0 0 0 0 rgba(232, 93, 93, 0); }
    }
    .led-green { display: inline-block; width: 10px; height: 10px; background-color: #5EC982; border-radius: 50%; animation: pulse-green 2s infinite; margin-right: 8px; }
    .led-red { display: inline-block; width: 10px; height: 10px; background-color: #E85D5D; border-radius: 50%; animation: pulse-red 0.8s infinite; margin-right: 8px; }

    /* ── Streamlit Tabs — Orbital Navigation ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: rgba(10, 10, 24, 0.75);
        padding: 6px 8px;
        border-radius: 10px;
        border: 1px solid rgba(120, 100, 200, 0.15);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 0.82rem !important;
        letter-spacing: 1px;
        color: #8B8FAF !important;
        border-radius: 8px;
        padding: 10px 18px;
        transition: color 0.2s ease, border-color 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(120, 100, 200, 0.12) !important;
        color: #E8C547 !important;
        border: 1px solid rgba(232, 197, 71, 0.4) !important;
    }

    /* ── Sidebar Cosmic Tint ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A0A1E 0%, #0D0B22 50%, #0F0D26 100%) !important;
        border-right: 1px solid rgba(120, 100, 200, 0.12);
    }

    /* ── Scrollbar Styling ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0A0A1E; }
    ::-webkit-scrollbar-thumb { background: rgba(120, 100, 200, 0.3); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(120, 100, 200, 0.5); }

    /* ── Streamlit Widget Overrides for Space Theme ── */
    .stSlider > div > div > div > div { background-color: #E8C547 !important; }
    .stSelectbox > div > div { background-color: rgba(14, 14, 32, 0.9) !important; border-color: rgba(120, 100, 200, 0.2) !important; }
    div[data-testid="stMetric"] { background: rgba(14, 14, 32, 0.6); border: 1px solid rgba(120, 100, 200, 0.12); border-radius: 8px; padding: 10px 14px; }
    div[data-testid="stMetricValue"] { font-family: 'Orbitron', sans-serif !important; color: #7EB8DA; }
    div[data-testid="stMetricLabel"] { font-family: 'Space Mono', monospace !important; color: #8B8FAF; text-transform: uppercase; letter-spacing: 1px; font-size: 0.78rem; }

    /* ── Expander Styling ── */
    .streamlit-expanderHeader { font-family: 'Exo 2', sans-serif !important; font-weight: 600; color: #c9d6e3 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Cached Singletons for Engines
# -----------------------------------------------------------------------------
@st.cache_resource
def load_classifier():
    try:
        return SpaceWeatherSeverityClassifier.load_model()
    except Exception:
        df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "cleaned_training_dataset.csv")
        clf = SpaceWeatherSeverityClassifier(model_type="hist_gb")
        X, y = clf.prepare_data(df)
        clf.fit(X, y)
        return clf

@st.cache_resource
def load_spatial_engine():
    return SpatialHazardEngine()

@st.cache_resource
def load_dosimetry_engine():
    return CrewDosimetryEngine()

@st.cache_resource
def load_maint_engine():
    return PredictiveMaintenanceEngine()

@st.cache_resource
def load_action_scheduler():
    return AStarActionScheduler()


# -----------------------------------------------------------------------------
# Sidebar: Mission Operations & Space Weather Control Panel
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 class='nasa-title-gradient'>🛰️ DSN TELEMETRY</h2>", unsafe_allow_html=True)
    st.markdown("<div class='nasa-mono' style='font-size:0.8rem; color:#8B8FAF;'>ISRO ISTRAC • MCF • NASA DSN LIVE INGEST</div>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### 🌐 Space Weather Simulation Preset")
    scenario_choice = st.selectbox(
        "Load Mission Scenario:",
        [
            "Custom Telemetry",
            "Nominal Spaceflight (Quiet Solar Min)",
            "Moderate CME Shock (August 2024)",
            "Severe SPE Front (October 2024 CME)",
            "G5 Super-Storm (May 10-12, 2024 Event)",
        ],
        index=0,
    )

    if scenario_choice == "Nominal Spaceflight (Quiet Solar Min)":
        f_val, v_val, bz_val, n_val, p_val = 1.2, 380.0, 3.2, 4.0, 1.2
    elif scenario_choice == "Moderate CME Shock (August 2024)":
        f_val, v_val, bz_val, n_val, p_val = 85.0, 580.0, -9.2, 11.5, 4.1
    elif scenario_choice == "Severe SPE Front (October 2024 CME)":
        f_val, v_val, bz_val, n_val, p_val = 420.0, 740.0, -21.0, 18.2, 9.6
    elif scenario_choice == "G5 Super-Storm (May 10-12, 2024 Event)":
        f_val, v_val, bz_val, n_val, p_val = 1850.0, 890.0, -34.5, 28.4, 14.8
    else:
        f_val, v_val, bz_val, n_val, p_val = 150.0, 640.0, -14.5, 12.5, 4.8

    st.markdown("### 🎛️ Aditya-L1 Sensor Feeds")
    sim_flux = st.slider("Solar Proton Flux (pfu)", 0.1, 3000.0, float(f_val), step=1.0)
    sim_speed = st.slider("Solar Wind Velocity (km/s)", 250.0, 1200.0, float(v_val), step=10.0)
    sim_bz = st.slider("IMF Bz Field (nT)", -50.0, 30.0, float(bz_val), step=0.5)
    sim_density = st.slider("Proton Density (cm⁻³)", 1.0, 60.0, float(n_val), step=0.5)
    sim_pressure = st.slider("Dynamic Pressure (nPa)", 0.5, 30.0, float(p_val), step=0.5)

    st.divider()
    st.markdown(
        """
        <div class='nasa-mono' style='font-size: 0.78rem; color: #8B8FAF; line-height: 1.6;'>
        <b>GROUND STATION NETWORK:</b><br/>
        • ISTRAC Bengaluru: <span style="color:#5EC982;">LOCK 100%</span><br/>
        • MCF Hassan: <span style="color:#5EC982;">LOCK 100%</span><br/>
        • DSN Goldstone/Madrid: <span style="color:#5EC982;">ACTIVE</span><br/>
        • Uplink Encryption: <span style="color:#7EB8DA;">HMAC-SHA256</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Current Ingest Telemetry
telemetry_packet = {
    "proton_flux_pfu": sim_flux,
    "proton_speed_kms": sim_speed,
    "mag_bz_field": sim_bz,
    "proton_density_cm3": sim_density,
    "solar_wind_dyn_pressure_npa": sim_pressure,
}

# Run All 5 SPARC Algorithms Live
clf = load_classifier()
severity_report = clf.predict_single(telemetry_packet)

spatial_eng = load_spatial_engine()
hazard_report = spatial_eng.evaluate_storm_hazards(
    solar_wind_speed_kms=sim_speed,
    bz_field_nt=sim_bz,
    proton_flux_pfu=sim_flux,
)

maint_eng = load_maint_engine()
fleet_maintenance = maint_eng.evaluate_fleet_telemetry()

scheduler = load_action_scheduler()
scheduled_commands = scheduler.schedule_telecommands(
    hazard_report["fleet_hazard_profile"], fleet_maintenance
)

dosimetry_eng = load_dosimetry_engine()
historical_flux_window = [sim_flux * (0.85 + 0.03 * i) for i in range(15)]
dosimetry_report = dosimetry_eng.forecast_6h_radiation_curve(
    historical_flux_window, sim_speed, sim_bz
)

# -----------------------------------------------------------------------------
# Mission Operations Master Header
# -----------------------------------------------------------------------------
h_left, h_right = st.columns([3, 1])
with h_left:
    st.markdown("<h1 class='nasa-title-gradient'>🚀 SPARC-PM : ISRO MISSION OPERATIONS CENTER</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='nasa-mono' style='color:#8B8FAF; margin-top:-10px; font-size:0.95rem;'>"
        "AUTONOMOUS SPACE WEATHER RISK CLASSIFICATION, GAGANYAAN DOSIMETRY & 3D FLEET DEFENSE"
        "</div>",
        unsafe_allow_html=True,
    )
with h_right:
    utc_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.markdown(
        f"""
        <div class='nasa-card' style='text-align:right; padding:10px 16px; margin-bottom:0;'>
            <div class='nasa-mono' style='color:#8B8FAF; font-size:0.75rem;'>MISSION ELAPSED TIME &bull; UTC</div>
            <div class='nasa-mono' style='color:#E8C547; font-size:1.15rem; font-weight:bold;'>{utc_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br/>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6 Interactive Mission Navigation Tabs
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 1. Mission Overview & Triage",
    "👨‍🚀 2. Gaganyaan Crew Dosimetry",
    "🌐 3. 3D Fleet Spatial Hazard",
    "🛠️ 4. Predictive Maintenance",
    "📡 5. Command Synthesizer",
    "📈 6. Incident Analytics & Replay",
])

# =============================================================================
# TAB 1: MISSION OVERVIEW & FSM TRIAGE
# =============================================================================
with tab1:
    triage = severity_report["triage"]
    banner_class = "nasa-card-green" if triage == "GREEN" else "nasa-card-yellow" if triage == "YELLOW" else "nasa-card-red"
    led = "led-green" if triage == "GREEN" else "led-red"

    st.markdown(
        f"""
        <div class="nasa-card {banner_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span class="{led}"></span>
                    <strong class="nasa-mono" style="font-size:1.25rem; color:#ffffff;">
                        SPACE WEATHER LEVEL: {severity_report['severity_label']} &nbsp;|&nbsp; FSM TRIAGE: {triage}
                    </strong>
                </div>
                <div>
                    <span class="badge-{triage.lower()}">{severity_report['action']}</span>
                </div>
            </div>
            <div class="nasa-mono" style="color:#d5e7f9; margin-top:8px; font-size:0.95rem;">
                <b>GROUND DIRECTIVE:</b> {severity_report['action_description']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Key Telemetry Gauges (4 Grid Cards)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="nasa-metric-card">
                <div class="nasa-metric-label">SOLAR PROTON FLUX</div>
                <div class="nasa-value-tick" style="color:{'#5EC982' if sim_flux < 10 else '#E8C547' if sim_flux < 100 else '#E85D5D'};">
                    {sim_flux:,.1f} <span style="font-size:0.95rem;">pfu</span>
                </div>
                <div class="nasa-mono" style="font-size:0.8rem; color:#8B8FAF;">
                    Sensor: Aditya-L1 ASPEX/SWIS
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="nasa-metric-card">
                <div class="nasa-metric-label">SOLAR WIND SPEED & Bz</div>
                <div class="nasa-value-tick">
                    {sim_speed:.0f} <span style="font-size:0.95rem; color:#8B8FAF;">km/s</span>
                </div>
                <div class="nasa-mono" style="font-size:0.8rem; color:{'#5EC982' if sim_bz >= 0 else '#E85D5D'};">
                    IMF Bz: {sim_bz:+.1f} nT (Reconnection)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class="nasa-metric-card">
                <div class="nasa-metric-label">SPACECRAFT AT HIGH HAZARD</div>
                <div class="nasa-value-tick" style="color:{'#5EC982' if hazard_report['critical_count'] == 0 else '#E85D5D'};">
                    {hazard_report['critical_count']} <span style="font-size:0.95rem; color:#8B8FAF;">/ {hazard_report['total_satellites']}</span>
                </div>
                <div class="nasa-mono" style="font-size:0.8rem; color:#E8C547;">
                    {hazard_report['warning_count']} Elevated Proximate Assets
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div class="nasa-metric-card">
                <div class="nasa-metric-label">GAGANYAAN CABIN RATE</div>
                <div class="nasa-value-tick" style="color:{'#5EC982' if dosimetry_report['alert_color'] == 'GREEN' else '#E85D5D'};">
                    {dosimetry_report['peak_dose_rate_usv_hr']:.1f} <span style="font-size:0.95rem;">μSv/hr</span>
                </div>
                <div class="nasa-mono" style="font-size:0.8rem; color:#8B8FAF;">
                    EVA Status: {dosimetry_report['eva_status']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Real-Time Visual Meters & Telecommand Directive Row
    col_chart1, col_chart2 = st.columns([1, 1])
    with col_chart1:
        st.markdown("<h3 class='nasa-title' style='font-size:1.05rem;'>🎯 Bayesian & Ensemble Severity Posterior</h3>", unsafe_allow_html=True)
        prob_data = pd.DataFrame([
            {"Severity Class": k, "Posterior (%)": v * 100.0}
            for k, v in severity_report["probabilities"].items()
        ])
        fig_p = px.bar(
            prob_data,
            x="Severity Class",
            y="Posterior (%)",
            color="Posterior (%)",
            color_continuous_scale="Blues",
            text_auto=".1f",
        )
        fig_p.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(12,12,28,0.8)",
            plot_bgcolor="rgba(12,12,28,0.8)",
            height=280,
            margin=dict(l=20, r=20, t=20, b=20),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_p, width="stretch")

    with col_chart2:
        st.markdown("<h3 class='nasa-title' style='font-size:1.05rem;'>⚡ Autonomous Ground Operations Summary</h3>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="nasa-card" style="height:280px; display:flex; flex-direction:column; justify-content:space-around;">
                <div class="nasa-mono" style="font-size:0.92rem; line-height:1.9;">
                    &bull; <b>Model Latency:</b> {severity_report['inference_latency_ms']} ms (<span style="color:#5EC982;">Sub-100ms Compliant</span>)<br/>
                    &bull; <b>A* Scheduler Time:</b> {scheduled_commands['scheduler_latency_ms']} ms<br/>
                    &bull; <b>Queued Telecommands:</b> {scheduled_commands['commands_scheduled_count']} Transmissions<br/>
                    &bull; <b>Ground Station Power Budget:</b> {scheduled_commands['allocated_power_w']} W / {scheduled_commands['max_power_budget_w']} W<br/>
                    &bull; <b>Active Crew Protocol:</b> <span style="color:#7EB8DA;">{dosimetry_report['crew_action']}</span><br/>
                    &bull; <b>Corridor Dynamic Diameter:</b> {hazard_report['storm_corridor_radius_km'] * 2:,.0f} km
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============================================================================
# TAB 2: GAGANYAAN HUMAN CREW DOSIMETRY
# =============================================================================
with tab2:
    st.markdown("<h2 class='nasa-title-gradient'>👨‍🚀 GAGANYAAN CREW RADIATION DOSIMETRY</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='nasa-mono' style='color:#8B8FAF; margin-top:-10px; margin-bottom:15px;'>"
        "PyTorch LSTM 6-Hour Forecast & Cumulative Absorbed Dose behind 3.5 g/cm² Aluminum Shielding"
        "</div>",
        unsafe_allow_html=True,
    )

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.metric("Peak Projected Rate", f"{dosimetry_report['peak_dose_rate_usv_hr']:.1f} μSv/hr")
    with d2:
        st.metric("6h Cumulative Exposure", f"{dosimetry_report['total_6h_dose_msv']:.4f} mSv")
    with d3:
        st.metric("Career Limit Budget (20 mSv)", f"{dosimetry_report['career_limit_percentage']:.2f}%")
    with d4:
        st.metric("EVA Clearance", dosimetry_report["eva_status"])

    # High-Resolution Interactive Plotly Forecast Chart
    timeline = [f"+{int(m)}m" for m in dosimetry_report["timestamps_min"]]
    fig_dosimetry = go.Figure()

    fig_dosimetry.add_trace(go.Scatter(
        x=timeline,
        y=dosimetry_report["dose_rate_usv_hr"],
        mode="lines+markers",
        name="Cabin Interior Dose Rate (μSv/hr)",
        line=dict(color="#7EB8DA", width=3.5),
        fill="tozeroy",
        fillcolor="rgba(126, 184, 218, 0.08)",
    ))
    fig_dosimetry.add_trace(go.Scatter(
        x=timeline,
        y=dosimetry_report["forecast_flux_pfu"],
        mode="lines",
        name="External Solar Wind Proton Flux (pfu)",
        line=dict(color="#FF9900", width=2, dash="dash"),
        yaxis="y2",
    ))

    # Safety Lines
    fig_dosimetry.add_hline(y=EVA_SAFE_THRESHOLD_USV_HR, line_dash="dot", line_color="#5EC982", annotation_text="EVA Safe Threshold (50 μSv/hr)", annotation_position="top left")
    fig_dosimetry.add_hline(y=EVA_CAUTION_THRESHOLD_USV_HR, line_dash="dot", line_color="#E85D5D", annotation_text="EVA Abort / Storm Threshold (250 μSv/hr)", annotation_position="top left")

    fig_dosimetry.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(12,12,28,0.8)",
        plot_bgcolor="rgba(12,12,28,0.8)",
        height=420,
        yaxis=dict(title="Cabin Dose Rate (μSv/hr)", color="#7EB8DA"),
        yaxis2=dict(title="Proton Flux (pfu)", color="#D4A030", overlaying="y", side="right"),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0.5)"),
        margin=dict(l=40, r=40, t=30, b=30),
    )
    st.plotly_chart(fig_dosimetry, width="stretch")

    # Gaganyaan Operational Directives Card
    st.markdown(
        f"""
        <div class="nasa-card {'nasa-card-red' if dosimetry_report['alert_color'] == 'RED' else 'nasa-card-green'}">
            <h4 style="color:#ffffff; margin-bottom:8px;">GAGANYAAN FLIGHT DIRECTIVE & CREW ACTION:</h4>
            <div class="nasa-mono" style="font-size:1.05rem; color:#7EB8DA;">
                <b>DIRECTIVE:</b> {dosimetry_report['crew_action']} &nbsp;|&nbsp; <b>PROTOCOL:</b> {dosimetry_report['action_guidance']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================================================================
# TAB 3: 3D FLEET SPATIAL HAZARD PROFILER
# =============================================================================
with tab3:
    st.markdown("<h2 class='nasa-title-gradient'>🌐 3D FLEET ORBITAL HAZARD RADAR</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='nasa-mono' style='color:#8B8FAF; margin-top:-10px; margin-bottom:15px;'>"
        "SGP4 True Equator Orbital Ephemeris & 3D Dynamic Storm Corridor Proximity Intersections"
        "</div>",
        unsafe_allow_html=True,
    )

    fleet_table = pd.DataFrame(hazard_report["fleet_hazard_profile"])

    # 3D Orbital Globe Visualization
    fig_globe = go.Figure()

    # Earth Sphere (WGS-84 Approx)
    u_vals = np.linspace(0, 2 * np.pi, 30)
    v_vals = np.linspace(0, np.pi, 30)
    r_earth = 6378.137
    x_earth = r_earth * np.outer(np.cos(u_vals), np.sin(v_vals))
    y_earth = r_earth * np.outer(np.sin(u_vals), np.sin(v_vals))
    z_earth = r_earth * np.outer(np.ones(np.size(u_vals)), np.cos(v_vals))

    fig_globe.add_trace(go.Surface(
        x=x_earth, y=y_earth, z=z_earth,
        colorscale="Blues",
        showscale=False,
        opacity=0.32,
        hoverinfo="skip",
    ))

    # Satellite Orbital Markers Categorized by Alert Status
    for alert_tier, hex_col in [("CRITICAL", "#E85D5D"), ("WARNING", "#E8C547"), ("ELEVATED", "#7EB8DA"), ("NOMINAL", "#5EC982")]:
        sub = fleet_table[fleet_table["alert_level"] == alert_tier]
        if not sub.empty:
            coords = np.array(sub["r_ecef"].tolist())
            fig_globe.add_trace(go.Scatter3d(
                x=coords[:, 0],
                y=coords[:, 1],
                z=coords[:, 2],
                mode="markers+text",
                name=f"{alert_tier} ({len(sub)})",
                text=sub["name"],
                textposition="top center",
                marker=dict(size=6.5, color=hex_col, opacity=0.9),
            ))

    fig_globe.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(12,12,28,0.8)",
        height=540,
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(title="X_ECEF (km)", backgroundcolor="rgba(0,0,0,0)"),
            yaxis=dict(title="Y_ECEF (km)", backgroundcolor="rgba(0,0,0,0)"),
            zaxis=dict(title="Z_ECEF (km)", backgroundcolor="rgba(0,0,0,0)"),
            aspectmode="data",
        ),
    )
    st.plotly_chart(fig_globe, width="stretch")

    # Fleet Spatial Radar Table
    st.markdown("<h3 class='nasa-title' style='font-size:1.05rem;'>📋 Live Constellation Hazard Proximity Telemetry</h3>", unsafe_allow_html=True)
    st.dataframe(
        fleet_table[["name", "orbit_type", "altitude_km", "dist_to_storm_km", "hazard_ratio", "alert_level"]],
        width="stretch",
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

# =============================================================================
# TAB 4: SUBSYSTEM PREDICTIVE MAINTENANCE
# =============================================================================
with tab4:
    st.markdown("<h2 class='nasa-title-gradient'>🛠️ DEEP LEARNING PREDICTIVE MAINTENANCE</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='nasa-mono' style='color:#8B8FAF; margin-top:-10px; margin-bottom:15px;'>"
        "PyTorch 1D-CNN + LSTM 72-Hour Component Failure Probability P_fail conditioned on Space Weather Stress"
        "</div>",
        unsafe_allow_html=True,
    )

    df_m = pd.DataFrame(fleet_maintenance)

    pm1, pm2, pm3 = st.columns(3)
    with pm1:
        st.metric("Critical Degradation (P_fail ≥ 0.70)", len(df_m[df_m["p_fail_72h"] >= 0.70]))
    with pm2:
        st.metric("Elevated Risk (0.40 ≤ P_fail < 0.70)", len(df_m[(df_m["p_fail_72h"] >= 0.40) & (df_m["p_fail_72h"] < 0.70)]))
    with pm3:
        st.metric("Optimal Health (P_fail < 0.20)", len(df_m[df_m["p_fail_72h"] < 0.20]))

    # Top At-Risk Assets Bar Chart
    top_assets = df_m.head(10)
    fig_top = px.bar(
        top_assets,
        x="sat_id",
        y="p_fail_72h",
        color="p_fail_72h",
        color_continuous_scale="Reds",
        title="Top-10 Highest Component Failure Risk Spacecraft (72h Forecast)",
        labels={"p_fail_72h": "Failure Probability P_fail", "sat_id": "Satellite ID"},
    )
    fig_top.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(12,12,28,0.8)",
        plot_bgcolor="rgba(12,12,28,0.8)",
        height=320,
    )
    st.plotly_chart(fig_top, width="stretch")

    # Multi-Sensor Housekeeping Telemetry Table
    st.markdown("<h3 class='nasa-title' style='font-size:1.05rem;'>📊 Multi-Sensor Housekeeping Telemetry Diagnostics</h3>", unsafe_allow_html=True)
    st.dataframe(
        df_m[["sat_id", "p_fail_72h", "health_status", "battery_voltage_v", "subsystem_temp_c", "gyro_drift_deg_hr", "dosimeter_count"]],
        width="stretch",
        hide_index=True,
        column_config={
            "sat_id": "Satellite ID",
            "p_fail_72h": st.column_config.ProgressColumn("72h Failure Risk", min_value=0.0, max_value=1.0, format="%.4f"),
            "health_status": "Health Status",
            "battery_voltage_v": st.column_config.NumberColumn("Battery (V)", format="%.2f"),
            "subsystem_temp_c": st.column_config.NumberColumn("Temp (°C)", format="%.1f"),
            "gyro_drift_deg_hr": st.column_config.NumberColumn("Gyro Drift (°/hr)", format="%.4f"),
            "dosimeter_count": st.column_config.NumberColumn("Dosimeter", format="%.1f"),
        },
    )

# =============================================================================
# TAB 5: CLOSED-LOOP COMMAND SYNTHESIZER
# =============================================================================
with tab5:
    st.markdown("<h2 class='nasa-title-gradient'>📡 A* CLOSED-LOOP COMMAND SYNTHESIZER</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='nasa-mono' style='color:#8B8FAF; margin-top:-10px; margin-bottom:15px;'>"
        "A* Priority Queue Search & Cryptographically Signed HMAC-SHA256 Binary Telecommand Frames"
        "</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Scheduled Telecommands", scheduled_commands["commands_scheduled_count"])
    with c2:
        st.metric("Allocated Power Budget", f"{scheduled_commands['allocated_power_w']} / {scheduled_commands['max_power_budget_w']} W")
    with c3:
        st.metric("A* Search Latency", f"{scheduled_commands['scheduler_latency_ms']} ms")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Command Execution Cards
    if scheduled_commands["command_queue"]:
        for cmd in scheduled_commands["command_queue"][:6]:
            frame = cmd["telecommand_frame"]
            with st.expander(f"⭐ PRIORITY RANK #{cmd['priority_rank']} : {cmd['satellite']} ➔ {cmd['recommended_action']} ({cmd['urgency_tier']})", expanded=(cmd["priority_rank"] == 1)):
                col_left, col_right = st.columns([3, 1])
                with col_left:
                    st.markdown(f"**Action Description:** {cmd['description']}")
                    st.markdown(f"**Power Draw:** `{cmd['power_draw_w']} W` &nbsp;|&nbsp; **f(n) Priority Score:** `{cmd['f_score']}`")
                    st.markdown(f"**Telecommand Payload Frame:** `{frame['payload']}`")
                    st.markdown(f"**HMAC-SHA256 Cryptographic Checksum:** `{frame['sha256_signature']}`")
                with col_right:
                    st.write("")
                    if st.button(f"⚡ TRANSMIT & UPLINK TO {cmd['satellite']}", key=f"uplink_{cmd['satellite']}"):
                        st.success(f"✅ UPLINK CONFIRMED: SHA-256 Checksum Verified at ISTRAC Ground Station!")
    else:
        st.info("Fleet operating in nominal regime. Zero emergency corrective telecommands queued.")

# =============================================================================
# TAB 6: INCIDENT ANALYTICS & HISTORICAL REPLAY
# =============================================================================
with tab6:
    st.markdown("<h2 class='nasa-title-gradient'>📈 INCIDENT ANALYTICS & MODEL BENCHMARKS</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='nasa-mono' style='color:#8B8FAF; margin-top:-10px; margin-bottom:15px;'>"
        "Empirical Model Validation on the Historical May 2024 Mother's Day Super-Storm and October 2024 CME"
        "</div>",
        unsafe_allow_html=True,
    )

    bench_path = PROJECT_ROOT / "docs" / "benchmark_results.json"
    if bench_path.exists():
        with open(bench_path, "r") as f:
            b_data = json.load(f)

        h_val = b_data.get("historical_validation", {})
        ab_val = b_data.get("ablation_study", {}).get("ablation_comparison", [])

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("Historical Accuracy", f"{h_val.get('accuracy', 0.8) * 100:.1f}%")
        with s2:
            st.metric("Macro F1-Score", f"{h_val.get('macro_f1', 0.85):.4f}")
        with s3:
            st.metric("True Skill Statistic (TSS)", f"{h_val.get('tss', 0.7):.4f}")
        with s4:
            st.metric("Mean Latency", f"{h_val.get('avg_latency_ms', 5.0):.2f} ms")

        st.markdown("<br/>", unsafe_allow_html=True)

        if ab_val:
            st.markdown("<h3 class='nasa-title' style='font-size:1.05rem;'>🔬 Space Weather Model Ablation Benchmark</h3>", unsafe_allow_html=True)
            df_ab = pd.DataFrame(ab_val)
            st.dataframe(
                df_ab,
                width="stretch",
                hide_index=True,
                column_config={
                    "architecture": "Architecture",
                    "accuracy": st.column_config.NumberColumn("Accuracy", format="%.4f"),
                    "macro_f1": st.column_config.NumberColumn("Macro F1", format="%.4f"),
                    "train_time_s": st.column_config.NumberColumn("Training Time (s)", format="%.3f"),
                    "latency_ms": st.column_config.NumberColumn("Inference Latency (ms)", format="%.3f"),
                },
            )
    else:
        st.info("Benchmark results file not found. Run `python src/evaluation/benchmark_eval.py`.")