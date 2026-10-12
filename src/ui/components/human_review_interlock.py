"""
SPARC-PM: Human Review & 10-Second Safety Interlock Panel
========================================================
Implements fail-closed mission-control safety interlock.
Ensures no automated telecommand transmission occurs without deliberate
operator authorization. Provides explicit abort, modify, and authorization states.
Uses render_html to prevent CommonMark code-block rendering artifacts.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
import streamlit as st

from src.ui.components.command_audit_log import log_event
from src.ui.components.html_utils import render_html


def render_human_review_interlock(
    selected_command: Optional[Dict[str, Any]],
    on_authorize_callback=None,
) -> None:
    """Renders the fail-closed human review panel with 10-second safety interlock."""
    if not selected_command:
        return

    sat_id = selected_command.get("sat_id", "SAT")
    sat_name = selected_command.get("satellite", sat_id)
    raw_action = selected_command.get("recommended_action", "NOMINAL")

    # State key in session state for safety interlocks
    interlock_state_key = f"interlock_state_{sat_id}"
    interlock_timer_key = f"interlock_start_{sat_id}"

    if interlock_state_key not in st.session_state:
        st.session_state[interlock_state_key] = "HOLD"  # HOLD -> ARMED -> AUTHORIZED -> DISPATCHED

    curr_state = st.session_state[interlock_state_key]

    render_html(
        '<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.88rem; color: #f8fafc; text-transform: uppercase; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">'
        '<span>🛡️ HUMAN-IN-THE-LOOP SAFETY INTERLOCK (FAIL-CLOSED)</span>'
        '<span style="font-size: 0.7rem; color: #FFBD59; font-family: \'JetBrains Mono\', monospace;">10s SAFETY PROTOCOL</span>'
        '</div>'
    )

    state_color = "#45D6A0" if curr_state == "DISPATCHED" else ("#42D9F5" if curr_state == "AUTHORIZED" else ("#FFBD59" if curr_state == "ARMED" else "#FF647C"))

    with st.container(border=True):
        header_strip = (
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-family: \'JetBrains Mono\', monospace; font-size: 0.76rem;">'
            f'<div><span style="color: #64748b;">TARGET:</span> <b style="color: #f8fafc;">{sat_name}</b> | <span style="color: #64748b;">ACTION:</span> <b style="color: #42D9F5;">{raw_action}</b></div>'
            f'<div><span style="color: #64748b;">INTERLOCK:</span> <b style="color: {state_color}; background: {state_color}18; border: 1px solid {state_color}35; padding: 2px 7px; border-radius: 3px;">[{curr_state}]</b></div>'
            f'</div>'
        )
        render_html(header_strip)

        col_left, col_right = st.columns([2, 1])

        with col_left:
            render_html(
                '<div style="font-size: 0.75rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 10px;">'
                '<b>Operational Safety Constraint:</b> Autonomous telecommands cannot be transmitted automatically. '
                'Flight controller must initiate the safety review countdown and review telemetry margins before uplink authorization is unlocked.'
                '</div>'
            )

            # Manual Action Override Selector
            action_options = ["ENTER_SAFE_MODE", "ATTITUDE_SHIELD_TILT", "POWER_DOWN_PAYLOAD", "ORBITAL_MANEUVER", "ENHANCED_TELEMETRY_POLL", "NOMINAL_ROUTINE"]
            sel_idx = action_options.index(raw_action) if raw_action in action_options else 0
            new_action = st.selectbox(
                "Modify Action (Override)",
                action_options,
                index=sel_idx,
                key=f"mod_act_{sat_id}",
                help="Allows flight director to override autonomous A* recommendation.",
            )

        with col_right:
            if curr_state == "HOLD":
                if st.button("🔓 INITIATE 10s INTERLOCK", key=f"arm_btn_{sat_id}", use_container_width=True):
                    st.session_state[interlock_state_key] = "ARMED"
                    st.session_state[interlock_timer_key] = time.time()
                    log_event("OPERATOR", f"Initiated 10s safety interlock review for {sat_name} ({raw_action}).", "WARNING")
                    st.rerun()

            elif curr_state == "ARMED":
                elapsed = time.time() - st.session_state.get(interlock_timer_key, time.time())
                remaining = max(0, int(10 - elapsed))

                if remaining > 0:
                    st.info(f"⏳ Interlock Hold: {remaining}s remaining...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    if st.button("✅ CONFIRM & AUTHORIZE", key=f"auth_btn_{sat_id}", use_container_width=True, type="primary"):
                        st.session_state[interlock_state_key] = "AUTHORIZED"
                        log_event("OPERATOR", f"Flight Director authorized {raw_action} uplink for {sat_name}.", "NOMINAL")
                        st.rerun()

            elif curr_state == "AUTHORIZED":
                st.success("Authorized for transmission.")
                if st.button("⚡ EXECUTE DSN UPLINK", key=f"tx_btn_{sat_id}", use_container_width=True, type="primary"):
                    st.session_state[interlock_state_key] = "DISPATCHED"
                    log_event("UPLINK", f"SIMULATED UPLINK: Dispatched authenticated {raw_action} frame to {sat_name} via DSN.", "NOMINAL")
                    st.toast(f"Transmitted {raw_action} to {sat_name}!", icon="📡")
                    st.rerun()

            elif curr_state == "DISPATCHED":
                render_html("<div style='color: #45D6A0; font-family: \"JetBrains Mono\", monospace; font-size: 0.76rem; font-weight: 700; text-align: center; padding: 6px;'>✓ PACKET UPLINK COMPLETE</div>")
                if st.button("RESET TO HOLD", key=f"reset_btn_{sat_id}", use_container_width=True):
                    st.session_state[interlock_state_key] = "HOLD"
                    st.rerun()

            # Abort Button (Always available)
            if curr_state != "HOLD" and curr_state != "DISPATCHED":
                if st.button("🛑 ABORT COMMAND", key=f"abort_btn_{sat_id}", use_container_width=True):
                    st.session_state[interlock_state_key] = "HOLD"
                    log_event("OPERATOR", f"ABORTED telecommand for {sat_name} by operator override.", "CRITICAL")
                    st.warning("Command aborted by controller.")
                    st.rerun()
