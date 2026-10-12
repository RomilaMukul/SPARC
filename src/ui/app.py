"""
SPARC-PM: Space Weather Risk Classification & Mission Control Console
=====================================================================
Autonomous Multi-Tier Space Weather Decision-Support Console for ISRO
Mission Operations Center (ISTRAC / MCF) Simulation Pipeline.

Full-screen interactive 3D Mission Control as landing page.
All existing backend engines and pages preserved.
"""

from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

# Path setup
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.pipeline import SCENARIOS, execute_pipeline
from src.ui.views.mission_control import render_mission_control_page
from src.ui.views.overview import render_overview_page
from src.ui.views.orbital_monitor_page import render_orbital_monitor_page
from src.ui.views.crew_dosimetry_page import render_crew_dosimetry_page
from src.ui.views.fleet_health_page import render_fleet_health_page
from src.ui.views.predictive_maintenance_page import render_predictive_maintenance_page
from src.ui.views.command_center_page import render_command_center_page
from src.ui.views.system_pages import render_system_page
from src.ui.components.navigation_rail import render_navigation

# -----------------------------------------------------------------------------
# Streamlit Page Setup & Full-Screen Mission Control CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SPARC-PM | ISRO Mission Operations Console",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Immersive Mission Control CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Full dark background */
    .stApp {
        background-color: #030712;
        font-family: 'Inter', -apple-system, sans-serif;
        color: #e2e8f0;
    }

    /* Headings */
    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.3px;
    }

    /* Hide Streamlit header/footer for immersive mode on Mission Control */
    header[data-testid="stHeader"] {
        background: rgba(3, 7, 18, 0.95) !important;
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(148, 163, 184, 0.08);
    }

    footer {
        display: none !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(3, 7, 18, 0.95) !important;
        border-right: 1px solid rgba(148, 163, 184, 0.08);
        backdrop-filter: blur(20px);
    }

    /* Compact sidebar content */
    section[data-testid="stSidebar"] .stRadio > label {
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
    }

    /* Streamlit Containers & Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #0b132b !important;
        border: 1px solid rgba(66, 217, 245, 0.22) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
    }

    /* Streamlit Widget Labels */
    div[data-testid="stWidgetLabel"] label,
    div[data-testid="stWidgetLabel"] p,
    .stSelectbox label,
    .stSelectbox label p,
    .stSlider label,
    .stSlider label p,
    label[data-testid="stWidgetLabel"] p {
        color: #cbd5e1 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
    }

    /* Selectbox Input Box */
    div[data-baseweb="select"] {
        background-color: #0f172a !important;
        border: 1px solid rgba(66, 217, 245, 0.35) !important;
        border-radius: 6px !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }

    div[data-baseweb="select"] * {
        color: #f8fafc !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }

    div[data-baseweb="select"] svg {
        fill: #42d9f5 !important;
    }

    /* Selectbox Dropdown Menu */
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[data-baseweb="menu"] {
        background-color: #0f172a !important;
        border: 1px solid rgba(66, 217, 245, 0.35) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
    }

    li[data-baseweb="menu-item"] {
        color: #e2e8f0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.8rem !important;
    }

    li[data-baseweb="menu-item"]:hover {
        background-color: #1e293b !important;
        color: #42d9f5 !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #0f172a;
        color: #f8fafc;
        border: 1px solid rgba(148, 163, 184, 0.25);
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.78rem;
        border-radius: 6px;
        transition: all 0.2s ease;
        letter-spacing: 0.5px;
    }
    .stButton > button:hover {
        background-color: #1e293b;
        border-color: #42d9f5;
        color: #42d9f5;
        box-shadow: 0 0 12px rgba(66, 217, 245, 0.25);
    }

    button[kind="primary"],
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        box-shadow: 0 0 14px rgba(56, 189, 248, 0.35) !important;
    }

    button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0369a1 0%, #0284c7 100%) !important;
        border-color: #42d9f5 !important;
        box-shadow: 0 0 18px rgba(66, 217, 245, 0.5) !important;
    }

    /* Modern Expander Header & Content */
    details[data-testid="stExpander"] {
        background-color: #0b132b !important;
        border: 1px solid rgba(66, 217, 245, 0.22) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }

    details[data-testid="stExpander"] summary {
        background-color: #0f172a !important;
        color: #e2e8f0 !important;
        padding: 9px 14px !important;
        border-radius: 6px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        transition: background 0.2s ease;
    }

    details[data-testid="stExpander"] summary:hover {
        background-color: #172540 !important;
        color: #42d9f5 !important;
    }

    details[data-testid="stExpander"] summary p,
    details[data-testid="stExpander"] summary span {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }

    details[data-testid="stExpander"] summary:hover p,
    details[data-testid="stExpander"] summary:hover span {
        color: #42d9f5 !important;
    }

    details[data-testid="stExpander"] summary svg {
        fill: #42d9f5 !important;
        stroke: #42d9f5 !important;
    }

    /* Sliders */
    div[data-testid="stSlider"] div[data-testid="stWidgetLabel"] p {
        color: #94a3b8 !important;
    }

    div[data-testid="stSlider"] span[data-testid="stSliderTickBarMin"],
    div[data-testid="stSlider"] span[data-testid="stSliderTickBarMax"],
    div[data-testid="stSlider"] div[data-testid="stThumbValue"] {
        color: #42d9f5 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Scrollbars */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }

    /* iframe for Three.js globe */
    iframe {
        border: none !important;
        border-radius: 0 !important;
    }

    /* Nav pill styling */
    .nav-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        cursor: pointer;
        transition: all 0.2s;
        text-transform: uppercase;
        text-decoration: none;
        color: #94a3b8;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.08);
    }

    .nav-pill:hover {
        color: #f8fafc;
        background: rgba(30, 41, 59, 0.8);
        border-color: rgba(148, 163, 184, 0.15);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "pipeline_results" not in st.session_state:
    default_telemetry = SCENARIOS["G3_SEVERE (October 2024 SPE)"]
    st.session_state["pipeline_results"] = execute_pipeline(default_telemetry, "G3_SEVERE (October 2024 SPE)")

if "manual_command_queue" not in st.session_state:
    st.session_state["manual_command_queue"] = []

# -----------------------------------------------------------------------------
# Sidebar Navigation (collapsed by default)
# -----------------------------------------------------------------------------
with st.sidebar:
    # Render compact navigation rail
    render_navigation()
    selected_page = st.session_state["selected_page"]
    


    # Scenario Selector in Sidebar
    st.markdown("<hr style='border:none; border-top:1px solid rgba(148,163,184,0.08); margin: 14px 0;'/>", unsafe_allow_html=True)
    st.markdown("<div style='font-family: \"JetBrains Mono\", monospace; font-size: 0.62rem; color: #475569; font-weight: 700; letter-spacing: 1px;'>SCENARIO</div>", unsafe_allow_html=True)
    
    selected_scenario = st.selectbox(
        "Space Weather Scenario",
        list(SCENARIOS.keys()),
        index=3,  # G3_SEVERE default
        key="sidebar_scenario",
        label_visibility="collapsed",
    )
    
    if st.button("🚀 RUN SIMULATION", use_container_width=True, key="sidebar_run_sim"):
        with st.spinner("Executing 5-Engine Pipeline..."):
            results = execute_pipeline(SCENARIOS[selected_scenario], selected_scenario)
            st.session_state["pipeline_results"] = results
            st.rerun()

    st.markdown(
        """
        <div style="margin-top: 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: #475569; line-height: 1.7;">
            <b>VERSION:</b> 2.4.0-PROD<br/>
            <b>SECURITY:</b> AUTHENTICATED<br/>
            <b>LATENCY:</b> <span style="color:#34d399;">SUB-100MS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Dynamic Layout Padding (Immersive for 3D Globe, Padded for Standard Pages)
# -----------------------------------------------------------------------------
if selected_page in ["🧭 Mission Control", "🌐 Mission Control"]:
    st.markdown(
        """
        <style>
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 3.5rem !important;
            padding-bottom: 2.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1400px !important;
            margin: 0 auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Primary Page Router
# -----------------------------------------------------------------------------
if selected_page in ["🧭 Mission Control", "🌐 Mission Control"]:
    render_mission_control_page()
elif selected_page == "📊 Overview":
    render_overview_page()
elif selected_page in ["🛰️ Orbital Monitor", "⚠️ Hazard Analysis"]:
    render_orbital_monitor_page()
elif selected_page == "👨‍🚀 Crew Dosimetry":
    render_crew_dosimetry_page()
elif selected_page == "🔧 Fleet Health":
    render_fleet_health_page()
elif selected_page == "⚙️ Predictive Maintenance":
    render_predictive_maintenance_page()
elif selected_page == "📡 Command Center":
    render_command_center_page()
elif selected_page == "📈 Space Weather":
    render_system_page("Telemetry")
elif selected_page == "📋 Telemetry Feeds":
    render_system_page("Telemetry")
elif selected_page == "🗃️ Data Sources":
    render_system_page("Data Sources")