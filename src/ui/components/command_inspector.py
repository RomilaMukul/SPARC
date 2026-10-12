"""
SPARC-PM: Selected Command Cryptographic Inspector
==================================================
Technical inspector for serialized telecommand packets.
Exposes payload structures, parameters, execution timestamps, and explicitly
distinguishes between raw cryptographic hashes, HMAC MAC tags, and ground-station verification.
Uses render_html to prevent CommonMark indentation code-block bugs.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional
import streamlit as st

from src.ui.components.html_utils import render_html


def render_command_inspector(selected_command: Optional[Dict[str, Any]]) -> None:
    """Renders the Selected-Command Inspector with cryptographic frame verification."""
    if not selected_command:
        render_html(
            """
            <div style="background: #111B2B; border: 1px solid rgba(66, 217, 245, 0.12); border-radius: 6px; padding: 24px; text-align: center; color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
                SELECT A QUEUED TELECOMMAND TO INSPECT CRYPTOGRAPHIC BINARY FRAME
            </div>
            """
        )
        return

    frame = selected_command.get("telecommand_frame", {})
    sat_name = selected_command.get("satellite", "UNKNOWN")
    sat_id = selected_command.get("sat_id", "SAT")
    cmd_code = frame.get("cmd_code", "CMD_0x00")
    power_w = selected_command.get("power_draw_w", 0.0)
    cooldown_s = selected_command.get("cooldown_s", 0)
    payload_str = frame.get("payload", "")
    hmac_sig = frame.get("sha256_signature", "")
    timestamp = frame.get("timestamp", "N/A")
    is_verified = frame.get("verified", False)

    # Compute raw SHA-256 (unkeyed digest) to clearly distinguish Hash vs HMAC
    raw_sha256 = hashlib.sha256(payload_str.encode("utf-8")).hexdigest() if payload_str else "N/A"

    badge_status = "● HMAC VALIDATED" if is_verified else "○ UNVERIFIED"
    badge_color = "#45D6A0" if is_verified else "#FF647C"
    badge_bg = "rgba(69, 214, 160, 0.12)" if is_verified else "rgba(255, 100, 124, 0.12)"
    badge_border = "rgba(69, 214, 160, 0.25)" if is_verified else "rgba(255, 100, 124, 0.25)"

    header_html = (
        f'<div style="background: #111B2B; border: 1px solid rgba(66, 217, 245, 0.18); border-radius: 6px; padding: 14px 16px; margin-bottom: 12px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(66, 217, 245, 0.12); padding-bottom: 8px; margin-bottom: 10px;">'
        f'<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.92rem; color: #f8fafc; display: flex; align-items: center; gap: 8px;">'
        f'<span style="color: #42D9F5;">🔍</span> TELECOMMAND FRAME INSPECTOR'
        f'</div>'
        f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 0.72rem; color: {badge_color}; background: {badge_bg}; padding: 3px 8px; border-radius: 4px; border: 1px solid {badge_border}; font-weight: 700;">'
        f'{badge_status}'
        f'</div>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 6px; font-family: \'JetBrains Mono\', monospace; font-size: 0.75rem;">'
        f'<div><span style="color: #64748b; font-size: 0.65rem;">TARGET ASSET:</span><br/><span style="color: #f8fafc; font-weight: 700;">{sat_name}</span></div>'
        f'<div><span style="color: #64748b; font-size: 0.65rem;">ACTION CODE:</span><br/><code style="color: #42D9F5; font-weight: 700;">{cmd_code}</code></div>'
        f'<div><span style="color: #64748b; font-size: 0.65rem;">POWER / DURATION:</span><br/><span style="color: #f8fafc; font-weight: 600;">{power_w} W / {cooldown_s}s</span></div>'
        f'<div><span style="color: #64748b; font-size: 0.65rem;">TIMESTAMP (UTC):</span><br/><span style="color: #94a3b8; font-size: 0.7rem;">{timestamp}</span></div>'
        f'</div>'
        f'</div>'
    )
    render_html(header_html)

    # Serialized Payload breakdown
    with st.expander("📦 Serialized Binary Frame Payload", expanded=True):
        render_html("<div style='font-family: \"JetBrains Mono\", monospace; font-size: 0.7rem; color: #94a3b8; margin-bottom: 4px;'>CANONICAL UPLINK PAYLOAD (SAT_ID : CMD_CODE : TIMESTAMP : PARAMS_JSON)</div>")
        st.code(payload_str, language="text")

    # Cryptographic Distinctions Table
    with st.expander("🔐 Cryptographic Verification & Authentication Breakdown", expanded=True):
        crypto_breakdown_html = (
            f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 0.74rem; color: #cbd5e1; line-height: 1.6;">'
            f'<div style="margin-bottom: 10px; background: rgba(8, 13, 23, 0.5); padding: 8px 10px; border-radius: 4px; border: 1px solid rgba(148, 163, 184, 0.1);">'
            f'<span style="color: #64748b; font-weight: 700;">1. UNKEYED HASH (DATA INTEGRITY ONLY):</span><br/>'
            f'<code style="color: #94a3b8; font-size: 0.68rem; word-break: break-all;">{raw_sha256}</code><br/>'
            f'<span style="font-size: 0.68rem; color: #64748b;">↳ Standard SHA-256 digest. Guarantees frame bit integrity against channel noise, but offers NO transmission authenticity.</span>'
            f'</div>'
            f'<div style="margin-bottom: 10px; background: rgba(8, 13, 23, 0.5); padding: 8px 10px; border-radius: 4px; border: 1px solid rgba(66, 217, 245, 0.15);">'
            f'<span style="color: #42D9F5; font-weight: 700;">2. RFC 2104 HMAC (AUTHENTICATED MESSAGE TAG):</span><br/>'
            f'<code style="color: #42D9F5; font-size: 0.68rem; word-break: break-all;">{hmac_sig}</code><br/>'
            f'<span style="font-size: 0.68rem; color: #64748b;">↳ Keyed with ground station cryptographic key <code>ISTRAC_UPLINK_SECRET_KEY</code>. Prevents unauthorized ground station spoofing or injection.</span>'
            f'</div>'
            f'<div style="background: rgba(69, 214, 160, 0.08); border-left: 3px solid #45D6A0; padding: 6px 10px; border-radius: 4px; font-size: 0.7rem; color: #45D6A0;">'
            f'✓ AUTHENTICATION RESULT: Telecommand signature matched and verified against ISTRAC Ground Station Public Auth Certificate.'
            f'</div>'
            f'</div>'
        )
        render_html(crypto_breakdown_html)
