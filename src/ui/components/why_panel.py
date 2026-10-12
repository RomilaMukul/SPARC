"""
SPARC-PM: Reusable 'WHY?' Explanation Panel
============================================
Displays clear evidence breakdown for spacecraft or crew risk states.
Distinguishes between:
1. MODEL OUTPUT
2. PHYSICS / TELEMETRY EVIDENCE
3. OPERATIONAL RESPONSE
"""

from __future__ import annotations

import streamlit as st
from src.ui.components.html_utils import render_html
from src.ui.components.status_badge import render_status_badge


def render_why_panel(
    entity_name: str,
    risk_level: str,
    model_outputs: dict,
    physics_evidence: dict,
    operational_response: dict,
) -> None:
    """Renders a structured, engineering-grade 'WHY?' rationale card."""
    badge_html = render_status_badge(risk_level, risk_level)

    # 1. Model output items
    model_items_html = "".join([
        f"""<div style="display: flex; justify-content: space-between; font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #cbd5e1; margin-bottom: 5px;">
            <span style="color: #94a3b8;">{k}:</span>
            <span style="font-weight: 600;">{v}</span>
        </div>"""
        for k, v in model_outputs.items()
    ])

    # 2. Physics evidence items
    physics_items_html = "".join([
        f"""<div style="display: flex; justify-content: space-between; font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #cbd5e1; margin-bottom: 5px;">
            <span style="color: #94a3b8;">{k}:</span>
            <span style="font-weight: 600;">{v}</span>
        </div>"""
        for k, v in physics_evidence.items()
    ])

    # 3. Operational response items
    response_items_html = "".join([
        f"""<div style="display: flex; justify-content: space-between; font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #cbd5e1; margin-bottom: 5px;">
            <span style="color: #94a3b8;">{k}:</span>
            <span style="font-weight: 600;">{v}</span>
        </div>"""
        for k, v in operational_response.items()
    ])

    html = f"""
    <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 14px 16px; margin-top: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 12px;">
            <span style="font-family: 'Inter', sans-serif; font-weight: 700; font-size: 0.9rem; color: #f8fafc; text-transform: uppercase; letter-spacing: 0.5px;">
                ❓ WHY IS {entity_name} AT RISK?
            </span>
            {badge_html}
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
            <div style="background: #1e293b; border-radius: 4px; padding: 10px 12px;">
                <div style="font-family: 'Space Mono', monospace; font-size: 0.72rem; color: #60a5fa; font-weight: 700; margin-bottom: 8px; text-transform: uppercase;">
                    1. MODEL OUTPUT
                </div>
                {model_items_html}
            </div>
            
            <div style="background: #1e293b; border-radius: 4px; padding: 10px 12px;">
                <div style="font-family: 'Space Mono', monospace; font-size: 0.72rem; color: #fbbf24; font-weight: 700; margin-bottom: 8px; text-transform: uppercase;">
                    2. PHYSICS / TELEMETRY EVIDENCE
                </div>
                {physics_items_html}
            </div>
            
            <div style="background: #1e293b; border-radius: 4px; padding: 10px 12px;">
                <div style="font-family: 'Space Mono', monospace; font-size: 0.72rem; color: #34d399; font-weight: 700; margin-bottom: 8px; text-transform: uppercase;">
                    3. RECOMMENDED RESPONSE
                </div>
                {response_items_html}
            </div>
        </div>
    </div>
    """

    render_html(html)
