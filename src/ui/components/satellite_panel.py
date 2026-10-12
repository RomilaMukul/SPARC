"""
SPARC-PM: Selected Satellite Information & Action Panel
======================================================
Detailed telemetry card for the selected spacecraft in the Orbital Monitor view.
Includes 'WHY?' explanation breakdown and 'ADD RESPONSE TO QUEUE' action.
"""

from __future__ import annotations

from typing import Any, Dict
import streamlit as st

from src.ui.components.html_utils import render_html
from src.ui.components.status_badge import render_status_badge


def render_satellite_panel(sat: Dict[str, Any], severity_report: Dict[str, Any], telemetry: Dict[str, Any]) -> None:
    """Renders selected satellite telemetry, status, risk, why rationale, and queue action."""
    sat_name = sat.get("name", "UNSPECIFIED SATELLITE")
    sat_id = sat.get("sat_id", "SAT-000")
    orbit_type = sat.get("orbit_type", "LEO")
    alert = sat.get("alert_level", "NOMINAL")
    hazard_ratio = sat.get("hazard_ratio", 0.0)
    alt_km = sat.get("altitude_km", 0.0)
    speed = sat.get("speed_kms", 0.0)
    dist_storm = sat.get("dist_to_storm_km", 0.0)
    criticality = sat.get("criticality", 0.5)

    alert_colors = {
        "CRITICAL": "#ef4444",
        "WARNING": "#f59e0b",
        "ELEVATED": "#3b82f6",
        "NOMINAL": "#10b981",
    }
    theme_col = alert_colors.get(alert, "#10b981")

    badge_html = render_status_badge(alert, alert)

    rec_cmd = (
        "ENTER_SAFE_MODE" if alert == "CRITICAL"
        else "ATTITUDE_SHIELD_TILT" if alert == "WARNING"
        else "ENHANCED_TELEMETRY_POLL" if alert == "ELEVATED"
        else "NOMINAL_ROUTINE"
    )

    sev_label = severity_report.get("severity_label", "N/A")
    triage = severity_report.get("triage", "GREEN")
    p_flux = telemetry.get("proton_flux_pfu", 0.0)
    sw_speed = telemetry.get("proton_speed_kms", 0.0)
    imf_bz = telemetry.get("mag_bz_field", 0.0)

    render_html(f"""
        <div style="background: #0b132b; border: 1px solid rgba(66, 217, 245, 0.25); border-radius: 8px; padding: 14px 16px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);">
            <!-- Panel Header -->
            <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(148, 163, 184, 0.12); padding-bottom: 10px; margin-bottom: 12px;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{theme_col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
                        </svg>
                        <span style="font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1.05rem; color: #f8fafc; letter-spacing: 0.3px;">
                            {sat_name}
                        </span>
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8; margin-top: 2px;">
                        ID: <span style="color: #cbd5e1;">{sat_id}</span> • ORBIT: <span style="color: #42d9f5;">{orbit_type}</span> • CRIT: <span style="color: #cbd5e1;">{criticality:.2f}</span>
                    </div>
                </div>
                <div>
                    {badge_html}
                </div>
            </div>

            <!-- 4-Metric Telemetry HUD Grid -->
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 14px;">
                <div style="background: #080d17; border: 1px solid rgba(148, 163, 184, 0.1); padding: 8px 10px; border-radius: 6px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #64748b; text-transform: uppercase;">HAZARD RATIO H_j</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.15rem; color: {theme_col};">{hazard_ratio:.4f}</div>
                </div>
                <div style="background: #080d17; border: 1px solid rgba(148, 163, 184, 0.1); padding: 8px 10px; border-radius: 6px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #64748b; text-transform: uppercase;">ALTITUDE</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.15rem; color: #f8fafc;">{alt_km:,.1f} <span style="font-size:0.7rem;color:#64748b;">km</span></div>
                </div>
                <div style="background: #080d17; border: 1px solid rgba(148, 163, 184, 0.1); padding: 8px 10px; border-radius: 6px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #64748b; text-transform: uppercase;">ORBITAL VELOCITY</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.15rem; color: #f8fafc;">{speed:.3f} <span style="font-size:0.7rem;color:#64748b;">km/s</span></div>
                </div>
                <div style="background: #080d17; border: 1px solid rgba(148, 163, 184, 0.1); padding: 8px 10px; border-radius: 6px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #64748b; text-transform: uppercase;">STORM DISTANCE</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.15rem; color: #f8fafc;">{dist_storm:,.1f} <span style="font-size:0.7rem;color:#64748b;">km</span></div>
                </div>
            </div>

            <!-- Engineering WHY Rationale 3-Tier Breakdown -->
            <div style="background: #080d17; border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 6px; padding: 10px 12px; margin-bottom: 12px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 700; color: #60a5fa; margin-bottom: 6px; text-transform: uppercase; display: flex; align-items: center; gap: 5px;">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2.5"><rect x="4" y="4" width="16" height="16" rx="2"></rect><rect x="9" y="9" width="6" height="6"></rect></svg>
                    1. MODEL FSM INFERENCE
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8; margin-bottom: 2px;">
                    <span>Space Weather Level:</span><span style="color:#f8fafc;font-weight:600;">{sev_label}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8; margin-bottom: 2px;">
                    <span>FSM Triage State:</span><span style="color:{theme_col};font-weight:600;">{triage}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8;">
                    <span>Spacecraft Alert Status:</span><span style="color:{theme_col};font-weight:600;">{alert}</span>
                </div>
            </div>

            <div style="background: #080d17; border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 6px; padding: 10px 12px; margin-bottom: 12px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 700; color: #fbbf24; margin-bottom: 6px; text-transform: uppercase; display: flex; align-items: center; gap: 5px;">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2.5"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line></svg>
                    2. PHYSICS EVIDENCE
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8; margin-bottom: 2px;">
                    <span>Solar Proton Flux:</span><span style="color:#f8fafc;font-weight:600;">{p_flux:.1f} pfu</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8; margin-bottom: 2px;">
                    <span>Solar Wind Velocity:</span><span style="color:#f8fafc;font-weight:600;">{sw_speed:.0f} km/s</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8;">
                    <span>IMF Bz Field:</span><span style="color:#f8fafc;font-weight:600;">{imf_bz:+.1f} nT</span>
                </div>
            </div>

            <div style="background: #080d17; border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 6px; padding: 10px 12px; margin-bottom: 6px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 700; color: #34d399; margin-bottom: 6px; text-transform: uppercase; display: flex; align-items: center; gap: 5px;">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                    3. RECOMMENDED DIRECTIVE
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8; margin-bottom: 2px;">
                    <span>Mitigation Action:</span><span style="color:#34d399;font-weight:700;">{rec_cmd}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8; margin-bottom: 2px;">
                    <span>Subsystem Target:</span><span style="color:#cbd5e1;">Payload / Power Bus</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #94a3b8;">
                    <span>Priority Tier:</span><span style="color:{theme_col};font-weight:600;">{alert}</span>
                </div>
            </div>
        </div>
    """)

    # Action Dispatch Button
    st.write("")
    if st.button(
        f"➕ QUEUE [{rec_cmd}] IN A* SCHEDULER",
        key=f"btn_add_queue_{sat_name}",
        use_container_width=True,
        type="primary" if alert in ["CRITICAL", "WARNING"] else "secondary",
    ):
        queue = st.session_state.get("manual_command_queue", [])
        queue.append({
            "satellite": sat_name,
            "action": rec_cmd,
            "urgency": alert,
            "timestamp": st.session_state.get("pipeline_results", {}).get("timestamp", "NOW"),
        })
        st.session_state["manual_command_queue"] = queue
        st.success(f"✅ Directive [{rec_cmd}] queued for {sat_name}! Visit Command Center to verify HMAC.")

