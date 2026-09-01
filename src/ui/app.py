import streamlit as st
import datetime

st.set_page_config(
    page_title="SPARC-PM Mission Control",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 SPARC-PM: Mission Control Dashboard")
st.subheader("Space Particle Radiation Alert & Resilience Center — Predictive Maintenance")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Global Fleet Status", value="NOMINAL", delta="0 Alerts")
with col2:
    st.metric(label="Active Satellites", value="24 / 24", delta="100% Online")
with col3:
    st.metric(label="Peak Proton Flux", value="12.4 pfu", delta="Normal Range")

st.divider()

st.success("🟢 System Operational | Aditya-L1 PAPA/ASPEX Ingestion Stream Active")
st.info(f"UTC Timestamp: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")