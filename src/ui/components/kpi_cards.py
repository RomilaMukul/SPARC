"""
SPARC-PM: Telemetry KPI Cards Component
=======================================
Dense, engineering-focused telemetry metric boxes.
"""

from __future__ import annotations

import streamlit as st
from src.ui.components.html_utils import render_html
from src.ui.components.status_badge import render_status_badge


def render_kpi_card(
    label: str,
    value: str,
    subtext: str,
    status_level: str = "NOMINAL",
    badge_text: str = "",
) -> None:
    """Renders a single high-density telemetry card."""
    border_color = (
        "#10b981" if status_level.upper() in ["GREEN", "NOMINAL"]
        else "#f59e0b" if status_level.upper() in ["YELLOW", "WARNING", "ELEVATED"]
        else "#ef4444"
    )

    badge_html = render_status_badge(badge_text, status_level) if badge_text else ""

    html = (
        f'<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid {border_color}; '
        f'border-radius: 6px; padding: 12px 14px; min-height: 96px; display: flex; flex-direction: column; justify-content: space-between;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center;">'
        f'<span style="font-family: \'Space Mono\', monospace; font-size: 0.72rem; color: #94a3b8; letter-spacing: 0.5px; text-transform: uppercase;">{label}</span>'
        f'{badge_html}'
        f'</div>'
        f'<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 1.4rem; color: #f8fafc; margin: 4px 0 2px 0;">'
        f'{value}'
        f'</div>'
        f'<div style="font-family: \'Space Mono\', monospace; font-size: 0.72rem; color: #64748b;">'
        f'{subtext}'
        f'</div>'
        f'</div>'
    )

    render_html(html)
