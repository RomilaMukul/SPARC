"""
SPARC-PM: Aerospace Mission Control Command Center
==================================================
Professional, high-density aerospace mission-control console.
Synchronizes SGP4 orbital tracking, A* heuristic decision scoring,
HMAC-SHA256 cryptographic frames, 10s safety interlocks, and event audit trails.
Uses render_html to prevent CommonMark code-block rendering bugs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
import streamlit as st

from src.ui.components.command_queue import render_command_queue
from src.ui.components.command_inspector import render_command_inspector
from src.ui.components.decision_explanation import render_decision_explanation
from src.ui.components.human_review_interlock import render_human_review_interlock
from src.ui.components.command_audit_log import render_command_audit_log
from src.ui.components.orbital_situational_panel import render_orbital_situational_panel
from src.ui.components.html_utils import render_html


def render_command_center_page() -> None:
    """Renders the comprehensive 8-section aerospace Command Center console."""
    results = st.session_state.get("pipeline_results", {})
    cmds = results.get("scheduled_commands", {})
    hazards = results.get("hazard_report", {})
    fleet_hazard_profile = hazards.get("fleet_hazard_profile", [])
    storm_radius = hazards.get("storm_corridor_radius_km", 45000.0)

    queue: List[Dict[str, Any]] = cmds.get("command_queue", [])
    allocated_power = float(cmds.get("allocated_power_w", 0.0))
    max_power = float(cmds.get("max_power_budget_w", 600.0))
    latency_ms = float(cmds.get("scheduler_latency_ms", 0.0))
    latency_compliant = bool(cmds.get("latency_compliant", latency_ms < 50.0))
    max_slots = int(cmds.get("max_commands_per_pass", 15))
    total_evaluated = int(cmds.get("total_candidates_evaluated", len(fleet_hazard_profile)))
    scenario_name = results.get("scenario_name", "ACTIVE BENCHMARK")
    is_live = bool(results.get("is_live", False))

    # A. Mission Header (Aerospace Telemetry Top Strip)
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    feed_badge_color = "#45D6A0" if is_live else "#42D9F5"
    feed_label = "ADITYA-L1 SWIS (LIVE FEED)" if is_live else f"TELEMETRY: SIMULATED ({scenario_name})"

    header_html = (
        f'<div style="background: #080D17; border-bottom: 1px solid rgba(66, 217, 245, 0.22); padding: 9px 18px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">'
        f'<div style="display: flex; align-items: center; gap: 12px;">'
        f'<span style="font-family: \'JetBrains Mono\', monospace; font-size: 1.05rem; font-weight: 800; color: #42D9F5; letter-spacing: 1px;">SPARC-PM</span>'
        f'<span style="color: #64748b; font-size: 0.8rem;">|</span>'
        f'<span style="font-family: \'Inter\', sans-serif; font-size: 0.82rem; font-weight: 700; color: #f8fafc; letter-spacing: 0.5px;">MISSION OPERATIONS COMMAND CENTER</span>'
        f'<span style="background: rgba(66, 217, 245, 0.12); color: #42D9F5; border: 1px solid rgba(66, 217, 245, 0.28); border-radius: 4px; padding: 1px 7px; font-family: \'JetBrains Mono\', monospace; font-size: 0.65rem; font-weight: 700;">A* ACTIVE</span>'
        f'</div>'
        f'<div style="display: flex; align-items: center; gap: 16px; font-family: \'JetBrains Mono\', monospace; font-size: 0.72rem; color: #94a3b8;">'
        f'<span>STATION: <b style="color: #f8fafc;">ISTRAC BLR-01</b></span>'
        f'<span>FEED: <b style="color: {feed_badge_color};">{feed_label}</b></span>'
        f'<span>CLOCK: <b style="color: #42D9F5;">{utc_now}</b></span>'
        f'</div>'
        f'</div>'
    )
    render_html(header_html)

    # B. Resource Status Strip with Real Progress Bars
    crit_count = sum(1 for c in queue if c.get("urgency_tier") == "CRITICAL")
    warn_count = sum(1 for c in queue if c.get("urgency_tier") == "WARNING")
    power_pct = (allocated_power / max_power * 100.0) if max_power > 0 else 0.0
    power_color = "#FF647C" if power_pct > 85 else ("#FFBD59" if power_pct > 60 else "#45D6A0")
    crit_color = "#FF647C" if crit_count > 0 else ("#FFBD59" if warn_count > 0 else "#45D6A0")
    slots_pct = (len(queue) / max_slots * 100.0) if max_slots > 0 else 0.0
    lat_bar_pct = min(100.0, (latency_ms / 50.0) * 100.0)
    lat_status_label = f"{latency_ms:.2f} ms <span style=\"font-size: 0.68rem; color: #45D6A0; font-weight: 400;\">• COMPLIANT (&lt;50ms)</span>" if latency_compliant else f"{latency_ms:.2f} ms <span style=\"font-size: 0.68rem; color: #FFBD59; font-weight: 400;\">• ELEVATED</span>"
    lat_color = "#45D6A0" if latency_compliant else "#FFBD59"

    strip_html = (
        f'<div style="background: #111B2B; border: 1px solid rgba(66, 217, 245, 0.18); border-radius: 6px; padding: 12px 16px; margin-bottom: 14px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; font-family: \'JetBrains Mono\', monospace;">'
        f'<div style="border-right: 1px solid rgba(148, 163, 184, 0.1); padding-right: 10px;">'
        f'<div style="font-size: 0.65rem; color: #64748b; text-transform: uppercase;">POWER ALLOCATION</div>'
        f'<div style="font-size: 0.95rem; font-weight: 700; color: {power_color}; margin-top: 2px;">{allocated_power:.1f} W <span style="font-size: 0.7rem; color: #94a3b8; font-weight: 400;">/ {max_power:.0f} W ({power_pct:.1f}%)</span></div>'
        f'<div style="width: 100%; height: 4px; background: rgba(148, 163, 184, 0.15); border-radius: 2px; margin-top: 6px; overflow: hidden;"><div style="width: {min(100.0, power_pct):.1f}%; height: 100%; background: {power_color}; border-radius: 2px;"></div></div>'
        f'</div>'
        f'<div style="border-right: 1px solid rgba(148, 163, 184, 0.1); padding-right: 10px;">'
        f'<div style="font-size: 0.65rem; color: #64748b; text-transform: uppercase;">UPLINK PASS CAPACITY</div>'
        f'<div style="font-size: 0.95rem; font-weight: 700; color: #42D9F5; margin-top: 2px;">{len(queue)} <span style="font-size: 0.7rem; color: #94a3b8; font-weight: 400;">/ {max_slots} SLOTS SCHEDULED</span></div>'
        f'<div style="width: 100%; height: 4px; background: rgba(148, 163, 184, 0.15); border-radius: 2px; margin-top: 6px; overflow: hidden;"><div style="width: {min(100.0, slots_pct):.1f}%; height: 100%; background: #42D9F5; border-radius: 2px;"></div></div>'
        f'</div>'
        f'<div style="border-right: 1px solid rgba(148, 163, 184, 0.1); padding-right: 10px;">'
        f'<div style="font-size: 0.65rem; color: #64748b; text-transform: uppercase;">CRITICAL ALERTS</div>'
        f'<div style="font-size: 0.95rem; font-weight: 700; color: {crit_color}; margin-top: 2px;">{crit_count} CRITICAL <span style="font-size: 0.7rem; color: #FFBD59; font-weight: 400;">• {warn_count} WARNING</span></div>'
        f'<div style="width: 100%; height: 4px; background: rgba(148, 163, 184, 0.15); border-radius: 2px; margin-top: 6px; overflow: hidden;"><div style="width: {min(100.0, (crit_count * 20.0 + warn_count * 10.0)):.1f}%; height: 100%; background: {crit_color}; border-radius: 2px;"></div></div>'
        f'</div>'
        f'<div>'
        f'<div style="font-size: 0.65rem; color: #64748b; text-transform: uppercase;">SCHEDULER ENGINE LATENCY</div>'
        f'<div style="font-size: 0.95rem; font-weight: 700; color: {lat_color}; margin-top: 2px;">{lat_status_label}</div>'
        f'<div style="width: 100%; height: 4px; background: rgba(148, 163, 184, 0.15); border-radius: 2px; margin-top: 6px; overflow: hidden;"><div style="width: {lat_bar_pct:.1f}%; height: 100%; background: {lat_color}; border-radius: 2px;"></div></div>'
        f'</div>'
        f'</div>'
    )
    render_html(strip_html)

    # Selection State Management
    if "command_center_selected_sat_id" not in st.session_state:
        if queue:
            st.session_state["command_center_selected_sat_id"] = queue[0].get("sat_id", "ISRO-001")
        elif fleet_hazard_profile:
            st.session_state["command_center_selected_sat_id"] = fleet_hazard_profile[0].get("sat_id", "ISRO-001")
        else:
            st.session_state["command_center_selected_sat_id"] = "ISRO-001"

    curr_selected_sat_id = st.session_state["command_center_selected_sat_id"]

    # Main Two-Column Flight Deck Layout
    col_deck_left, col_deck_right = st.columns([1.1, 0.9])

    with col_deck_left:
        # C. A* Prioritized Command Queue
        render_html(
            '<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.88rem; color: #f8fafc; text-transform: uppercase; margin-bottom: 4px; display: flex; align-items: center; justify-content: space-between;">'
            '<span>📋 A* OPTIMIZED TELECOMMAND QUEUE</span>'
            '<span style="font-size: 0.7rem; color: #42D9F5; font-family: \'JetBrains Mono\', monospace;">PRIORITIZED BY SEARCH HEURISTIC f(n)</span>'
            '</div>'
        )

        selected_cmd = render_command_queue(cmds, selected_sat_id=curr_selected_sat_id)
        if selected_cmd:
            st.session_state["command_center_selected_sat_id"] = selected_cmd.get("sat_id", curr_selected_sat_id)
            curr_selected_sat_id = selected_cmd.get("sat_id", curr_selected_sat_id)

        st.write("")

        # F. Decision Explanation Panel (A* Formula & Constraints)
        render_decision_explanation(
            selected_command=selected_cmd,
            total_evaluated=total_evaluated,
            scheduled_count=len(queue),
            max_power_budget_w=max_power,
            allocated_power_w=allocated_power,
        )

    with col_deck_right:
        # D. Orbital Situational Awareness Panel (Map + Tracking)
        render_html(
            '<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.88rem; color: #f8fafc; text-transform: uppercase; margin-bottom: 4px; display: flex; align-items: center; justify-content: space-between;">'
            '<span>🌐 SGP4 ORBITAL SITUATIONAL MAP</span>'
            '<span style="font-size: 0.7rem; color: #42D9F5; font-family: \'JetBrains Mono\', monospace;">GROUND TRACK SYNCHRONIZED</span>'
            '</div>'
        )
        render_orbital_situational_panel(
            fleet_hazard_profile=fleet_hazard_profile,
            selected_sat_id=curr_selected_sat_id,
            storm_radius_km=storm_radius,
        )

        st.write("")

        # E. Selected-Command Inspector (HMAC vs Hash Verification)
        render_command_inspector(selected_command=selected_cmd)

    # Bottom Row: G. Human Review Panel & H. Event Timeline
    render_html("<hr style='border: none; border-top: 1px solid rgba(66, 217, 245, 0.15); margin: 18px 0 14px 0;'/>")
    col_bot_left, col_bot_right = st.columns([1, 1])

    with col_bot_left:
        # G. Human Review Interlock (Fail-Closed)
        render_human_review_interlock(selected_command=selected_cmd)

    with col_bot_right:
        # H. Event Timeline
        render_command_audit_log()
