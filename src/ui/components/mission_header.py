"""
SPARC-PM: Mission Control Header Component
==========================================
Standardized engineering header for all mission operations pages.
"""

from __future__ import annotations

from datetime import datetime, timezone
import streamlit as st

from src.ui.components.html_utils import render_html
from src.ui.components.status_badge import render_status_badge, render_led


def render_mission_header(page_title: str, subtitle: str) -> None:
    """Renders a clean, high-density aerospace mission header."""
    results = st.session_state.get("pipeline_results", {})
    sev = results.get("severity_report", {})
    triage = sev.get("triage", "GREEN")
    sev_label = sev.get("severity_label", "G0_NOMINAL_QUIET")
    scenario_name = results.get("scenario_name", "NOMINAL")
    utc_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    col_title, col_info = st.columns([2.5, 1.5])

    with col_title:
        led_html = render_led(triage)
        render_html(f"""
            <div style="padding: 4px 0;">
                <div style="font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1.35rem; color: #f8fafc; letter-spacing: 0.5px; text-transform: uppercase; display: flex; align-items: center;">
                    {led_html} {page_title}
                </div>
                <div style="font-family: 'Space Mono', monospace; font-size: 0.8rem; color: #94a3b8; margin-top: 2px;">
                    {subtitle}
                </div>
            </div>
        """)

    with col_info:
        badge_html = render_status_badge(sev_label, triage)
        render_html(f"""
            <div style="background: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 8px 12px; text-align: right;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-family: 'Space Mono', monospace; font-size: 0.72rem; color: #94a3b8;">SYSTEM STATE</span>
                    {badge_html}
                </div>
                <div style="font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #e2e8f0; margin-top: 4px;">
                    {utc_str}
                </div>
            </div>
        """)

    st.markdown("<hr style='border:none; border-top:1px solid #1e293b; margin: 10px 0 16px 0;'/>", unsafe_allow_html=True)
