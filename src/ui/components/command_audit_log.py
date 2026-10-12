"""
SPARC-PM: Command Center Event Timeline & Audit Log
===================================================
Maintains a verifiable, chronological audit log of all scheduling events,
validation checks, operator authorizations, aborts, and simulated dispatches.
Uses render_html to prevent CommonMark code-block rendering artifacts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
import streamlit as st

from src.ui.components.html_utils import render_html


def init_audit_log() -> None:
    """Initializes audit log in session state if not present."""
    if "command_center_audit_log" not in st.session_state:
        st.session_state["command_center_audit_log"] = [
            {
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
                "source": "SCHEDULER",
                "severity": "NOMINAL",
                "message": "A* Action Scheduler initialized with 600W power ceiling & 15-cmd pass limit.",
            },
            {
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
                "source": "CRYPTO",
                "severity": "NOMINAL",
                "message": "RFC 2104 HMAC-SHA256 signature engine online with ISTRAC ground station key.",
            },
        ]


def log_event(source: str, message: str, severity: str = "NOMINAL") -> None:
    """Appends an event to the session audit log."""
    init_audit_log()
    st.session_state["command_center_audit_log"].insert(
        0,
        {
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
            "source": source,
            "severity": severity,
            "message": message,
        },
    )
    st.session_state["command_center_audit_log"] = st.session_state["command_center_audit_log"][:50]


def render_command_audit_log() -> None:
    """Renders the event timeline component using sanitized HTML."""
    init_audit_log()
    events: List[Dict[str, Any]] = st.session_state.get("command_center_audit_log", [])

    render_html(
        '<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.88rem; color: #f8fafc; text-transform: uppercase; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">'
        '<span>⏱️ GROUND STATION EVENT & UPLINK TIMELINE</span>'
        '<span style="font-size: 0.7rem; color: #64748b; font-family: \'JetBrains Mono\', monospace;">AUDIT TRAIL SECURE</span>'
        '</div>'
    )

    badge_styles = {
        "CRITICAL": "color: #FF647C; background: rgba(255, 100, 124, 0.12); border-color: rgba(255, 100, 124, 0.25);",
        "WARNING": "color: #FFBD59; background: rgba(255, 189, 89, 0.12); border-color: rgba(255, 189, 89, 0.25);",
        "NOMINAL": "color: #45D6A0; background: rgba(69, 214, 160, 0.12); border-color: rgba(69, 214, 160, 0.25);",
        "INFO": "color: #42D9F5; background: rgba(66, 217, 245, 0.12); border-color: rgba(66, 217, 245, 0.25);",
    }

    timeline_items = []
    for ev in events[:12]:
        ts = ev.get("timestamp", "00:00:00")
        src = ev.get("source", "SYS")
        msg = ev.get("message", "")
        sev = ev.get("severity", "NOMINAL")
        b_style = badge_styles.get(sev, badge_styles["INFO"])

        item_html = (
            f'<div style="display: flex; gap: 10px; align-items: flex-start; padding: 6px 0; border-bottom: 1px solid rgba(148, 163, 184, 0.08); font-family: \'JetBrains Mono\', monospace; font-size: 0.72rem;">'
            f'<span style="color: #64748b; white-space: nowrap;">{ts}</span>'
            f'<span style="{b_style} padding: 1px 6px; border-radius: 3px; font-weight: 700; font-size: 0.65rem; border: 1px solid; white-space: nowrap;">[{src}]</span>'
            f'<span style="color: #cbd5e1; line-height: 1.4;">{msg}</span>'
            f'</div>'
        )
        timeline_items.append(item_html)

    log_html = (
        f'<div style="background: #111B2B; border: 1px solid rgba(66, 217, 245, 0.12); border-radius: 6px; padding: 10px 14px; max-height: 220px; overflow-y: auto;">'
        f'{"".join(timeline_items)}'
        f'</div>'
    )
    render_html(log_html)
