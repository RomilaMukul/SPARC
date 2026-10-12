"""
SPARC-PM: High-Density Aerospace Command Queue Component
=========================================================
Presents the prioritized A* telecommand queue with synchronized selection,
NORAD IDs, execution metrics, lifecycle states, and power allocations.
Uses render_html to eliminate CommonMark indentation bugs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from src.ui.components.html_utils import render_html


def render_command_queue(
    scheduled_commands: Dict[str, Any],
    selected_sat_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Renders high-density mission-control command queue with synchronized selection.
    Returns the currently selected command dictionary.
    """
    queue: List[Dict[str, Any]] = scheduled_commands.get("command_queue", [])

    if not queue:
        render_html(
            """
            <div style="background: #111B2B; border: 1px solid rgba(69, 214, 160, 0.25); border-radius: 6px; padding: 24px; text-align: center; color: #45D6A0; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
                ✓ ALL FLEET ASSETS IN NOMINAL FLIGHT MARGINS • ZERO PROTECTIVE TELECOMMANDS QUEUED
            </div>
            """
        )
        return None

    # Filter Controls
    filter_opt = st.segmented_control(
        "Filter Queue",
        options=["ALL", "CRITICAL", "WARNING", "ELEVATED"],
        default="ALL",
        label_visibility="collapsed",
        key="cmd_queue_filter",
    )

    filtered_queue = queue
    if filter_opt and filter_opt != "ALL":
        filtered = [c for c in queue if c.get("urgency_tier") == filter_opt]
        if filtered:
            filtered_queue = filtered

    # Target selection keys
    target_names = [
        f"#{c.get('priority_rank', i+1)} | {c.get('satellite', 'SAT')} — {c.get('recommended_action', 'NOMINAL')}"
        for i, c in enumerate(filtered_queue)
    ]

    # Safely clamp default index based on selected_sat_id
    default_idx = 0
    if selected_sat_id:
        for idx, c in enumerate(filtered_queue):
            if c.get("sat_id") == selected_sat_id or c.get("satellite") == selected_sat_id:
                default_idx = idx
                break

    selected_choice = st.selectbox(
        "Select Active Telecommand to Inspect & Authorize",
        options=range(len(filtered_queue)),
        format_func=lambda i: target_names[i],
        index=min(default_idx, len(filtered_queue) - 1),
        key="queue_active_select_idx",
        help="Selects target satellite across the 3D map, cryptographic inspector, and human review interlock.",
    )

    selected_cmd = filtered_queue[selected_choice] if filtered_queue else None

    # Build entire table HTML in one single block to avoid split DOM container bugs
    rows_html = []
    for idx, cmd in enumerate(filtered_queue):
        is_active = (selected_cmd is not None and cmd.get("sat_id") == selected_cmd.get("sat_id"))
        row_bg = "background: rgba(66, 217, 245, 0.08); border-left: 3px solid #42D9F5;" if is_active else ("background: #0D1624;" if idx % 2 == 1 else "background: #080D17;")
        
        rank = cmd.get("priority_rank", idx + 1)
        sat = cmd.get("satellite", "SAT")
        sat_id = cmd.get("sat_id", "SAT")
        orbit = cmd.get("orbit", "LEO")
        act = cmd.get("recommended_action", "NOMINAL")
        code = cmd.get("telecommand_frame", {}).get("cmd_code", "CMD_0x00")
        f_score = cmd.get("f_score", 0.0)
        h_ratio = cmd.get("hazard_ratio", 0.0)
        p_fail = cmd.get("p_fail_72h", 0.0)
        power = cmd.get("power_draw_w", 0.0)
        urgency = cmd.get("urgency_tier", "NOMINAL")

        urg_color = "#FF647C" if urgency == "CRITICAL" else ("#FFBD59" if urgency == "WARNING" else ("#42D9F5" if urgency == "ELEVATED" else "#45D6A0"))

        # Priority Rank Badge Styling
        if rank == 1:
            rank_badge = '<span style="background: rgba(255, 215, 0, 0.18); color: #FFD700; border: 1px solid rgba(255, 215, 0, 0.45); padding: 1px 6px; border-radius: 3px; font-weight: 800;">#1 PRI</span>'
        elif rank == 2:
            rank_badge = '<span style="background: rgba(226, 232, 240, 0.15); color: #E2E8F0; border: 1px solid rgba(226, 232, 240, 0.3); padding: 1px 6px; border-radius: 3px; font-weight: 700;">#2</span>'
        elif rank == 3:
            rank_badge = '<span style="background: rgba(205, 127, 50, 0.15); color: #CD7F32; border: 1px solid rgba(205, 127, 50, 0.3); padding: 1px 6px; border-radius: 3px; font-weight: 700;">#3</span>'
        else:
            rank_badge = f'<span style="color: #94a3b8; font-weight: 600;">#{rank}</span>'

        urg_badge = f'<span style="color: {urg_color}; background: {urg_color}18; border: 1px solid {urg_color}35; padding: 2px 6px; border-radius: 3px; font-weight: 700; font-size: 0.65rem;">● {urgency}</span>'

        row_html = (
            f'<tr style="{row_bg} border-bottom: 1px solid rgba(148, 163, 184, 0.08);">'
            f'<td style="padding: 7px 10px; font-weight: 700;">{rank_badge}</td>'
            f'<td style="padding: 7px 10px; font-weight: 600; color: {"#42D9F5" if is_active else "#f8fafc"};">{sat} <span style="color: #64748b; font-size: 0.65rem;">({sat_id})</span></td>'
            f'<td style="padding: 7px 10px; color: #94a3b8;">{orbit}</td>'
            f'<td style="padding: 7px 10px;"><code style="color: {urg_color}; background: rgba(15, 23, 42, 0.6); padding: 2px 5px; border-radius: 3px; font-weight: 700;">{code}</code> <span style="font-weight: 400; color: #cbd5e1; font-size: 0.68rem;">({act})</span></td>'
            f'<td style="padding: 7px 10px; color: #42D9F5; font-weight: 700;">{f_score:.4f}</td>'
            f'<td style="padding: 7px 10px; color: {"#FF647C" if h_ratio > 0.6 else "#FFBD59"};">{h_ratio*100:.1f}%</td>'
            f'<td style="padding: 7px 10px; color: {"#FF647C" if p_fail > 0.4 else "#45D6A0"};">{p_fail*100:.1f}%</td>'
            f'<td style="padding: 7px 10px; color: #f8fafc; font-weight: 600;">{power:.0f} W</td>'
            f'<td style="padding: 7px 10px;">{urg_badge}</td>'
            f'</tr>'
        )
        rows_html.append(row_html)

    full_table_html = (
        f'<div style="background: #080D17; border: 1px solid rgba(66, 217, 245, 0.18); border-radius: 6px; overflow: hidden; margin-top: 10px;">'
        f'<table style="width: 100%; border-collapse: collapse; font-family: \'JetBrains Mono\', monospace; font-size: 0.72rem; color: #cbd5e1;">'
        f'<thead>'
        f'<tr style="background: #111B2B; border-bottom: 1px solid rgba(66, 217, 245, 0.2); text-align: left; color: #64748b; font-size: 0.68rem; letter-spacing: 0.5px;">'
        f'<th style="padding: 8px 10px;">PRIORITY</th>'
        f'<th style="padding: 8px 10px;">ASSET (NORAD)</th>'
        f'<th style="padding: 8px 10px;">ORBIT</th>'
        f'<th style="padding: 8px 10px;">ACTION CODE</th>'
        f'<th style="padding: 8px 10px;">A* SCORE f(n)</th>'
        f'<th style="padding: 8px 10px;">HAZARD H_j</th>'
        f'<th style="padding: 8px 10px;">72h P_FAIL</th>'
        f'<th style="padding: 8px 10px;">POWER</th>'
        f'<th style="padding: 8px 10px;">STATUS TIER</th>'
        f'</tr>'
        f'</thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        f'</table>'
        f'</div>'
    )

    render_html(full_table_html)
    return selected_cmd
