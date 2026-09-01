import sys
import os
import datetime
import pandas as pd
import streamlit as st

# Ensure root & src directories are in python path so modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

st.set_page_config(
    page_title="SPARC-PM Mission Control HUD",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

REFRESH_SECONDS = 10

# -----------------------------------------------------------------------------
# Sci-Fi / HUD Cyberpunk Styling & Seamless Refresh (No Dimming)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Share+Tech+Mono&family=Rajdhani:wght@500;600;700&display=swap');

    /* Global Dark Sci-Fi Background */
    .stApp {
        background-color: #060913;
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(0, 240, 255, 0.08) 0%, transparent 65%),
            linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
        background-size: 100% 100%, 35px 35px, 35px 35px;
        font-family: 'Rajdhani', sans-serif;
        color: #d0f0ff;
    }

    /* DISABLE STREAMLIT DIMMING / GREY OVERLAY ON REFRESH */
    div[data-testid="stAppViewBlockContainer"],
    div[data-testid="stAppViewContainer"],
    div[data-testid="stHeader"],
    .stMainBlockContainer,
    .element-container,
    div[data-testid="stVerticalBlock"],
    div[data-st-mode],
    [data-testid="stFragment"] {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }

    /* Sci-Fi Typography */
    h1, h2, h3, .hud-title {
        font-family: 'Orbitron', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .hud-title-gradient {
        background: linear-gradient(90deg, #00F0FF 0%, #7000FF 50%, #FF0055 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-shadow: 0 0 25px rgba(0, 240, 255, 0.5);
    }

    .hud-mono {
        font-family: 'Share Tech Mono', monospace !important;
    }

    /* Sci-Fi Glass Containers */
    .hud-card {
        background: rgba(10, 16, 30, 0.85);
        border: 1px solid rgba(0, 240, 255, 0.3);
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.7), inset 0 0 20px rgba(0, 240, 255, 0.05);
        backdrop-filter: blur(12px);
        margin-bottom: 12px;
        position: relative;
    }

    .hud-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 4px; height: 100%;
        background: #00F0FF;
        box-shadow: 0 0 12px #00F0FF;
        border-radius: 10px 0 0 10px;
    }

    .hud-card-critical::before { background: #FF0055; box-shadow: 0 0 12px #FF0055; }
    .hud-card-warning::before { background: #FF9900; box-shadow: 0 0 12px #FF9900; }
    .hud-card-nominal::before { background: #00FF66; box-shadow: 0 0 12px #00FF66; }

    /* Sci-Fi Number Changing & Ticker Animations */
    @keyframes ticker-glow {
        0% { opacity: 0.7; transform: translateY(-2px); filter: brightness(1.4); }
        50% { opacity: 1; transform: translateY(0); filter: brightness(1.7); text-shadow: 0 0 22px #00F0FF; }
        100% { opacity: 1; transform: translateY(0); filter: brightness(1); }
    }

    .hud-metric-card {
        background: rgba(10, 16, 32, 0.85);
        border: 1px solid rgba(0, 240, 255, 0.3);
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.6), inset 0 0 15px rgba(0, 240, 255, 0.08);
        backdrop-filter: blur(10px);
        margin-bottom: 10px;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .hud-metric-label {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 0.82rem;
        color: #7fadf2;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    .hud-value-tick {
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 800;
        font-size: 1.85rem;
        color: #00F0FF;
        text-shadow: 0 0 14px rgba(0, 240, 255, 0.7);
        animation: ticker-glow 0.6s cubic-bezier(0.1, 0.9, 0.2, 1);
        display: inline-block;
        line-height: 1.1;
    }

    .hud-metric-sub {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 0.82rem;
        letter-spacing: 0.5px;
    }

    /* Animated Pulsing Status LED */
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(0, 255, 102, 0.8); }
        70% { box-shadow: 0 0 0 12px rgba(0, 255, 102, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 255, 102, 0); }
    }

    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 0, 85, 0.9); }
        70% { box-shadow: 0 0 0 14px rgba(255, 0, 85, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 0, 85, 0); }
    }

    .led-nominal {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #00FF66;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse-green 1.8s infinite;
    }

    .led-critical {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #FF0055;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse-red 0.8s infinite;
    }

    /* Custom Scanline Grid Overlay for Movie HUD Effect */
    .scanline-grid {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.15) 50%);
        background-size: 100% 4px;
        z-index: 99999;
        pointer-events: none;
        opacity: 0.4;
    }
    </style>
    <div class="scanline-grid"></div>
    """,
    unsafe_allow_html=True
)

# Sidebar Configuration Controls
with st.sidebar:
    st.markdown("<h2 class='hud-title-gradient'>⚙️ HUD CONTROLS</h2>", unsafe_allow_html=True)
    refresh_rate = st.slider("⏱️ Refresh Interval (Sec)", min_value=3, max_value=30, value=REFRESH_SECONDS)
    st.divider()
    st.markdown(
        """
        <div class='hud-mono' style='font-size: 0.85rem; color: #8ab4f8;'>
        <b>SPARC-PM v1.0 MISSION CONTROL</b><br/>
        • Telemetry Source: ISRO Aditya-L1 (ASPEX / PAPA / MAG)<br/>
        • Orbit Propagator: SGP4 ECEF Model<br/>
        • Risk Corridors: SAA & Auroral Ovals
        </div>
        """,
        unsafe_allow_html=True
    )

# Header Section
head_col1, head_col2 = st.columns([4, 1])
with head_col1:
    st.markdown("<h1 class='hud-title-gradient'>🛰️ SPARC-PM : MISSION CONTROL HUD</h1>", unsafe_allow_html=True)
    st.markdown("<div class='hud-mono' style='color: #00F0FF; margin-top: -10px;'>SPACE PARTICLE RADIATION ALERT & RESILIENCE CENTER — TELEMETRY & RISK MONITOR</div>", unsafe_allow_html=True)

with head_col2:
    st.write("")
    if st.button("⚡ EXECUTE MANUAL REFRESH", use_container_width=True):
        st.rerun()

# -----------------------------------------------------------------------------
# Auto-Refreshing Fragment (Movie Style Telemetry HUD - No Dimming)
# -----------------------------------------------------------------------------
@st.fragment(run_every=refresh_rate)
def render_hud_fragment():
    try:
        from dashboard_data import get_dashboard_snapshot
        snapshot = get_dashboard_snapshot()
    except (FileNotFoundError, Exception) as e:
        st.error("⚠️ CRITICAL: TELEMETRY STREAM OFFLINE")
        st.warning(f"Pipeline error: {e}")
        st.info("Execute dataset generator: `python src/fetch_celestrak.py` & `python src/parse_aditya.py`")
        return

    severity = snapshot.get("severity", "Calm")
    probabilities = snapshot.get("severity_probabilities", {})
    raw_vals = snapshot.get("raw_values", {})
    risk_df = snapshot.get("satellite_risk_table", pd.DataFrame())

    total_satellites = len(risk_df)
    if total_satellites > 0:
        critical_count = len(risk_df[risk_df["risk_level"] == "CRITICAL"])
        warning_count = len(risk_df[risk_df["risk_level"] == "WARNING"])
        nominal_count = len(risk_df[risk_df["risk_level"] == "NOMINAL"])
        alert_count = critical_count + warning_count
        online_pct = (nominal_count / total_satellites) * 100.0
    else:
        critical_count = warning_count = nominal_count = alert_count = 0
        online_pct = 100.0

    peak_proton_flux = raw_vals.get("aspex_proton_flux", 12.4)
    wind_velocity = raw_vals.get("papa_wind_velocity", 450.0)
    mag_bz = raw_vals.get("mag_bz_field", -2.5)

    timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Dynamic Alert Header Card
    if severity == "Calm":
        led_class = "led-nominal"
        status_msg = "🟢 SYSTEM NOMINAL — SOLAR CONDITIONS CALM"
        border_class = "hud-card-nominal"
    elif severity == "Watch":
        led_class = "led-nominal"
        status_msg = "🟡 DISTURBANCE DETECTED — SPACE WEATHER WATCH IN EFFECT"
        border_class = "hud-card-warning"
    elif severity == "Warning":
        led_class = "led-critical"
        status_msg = "🟠 HIGH RADIATION WARNING — ASSET CORRIDORS AT RISK"
        border_class = "hud-card-warning"
    else:
        led_class = "led-critical"
        status_msg = "🔴 SPACE WEATHER EMERGENCY — SEVERE SOLAR EVENT IN PROGRESS!"
        border_class = "hud-card-critical"

    st.markdown(
        f"""
        <div class="hud-card {border_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="{led_class}"></span>
                    <strong class="hud-mono" style="font-size: 1.2rem; color: #ffffff;">{status_msg}</strong>
                </div>
                <div class="hud-mono" style="color: #00F0FF; font-size: 0.95rem;">
                    LIVE TELEMETRY STREAM &nbsp;|&nbsp; UTC {timestamp_str}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Telemetry KPI Dashboard Cards (Animated Sci-Fi Number Changing HUD Cards)
    k1, k2, k3, k4 = st.columns(4)

    fleet_val = "NOMINAL" if alert_count == 0 else f"ALERT ({alert_count})"
    fleet_color = "#00FF66" if alert_count == 0 else "#FF0055"
    fleet_sub = "0 Hazards Detected" if alert_count == 0 else f"▲ {alert_count} Threats Active"
    fleet_sub_color = "#00FF66" if alert_count == 0 else "#FF0055"

    with k1:
        st.markdown(
            f"""
            <div class="hud-metric-card">
                <div class="hud-metric-label">FLEET STATUS</div>
                <div class="hud-value-tick" style="color: {fleet_color}; text-shadow: 0 0 14px {fleet_color};">
                    {fleet_val}
                </div>
                <div class="hud-metric-sub" style="color: {fleet_sub_color};">
                    {fleet_sub}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with k2:
        st.markdown(
            f"""
            <div class="hud-metric-card">
                <div class="hud-metric-label">TRACKED ASSETS</div>
                <div class="hud-value-tick">
                    {nominal_count:,} <span style="font-size:1.1rem; color:#7fadf2;">/ {total_satellites:,}</span>
                </div>
                <div class="hud-metric-sub" style="color: {'#00FF66' if online_pct >= 95 else '#FF9900'};">
                    ▲ {online_pct:.1f}% Operational
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    flux_color = "#00FF66" if severity == "Calm" else "#FF9900" if severity in ["Watch", "Warning"] else "#FF0055"
    with k3:
        st.markdown(
            f"""
            <div class="hud-metric-card">
                <div class="hud-metric-label">SOLAR PROTON FLUX</div>
                <div class="hud-value-tick" style="color: {flux_color}; text-shadow: 0 0 14px {flux_color};">
                    {peak_proton_flux:.1f} <span style="font-size:1.1rem;">pfu</span>
                </div>
                <div class="hud-metric-sub" style="color: {flux_color};">
                    SEVERITY: {severity.upper()}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    bz_color = "#00FF66" if mag_bz >= -5.0 else "#FF0055"
    with k4:
        st.markdown(
            f"""
            <div class="hud-metric-card">
                <div class="hud-metric-label">SOLAR WIND / IMF Bz</div>
                <div class="hud-value-tick">
                    {wind_velocity:.0f} <span style="font-size:1.1rem; color:#7fadf2;">km/s</span>
                </div>
                <div class="hud-metric-sub" style="color: {bz_color};">
                    Bz FIELD: {mag_bz:.1f} nT
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Viva Model Transparency Panel
    with st.expander("🔬 NAIVE BAYES PROBABILISTIC CLASSIFIER BREAKDOWN (VIVA AUDIT PANEL)"):
        st.markdown(
            "<div class='hud-mono' style='color: #8ab4f8;'>Live posterior probability outputs generated by the Gaussian Naive Bayes classifier trained on Aditya-L1 particle data:</div><br/>",
            unsafe_allow_html=True
        )
        if probabilities:
            cols = st.columns(4)
            for idx, cls in enumerate(["Calm", "Watch", "Warning", "Emergency"]):
                p_val = probabilities.get(cls, 0.0)
                with cols[idx]:
                    st.metric(label=f"P({cls.upper()})", value=f"{p_val * 100:.1f}%")
                    st.progress(float(min(max(p_val, 0.0), 1.0)))

    # Satellite Risk Table HUD
    st.markdown("<h3 class='hud-title-gradient' style='font-size: 1.3rem; margin-top: 15px;'>🛰️ 3D ORBITAL PROXIMITY & HAZARD RADAR</h3>", unsafe_allow_html=True)

    if not risk_df.empty:
        c_filter1, c_filter2 = st.columns([2, 2])
        with c_filter1:
            risk_filter = st.multiselect(
                "Filter Hazard Status:",
                options=["CRITICAL", "WARNING", "NOMINAL"],
                default=["CRITICAL", "WARNING", "NOMINAL"]
            )
        with c_filter2:
            search_query = st.text_input("🔍 Search Satellite / NORAD ID:", "")

        filtered_df = risk_df[risk_df["risk_level"].isin(risk_filter)].copy()
        if search_query:
            q = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df["name"].str.lower().str.contains(q) |
                filtered_df["norad_id"].astype(str).str.contains(q)
            ]

        risk_order = {"CRITICAL": 0, "WARNING": 1, "NOMINAL": 2}
        filtered_df["sort_key"] = filtered_df["risk_level"].map(risk_order)
        filtered_df = filtered_df.sort_values("sort_key").drop(columns=["sort_key"])

        # Format risk_level with glowing sci-fi indicator badges for instant visual recognition
        display_df = filtered_df.copy()
        display_df["risk_level"] = display_df["risk_level"].map({
            "CRITICAL": "🔴 CRITICAL",
            "WARNING": "🟠 WARNING",
            "NOMINAL": "🟢 NOMINAL"
        }).fillna(display_df["risk_level"])

        st.dataframe(
            display_df,
            use_container_width=True,
            height=380,
            hide_index=True,
            column_config={
                "name": st.column_config.TextColumn("Satellite Name"),
                "norad_id": st.column_config.NumberColumn("NORAD ID", format="%d"),
                "lat": st.column_config.NumberColumn("Latitude (°)", format="%.2f"),
                "lon": st.column_config.NumberColumn("Longitude (°)", format="%.2f"),
                "alt_km": st.column_config.NumberColumn("Altitude (km)", format="%.1f"),
                "nearest_corridor": st.column_config.TextColumn("Nearest Hazard Corridor"),
                "distance_km": st.column_config.NumberColumn("Distance to Corridor (km)", format="%.1f"),
                "risk_level": st.column_config.TextColumn("Risk Level"),
            }
        )
        st.caption(f"📡 Active Orbital Tracking: {len(filtered_df):,} / {total_satellites:,} satellites monitored. (Auto-updating stream)")
    else:
        st.info("No orbital telemetry available.")

render_hud_fragment()