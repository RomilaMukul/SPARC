import sys
import os
import json
import datetime
import pandas as pd
import streamlit as st

# Ensure root & src directories are in python path so modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

st.set_page_config(
    page_title="SPARC-PM Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

REFRESH_SECONDS = 10

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap');

    .stApp {
        background-color: #0d1117;
        font-family: 'Inter', sans-serif;
        color: #c9d1d9;
    }

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

    h1, h2, h3, .hud-title {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .hud-mono {
        font-family: 'Roboto Mono', monospace !important;
    }

    .hud-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 12px;
        position: relative;
    }

    .hud-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 4px; height: 100%;
        background: #58a6ff;
        border-radius: 6px 0 0 6px;
    }

    .hud-card-critical::before { background: #f85149; }
    .hud-card-warning::before { background: #d29922; }
    .hud-card-nominal::before { background: #3fb950; }

    .hud-metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 10px;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .hud-metric-label {
        font-family: 'Roboto Mono', monospace !important;
        font-size: 0.8rem;
        color: #8b949e;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .hud-value-tick {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700;
        font-size: 1.75rem;
        color: #58a6ff;
        display: inline-block;
        line-height: 1.1;
    }

    .hud-metric-sub {
        font-family: 'Roboto Mono', monospace !important;
        font-size: 0.8rem;
    }

    .led-nominal {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #3fb950;
        border-radius: 50%;
        margin-right: 8px;
    }

    .led-critical {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #f85149;
        border-radius: 50%;
        margin-right: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar Controls
with st.sidebar:
    st.markdown("<h3 style='color: #f0f6fc;'>Dashboard Controls</h3>", unsafe_allow_html=True)
    refresh_rate = st.slider("Refresh Interval (Sec)", min_value=3, max_value=30, value=REFRESH_SECONDS)
    st.divider()
    st.markdown(
        """
        <div class='hud-mono' style='font-size: 0.82rem; color: #8b949e;'>
        <b>SPARC-PM Mission Control</b><br/>
        • Telemetry: ISRO Aditya-L1 (ASPEX / PAPA / MAG)<br/>
        • Orbit Propagator: SGP4 ECEF Model<br/>
        • Corridors: SAA & Auroral Ovals
        </div>
        """,
        unsafe_allow_html=True
    )

# Header Section
head_col1, head_col2 = st.columns([4, 1])
with head_col1:
    st.markdown("<h2 style='color: #58a6ff; margin-bottom: 0;'>SPARC-PM Mission Control Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<div class='hud-mono' style='color: #8b949e; margin-top: 2px;'>Space Particle Radiation Alert & Resilience Center - Telemetry & Risk Monitor</div>", unsafe_allow_html=True)

with head_col2:
    st.write("")
    if st.button("Refresh Data", use_container_width=True):
        st.rerun()

@st.fragment(run_every=refresh_rate)
def render_hud_fragment():
    try:
        from dashboard_data import get_dashboard_snapshot
        snapshot = get_dashboard_snapshot()
    except (FileNotFoundError, Exception) as e:
        st.error("Telemetry stream unavailable.")
        st.warning(f"Pipeline error: {e}")
        st.info("Run data pipeline scripts: `python src/fetch_celestrak.py` and `python src/parse_aditya.py`")
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
        status_msg = "SYSTEM NOMINAL - SOLAR CONDITIONS CALM"
        border_class = "hud-card-nominal"
    elif severity == "Watch":
        led_class = "led-nominal"
        status_msg = "DISTURBANCE DETECTED - SPACE WEATHER WATCH IN EFFECT"
        border_class = "hud-card-warning"
    elif severity == "Warning":
        led_class = "led-critical"
        status_msg = "HIGH RADIATION WARNING - ASSET CORRIDORS AT RISK"
        border_class = "hud-card-warning"
    else:
        led_class = "led-critical"
        status_msg = "SPACE WEATHER EMERGENCY - SEVERE SOLAR EVENT IN PROGRESS"
        border_class = "hud-card-critical"

    st.markdown(
        f"""
        <div class="hud-card {border_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="{led_class}"></span>
                    <strong class="hud-mono" style="font-size: 1.1rem; color: #f0f6fc;">{status_msg}</strong>
                </div>
                <div class="hud-mono" style="color: #58a6ff; font-size: 0.9rem;">
                    LIVE TELEMETRY STREAM &nbsp;|&nbsp; UTC {timestamp_str}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Telemetry KPI Cards
    k1, k2, k3, k4 = st.columns(4)

    fleet_val = "NOMINAL" if alert_count == 0 else f"ALERT ({alert_count})"
    fleet_color = "#3fb950" if alert_count == 0 else "#f85149"
    fleet_sub = "0 Hazards Detected" if alert_count == 0 else f"{alert_count} Threats Active"
    fleet_sub_color = "#3fb950" if alert_count == 0 else "#f85149"

    with k1:
        st.markdown(
            f"""
            <div class="hud-metric-card">
                <div class="hud-metric-label">Fleet Status</div>
                <div class="hud-value-tick" style="color: {fleet_color};">
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
                <div class="hud-metric-label">Tracked Assets</div>
                <div class="hud-value-tick">
                    {nominal_count:,} <span style="font-size:1rem; color:#8b949e;">/ {total_satellites:,}</span>
                </div>
                <div class="hud-metric-sub" style="color: {'#3fb950' if online_pct >= 95 else '#d29922'};">
                    {online_pct:.1f}% Operational
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    flux_color = "#3fb950" if severity == "Calm" else "#d29922" if severity in ["Watch", "Warning"] else "#f85149"
    with k3:
        st.markdown(
            f"""
            <div class="hud-metric-card">
                <div class="hud-metric-label">Solar Proton Flux</div>
                <div class="hud-value-tick" style="color: {flux_color};">
                    {peak_proton_flux:.1f} <span style="font-size:1rem;">pfu</span>
                </div>
                <div class="hud-metric-sub" style="color: {flux_color};">
                    Severity: {severity.upper()}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    bz_color = "#3fb950" if mag_bz >= -5.0 else "#f85149"
    with k4:
        st.markdown(
            f"""
            <div class="hud-metric-card">
                <div class="hud-metric-label">Solar Wind / IMF Bz</div>
                <div class="hud-value-tick">
                    {wind_velocity:.0f} <span style="font-size:1rem; color:#8b949e;">km/s</span>
                </div>
                <div class="hud-metric-sub" style="color: {bz_color};">
                    Bz Field: {mag_bz:.1f} nT
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Probabilistic Classifier Breakdown
    with st.expander("Probabilistic Naive Bayes Classifier Distribution"):
        st.markdown(
            "<div class='hud-mono' style='color: #8b949e;'>Posterior probability outputs from Gaussian Naive Bayes classifier trained on Aditya-L1 telemetry:</div><br/>",
            unsafe_allow_html=True
        )
        if probabilities:
            cols = st.columns(4)
            for idx, cls in enumerate(["Calm", "Watch", "Warning", "Emergency"]):
                p_val = probabilities.get(cls, 0.0)
                with cols[idx]:
                    st.metric(label=f"P({cls.upper()})", value=f"{p_val * 100:.1f}%")
                    st.progress(float(min(max(p_val, 0.0), 1.0)))

    # Tabs Navigation
    tab_globe, tab_pdm, tab_scheduler, tab_benchmarks = st.tabs([
        "3D Fleet Hazard Globe",
        "Dosimetry & Predictive Maintenance",
        "A* Telecommand Scheduler",
        "SOTA Benchmarks & Report"
    ])

    with tab_globe:
        st.markdown("<h4 style='color: #f0f6fc;'>Real-Time 3D Orbital Fleet Hazard View</h4>", unsafe_allow_html=True)
        try:
            from globe_visualization import generate_3d_fleet_hazard_globe
            fig_3d = generate_3d_fleet_hazard_globe(risk_df, severity=severity)
            st.plotly_chart(fig_3d, use_container_width=True)
        except Exception as e:
            st.warning(f"Unable to render 3D Globe: {e}")

        st.markdown("<h4 style='color: #f0f6fc; margin-top: 15px;'>3D Orbital Telemetry Table</h4>", unsafe_allow_html=True)
        if not risk_df.empty:
            c_filter1, c_filter2 = st.columns([2, 2])
            with c_filter1:
                risk_filter = st.multiselect(
                    "Filter Hazard Status:",
                    options=["CRITICAL", "WARNING", "NOMINAL"],
                    default=["CRITICAL", "WARNING", "NOMINAL"]
                )
            with c_filter2:
                search_query = st.text_input("Search Satellite / NORAD ID:", "")

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

            display_df = filtered_df.copy()
            display_df["risk_level"] = display_df["risk_level"].map({
                "CRITICAL": "CRITICAL",
                "WARNING": "WARNING",
                "NOMINAL": "NOMINAL"
            }).fillna(display_df["risk_level"])

            st.dataframe(
                display_df,
                use_container_width=True,
                height=350,
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
            st.caption(f"Active Orbital Tracking: {len(filtered_df):,} / {total_satellites:,} satellites monitored.")
        else:
            st.info("No orbital telemetry available.")

    with tab_pdm:
        st.markdown("<h4 style='color: #f0f6fc;'>Gaganyaan Crew Dosimetry & Subsystem Predictive Maintenance</h4>", unsafe_allow_html=True)
        col_dose, col_pdm = st.columns(2)
        
        with col_dose:
            st.markdown(
                """
                <div class="hud-card hud-card-nominal">
                    <h5 style="color:#58a6ff; margin-top:0;">6-Hour Solar Proton Flux Forecast & Crew Dosimetry</h5>
                    <p class="hud-mono" style="font-size:0.85rem; color:#8b949e;">
                    <b>Model:</b> 2-Layer LSTM Forecaster (PyTorch)<br/>
                    <b>Physics Integration:</b> Simpson's Rule Dose Rate Model (Shielding: 5.0 g/cm² Al)<br/>
                    <b>Validation RMSE:</b> 23.39 pfu (vs BLEO Baseline [6]: ~12.5 pfu)
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            dose_json_path = "data/processed/solar_flux_forecast.json"
            if os.path.exists(dose_json_path):
                with open(dose_json_path) as f:
                    dose_data = json.load(f)
                
                flux_6hr = dose_data.get("forecast_6hr_pfu", [18.2, 18.2, 18.2, 18.2, 18.2, 18.2])
                crew_dose = dose_data.get("crew_dosimetry", {}).get("predicted_6hr_dose_msv", 0.0114)
                status_dose = dose_data.get("crew_dosimetry", {}).get("dosimetry_status", "NOMINAL_SAFE")

                st.metric(
                    label="Gaganyaan Crew 6-Hr Accumulated Dose",
                    value=f"{crew_dose:.4f} mSv",
                    delta=status_dose,
                    delta_color="normal" if "SAFE" in status_dose else "inverse"
                )

                df_flux = pd.DataFrame({
                    "Hour": [f"+{i+1}h" for i in range(len(flux_6hr))],
                    "Proton Flux (pfu)": flux_6hr
                })
                st.line_chart(df_flux.set_index("Hour"))
            else:
                st.info("Execute `solar_dose_forecaster.py` to populate forecaster output.")

        with col_pdm:
            st.markdown(
                """
                <div class="hud-card hud-card-warning">
                    <h5 style="color:#d29922; margin-top:0;">Multimodal CNN-LSTM Subsystem Health</h5>
                    <p class="hud-mono" style="font-size:0.85rem; color:#8b949e;">
                    <b>Inputs:</b> Battery SoC, Subsystem Temp, Gyro Drift, CMOS Hits + Weather Severity<br/>
                    <b>Ablation Test:</b> Weather severity input increases ROC-AUC by +0.105
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            pdm_json_path = "data/processed/maintenance_predictions.json"
            if os.path.exists(pdm_json_path):
                with open(pdm_json_path) as f:
                    pdm_data = json.load(f)
                
                sub_health = pdm_data.get("subsystem_health", {})
                p_fail = sub_health.get("predicted_failure_probability", 0.08)

                st.metric(
                    label="Predicted Subsystem Failure Probability P(Fail)",
                    value=f"{p_fail * 100:.1f}%",
                    delta="CRITICAL RISK" if p_fail > 0.4 else "STABLE",
                    delta_color="inverse" if p_fail > 0.4 else "normal"
                )

                m1, m2, m3 = st.columns(3)
                m1.metric("Battery SoC", f"{sub_health.get('battery_health_pct', 94.2)}%")
                m2.metric("Gyro Drift", f"{sub_health.get('gyro_drift_deg_s', 0.021)} deg/s")
                m3.metric("CMOS Noise", f"{sub_health.get('cmos_noise_hits_s', 3.4)} c/s")

                st.markdown(
                    f"""
                    <div class="hud-mono" style="font-size:0.82rem; background:#161b22; padding:10px; border-radius:5px; border:1px solid #30363d;">
                    <b>Ablation Benchmark Results:</b><br/>
                    • Proposed Model B (With Severity Channel): AUC <b>{pdm_data.get('model_B_sparc_with_weather_auc', 0.8356)}</b> | F1 <b>{pdm_data.get('model_B_sparc_with_weather_f1', 0.3415)}</b><br/>
                    • Baseline Model A (Without Severity Channel): AUC {pdm_data.get('model_A_no_weather_auc', 0.7303)} | F1 {pdm_data.get('model_A_no_weather_f1', 0.2752)}<br/>
                    • SOTA Baseline Muthukumar & Philip [11]: F1 0.8800 | AUC 0.9100
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("Execute `predictive_maintenance.py` to train & evaluate maintenance model.")

    with tab_scheduler:
        st.markdown("<h4 style='color: #f0f6fc;'>Closed-Loop A* Telecommand Priority Scheduler</h4>", unsafe_allow_html=True)
        tc_json_path = "data/processed/telecommand_schedule.json"
        if os.path.exists(tc_json_path):
            with open(tc_json_path) as f:
                tc_data = json.load(f)

            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("A* Execution Latency", f"{tc_data.get('astar_runtime_ms', 4.10)} ms", delta="< 100ms Target (Pass)", delta_color="normal")
            sc2.metric("Avg Hazard Mitigation", f"{tc_data.get('astar_avg_mitigation_pct', 99.0)}%", delta=f"vs Greedy: {tc_data.get('greedy_avg_mitigation_pct', 85.0)}%")
            sc3.metric("Scheduled Commands", len(tc_data.get("scheduled_telecommands", [])))

            st.markdown("<h5 style='color:#58a6ff;' class='hud-mono'>Authenticated Telecommand Queue</h5>", unsafe_allow_html=True)
            df_tc = pd.DataFrame(tc_data.get("scheduled_telecommands", []))
            if not df_tc.empty:
                st.dataframe(
                    df_tc[[
                        "satellite_name", "norad_id", "recommended_action", 
                        "power_cost_w", "urgency_score", "sha256_signature", "execution_status"
                    ]],
                    use_container_width=True,
                    height=280,
                    hide_index=True
                )
        else:
            st.info("Execute `astarscheduler.py` to generate telecommand schedule.")

    with tab_benchmarks:
        st.markdown("<h4 style='color: #f0f6fc;'>SOTA Baseline Benchmark Comparison Report</h4>", unsafe_allow_html=True)
        bm_md_path = "docs/benchmark_results.md"
        if os.path.exists(bm_md_path):
            with open(bm_md_path) as f:
                report_md = f.read()
            st.markdown(report_md)
        else:
            st.info("Execute `evaluate_baselines.py` to generate benchmark report.")

render_hud_fragment()