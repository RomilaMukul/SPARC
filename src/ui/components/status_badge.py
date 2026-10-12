"""
SPARC-PM: Engineering Status Badge Component
============================================
Clean, non-glowing engineering badges for mission operations.
"""

import streamlit as st

BADGE_STYLES = {
    "NOMINAL": "background: #064e3b; color: #34d399; border: 1px solid #10b981;",
    "GREEN": "background: #064e3b; color: #34d399; border: 1px solid #10b981;",
    "ELEVATED": "background: #1e3a5f; color: #60a5fa; border: 1px solid #3b82f6;",
    "INFO": "background: #1e3a5f; color: #60a5fa; border: 1px solid #3b82f6;",
    "WARNING": "background: #451a03; color: #fbbf24; border: 1px solid #f59e0b;",
    "YELLOW": "background: #451a03; color: #fbbf24; border: 1px solid #f59e0b;",
    "CRITICAL": "background: #450a0a; color: #fca5a5; border: 1px solid #ef4444;",
    "RED": "background: #450a0a; color: #fca5a5; border: 1px solid #ef4444;",
}


def render_status_badge(text: str, level: str = "NOMINAL") -> str:
    """Returns HTML string for an engineering status badge."""
    style = BADGE_STYLES.get(level.upper(), BADGE_STYLES["NOMINAL"])
    return f"""<span style="{style} font-family: 'Space Mono', monospace; font-size: 0.75rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.5px; text-transform: uppercase;">{text}</span>"""


def render_led(level: str = "NOMINAL") -> str:
    """Returns HTML string for a non-glowing LED indicator."""
    color = "#10b981" if level.upper() in ["GREEN", "NOMINAL"] else "#f59e0b" if level.upper() in ["YELLOW", "WARNING", "ELEVATED"] else "#ef4444"
    return f"""<span style="display:inline-block; width:8px; height:8px; border-radius:50%; background-color:{color}; margin-right:6px; vertical-align:middle;"></span>"""
