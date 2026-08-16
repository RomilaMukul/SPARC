import sys
import os
import datetime
import pandas as pd
import streamlit as st

# Ensure root & src directories are in python path so modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

st.set_page_config(
    page_title="SPARC-PM Mission Control",
    page_icon="🚀",
    layout="wide"
)

# Header & Refresh Button
head_col1, head_col2 = st.columns([5, 1])
with head_col1:
    st.title("🚀 SPARC-PM: Mission Control Dashboard")
    st.subheader("Space Particle Radiation Alert & Resilience Center — Predictive Maintenance")

with head_col2:
    st.write("")
    if st.button("🔄 Refresh Pipeline"):
        st.cache_data.clear()
        st.rerun()

# -----------------------------------------------------------------------------
# Cached Snapshot Ingestion Pipeline
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_snapshot():
    from dashboard_data import get_dashboard_snapshot
    return get_dashboard_snapshot()

try:
    snapshot = load_snapshot()
except (FileNotFoundError, Exception) as e:
    st.error("⚠️ Pipeline Data Missing or Uninitialized")
    st.warning(f"Error loading pipeline: {e}")
    st.info(
        "Please run the data ingestion pipelines first:\n\n"
        "```bash\n"
        "python src/fetch_celestrak.py\n"
        "python src/parse_aditya.py\n"
        "```"
    )
    st.stop()

# -----------------------------------------------------------------------------
# Data Extraction & Metrics Calculation
# -----------------------------------------------------------------------------
severity = snapshot.get("severity", "Calm")
probabilities = snapshot.get("severity_probabilities", {})
timestamp = snapshot.get("severity_timestamp", "N/A")
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

# -----------------------------------------------------------------------------
# Top-Level KPI Metrics
# -----------------------------------------------------------------------------
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

with kpi_col1:
    fleet_status = "NOMINAL" if alert_count == 0 else f"ALERT ({alert_count} Risks)"
    st.metric(
        label="Global Fleet Status",
        value=fleet_status,
        delta=f"{alert_count} Alerts",
        delta_color="inverse" if alert_count > 0 else "normal"
    )

with kpi_col2:
    st.metric(
        label="Active Satellites Tracked",
        value=f"{nominal_count:,} / {total_satellites:,}",
        delta=f"{online_pct:.1f}% Nominal",
        delta_color="normal" if online_pct >= 95 else "inverse"
    )

with kpi_col3:
    st.metric(
        label="Peak Solar Proton Flux",
        value=f"{peak_proton_flux:.1f} pfu",
        delta=f"Severity: {severity}",
        delta_color="normal" if severity == "Calm" else "inverse"
    )

st.divider()

# -----------------------------------------------------------------------------
# Dynamic Severity Alert Banner
# -----------------------------------------------------------------------------
timestamp_str = f"UTC Timestamp: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"

if severity == "Calm":
    st.success(f"🟢 System Operational — Calm Conditions | Aditya-L1 Ingestion Stream Active | {timestamp_str}")
elif severity == "Watch":
    st.info(f"🟡 Space Weather Watch — Minor Solar Disturbance Detected | Aditya-L1 Ingestion Stream Active | {timestamp_str}")
elif severity == "Warning":
    st.warning(f"🟠 Space Weather Warning — Elevated Solar Radiation Alert | Aditya-L1 Ingestion Stream Active | {timestamp_str}")
elif severity == "Emergency":
    st.error(f"🔴 SPACE WEATHER EMERGENCY — Severe Solar Flare / Proton Event in Progress! | Aditya-L1 Ingestion Stream Active | {timestamp_str}")
else:
    st.info(f"🔵 Status: {severity} | Aditya-L1 Ingestion Stream Active | {timestamp_str}")

# -----------------------------------------------------------------------------
# Model Transparency Expander (Viva Transparency)
# -----------------------------------------------------------------------------
with st.expander("🔍 Model Transparency: Naive Bayes Severity Class Probabilities"):
    st.markdown(
        "**Naive Bayes Classifier Output Breakdown:** Shows the estimated posterior probability "
        "distribution across solar weather severity classes for the current telemetry snapshot."
    )
    if probabilities:
        all_classes = ["Calm", "Watch", "Warning", "Emergency"]
        prob_cols = st.columns(len(all_classes))
        for idx, cls_name in enumerate(all_classes):
            prob_val = probabilities.get(cls_name, 0.0)
            with prob_cols[idx]:
                st.metric(label=f"P({cls_name})", value=f"{prob_val * 100:.1f}%")
                st.progress(float(min(max(prob_val, 0.0), 1.0)))
    else:
        st.write("No probability distribution available.")

st.divider()

# -----------------------------------------------------------------------------
# Satellite Risk Assessment Table (DA1 Core Requirement)
# -----------------------------------------------------------------------------
st.subheader("🛰️ Satellite Risk Assessment (3D Proximity & Orbit Mechanics)")
st.caption(
    "Propagated via SGP4 and 3D Euclidean proximity analysis against space weather storm corridors "
    "(South Atlantic Anomaly, Auroral Ovals). Risk levels adjust dynamically based on live Naive Bayes severity classification."
)

if not risk_df.empty:
    filter_col1, filter_col2 = st.columns([2, 2])
    with filter_col1:
        risk_filter = st.multiselect(
            "Filter by Risk Level:",
            options=["CRITICAL", "WARNING", "NOMINAL"],
            default=["CRITICAL", "WARNING", "NOMINAL"]
        )
    with filter_col2:
        search_query = st.text_input("Search Satellite Name / NORAD ID:", "")

    filtered_df = risk_df[risk_df["risk_level"].isin(risk_filter)].copy()
    if search_query:
        query = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["name"].str.lower().str.contains(query) |
            filtered_df["norad_id"].astype(str).str.contains(query)
        ]

    risk_order = {"CRITICAL": 0, "WARNING": 1, "NOMINAL": 2}
    filtered_df["sort_key"] = filtered_df["risk_level"].map(risk_order)
    filtered_df = filtered_df.sort_values("sort_key").drop(columns=["sort_key"])

    def style_risk_table(df):
        def highlight_risk(val):
            if val == "CRITICAL":
                return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
            elif val == "WARNING":
                return "background-color: #fff3cd; color: #856404; font-weight: bold;"
            elif val == "NOMINAL":
                return "background-color: #d4edda; color: #155724; font-weight: bold;"
            return ""

        return df.style.map(highlight_risk, subset=["risk_level"])

    styled_table = style_risk_table(filtered_df)
    st.dataframe(
        styled_table,
        use_container_width=True,
        height=400,
        column_config={
            "name": "Satellite Name",
            "norad_id": "NORAD ID",
            "lat": st.column_config.NumberColumn("Latitude (°)", format="%.2f"),
            "lon": st.column_config.NumberColumn("Longitude (°)", format="%.2f"),
            "alt_km": st.column_config.NumberColumn("Altitude (km)", format="%.1f"),
            "nearest_corridor": "Nearest Hazard Corridor",
            "distance_km": st.column_config.NumberColumn("Corridor Distance (km)", format="%.1f"),
            "risk_level": "Risk Level",
        }
    )
    st.caption(f"Displaying {len(filtered_df):,} of {total_satellites:,} satellites.")
else:
    st.info("No satellite risk data available.")