"""
SPARC-PM: A* Decision Explanation & Mathematical Rationale Panel
================================================================
Displays the formal multi-objective A* priority scoring formula,
component mathematical breakdown, and candidate constraint rejection rationale.
Does NOT label weighted urgency scores as probabilities.
Uses render_html to prevent CommonMark indentation code-block bugs.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import streamlit as st

from src.ui.components.html_utils import render_html


def render_decision_explanation(
    selected_command: Optional[Dict[str, Any]],
    total_evaluated: int = 50,
    scheduled_count: int = 8,
    max_power_budget_w: float = 600.0,
    allocated_power_w: float = 0.0,
) -> None:
    """Renders mathematical breakdown of A* priority score f(n) = g(n) + h(n)."""
    if not selected_command:
        render_html(
            """
            <div style="background: #111B2B; border: 1px solid rgba(66, 217, 245, 0.12); border-radius: 6px; padding: 20px; text-align: center; color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
                SELECT A COMMAND TO VIEW MATHEMATICAL A* DECISION EXPLANATION
            </div>
            """
        )
        return

    sat_name = selected_command.get("satellite", "UNKNOWN")
    raw_action = selected_command.get("recommended_action", "NOMINAL")
    rank = selected_command.get("priority_rank", 1)
    orbit = selected_command.get("orbit", "LEO")

    # Metrics
    f_score = float(selected_command.get("f_score", 0.0))
    hazard_ratio = float(selected_command.get("hazard_ratio", 0.0))
    p_fail = float(selected_command.get("p_fail_72h", 0.0))
    crit = float(selected_command.get("criticality", 0.5))
    time_to_corridor_s = float(selected_command.get("time_to_corridor_s", 3600.0))

    # Recompute or read g_cost and h_heuristic
    g_cost = float(selected_command.get("g_cost", round(0.40 * hazard_ratio + 0.40 * p_fail + 0.20 * crit, 4)))
    h_heuristic = float(selected_command.get("h_heuristic", round(f_score - g_cost, 4)))

    deferred_count = max(0, total_evaluated - scheduled_count)
    rationale_text = _get_action_rationale(raw_action, hazard_ratio, p_fail, orbit)

    # Component weights and values
    h_contrib = round(0.40 * hazard_ratio, 4)
    p_contrib = round(0.40 * p_fail, 4)
    c_contrib = round(0.20 * crit, 4)

    panel_html = (
        f'<div style="background: #111B2B; border: 1px solid rgba(66, 217, 245, 0.18); border-radius: 6px; padding: 14px 16px; margin-bottom: 12px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(66, 217, 245, 0.12); padding-bottom: 8px; margin-bottom: 12px;">'
        f'<div style="font-family: \'Inter\', sans-serif; font-weight: 700; font-size: 0.92rem; color: #f8fafc; display: flex; align-items: center; gap: 8px;">'
        f'<span style="color: #42D9F5;">📐</span> A* HEURISTIC DECISION EXPLANATION'
        f'</div>'
        f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 0.72rem; color: #cbd5e1;">'
        f'ASSET <span style="color: #42D9F5; font-weight: 700;">{sat_name}</span> • RANK <span style="color: #42D9F5; font-weight: 700;">#{rank}</span> OF {scheduled_count}'
        f'</div>'
        f'</div>'
        f'<div style="background: #080D17; border: 1px solid rgba(66, 217, 245, 0.15); border-radius: 4px; padding: 10px 14px; margin-bottom: 12px; font-family: \'JetBrains Mono\', monospace; font-size: 0.76rem;">'
        f'<div style="color: #42D9F5; font-weight: 700; margin-bottom: 4px; display: flex; justify-content: space-between;">'
        f'<span>EVALUATION FUNCTION: f(n) = g(n) + h(n)</span>'
        f'<span style="color: #42D9F5; font-size: 0.85rem;">= {f_score:.4f}</span>'
        f'</div>'
        f'<div style="color: #94a3b8; font-size: 0.72rem; line-height: 1.6;">'
        f'• <b>Edge Cost g(n):</b> (0.40 × H<sub>j</sub>) + (0.40 × P<sub>fail</sub>) + (0.20 × w<sub>crit</sub>) = <b>{g_cost:.4f}</b><br/>'
        f'• <b>Admissible Heuristic h(n):</b> max(0, 1 - t<sub>entry</sub> / 3600s) × 0.35 = <b>{h_heuristic:.4f}</b>'
        f'</div>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 14px; font-family: \'JetBrains Mono\', monospace; font-size: 0.72rem;">'
        f'<div style="background: rgba(15, 23, 42, 0.6); padding: 8px; border-radius: 4px; border: 1px solid rgba(148, 163, 184, 0.1);">'
        f'<span style="color: #64748b; font-size: 0.66rem;">HAZARD RATIO H_j</span><br/>'
        f'<span style="color: {"#FF647C" if hazard_ratio>0.6 else "#FFBD59"}; font-weight: 700; font-size: 0.85rem;">{hazard_ratio:.4f}</span><br/>'
        f'<span style="color: #64748b; font-size: 0.66rem;">Contrib: {h_contrib:.3f} (40%)</span>'
        f'</div>'
        f'<div style="background: rgba(15, 23, 42, 0.6); padding: 8px; border-radius: 4px; border: 1px solid rgba(148, 163, 184, 0.1);">'
        f'<span style="color: #64748b; font-size: 0.66rem;">72H P_FAIL</span><br/>'
        f'<span style="color: {"#FF647C" if p_fail>0.5 else "#45D6A0"}; font-weight: 700; font-size: 0.85rem;">{p_fail:.4f}</span><br/>'
        f'<span style="color: #64748b; font-size: 0.66rem;">Contrib: {p_contrib:.3f} (40%)</span>'
        f'</div>'
        f'<div style="background: rgba(15, 23, 42, 0.6); padding: 8px; border-radius: 4px; border: 1px solid rgba(148, 163, 184, 0.1);">'
        f'<span style="color: #64748b; font-size: 0.66rem;">CRITICALITY w_crit</span><br/>'
        f'<span style="color: #42D9F5; font-weight: 700; font-size: 0.85rem;">{crit:.2f}</span><br/>'
        f'<span style="color: #64748b; font-size: 0.66rem;">Contrib: {c_contrib:.3f} (20%)</span>'
        f'</div>'
        f'<div style="background: rgba(15, 23, 42, 0.6); padding: 8px; border-radius: 4px; border: 1px solid rgba(148, 163, 184, 0.1);">'
        f'<span style="color: #64748b; font-size: 0.66rem;">TIME TO CORRIDOR</span><br/>'
        f'<span style="color: #f8fafc; font-weight: 700; font-size: 0.85rem;">{time_to_corridor_s/60.0:.1f}m</span><br/>'
        f'<span style="color: #64748b; font-size: 0.66rem;">{time_to_corridor_s:.0f} sec</span>'
        f'</div>'
        f'</div>'
        f'<div style="font-family: \'Inter\', sans-serif; font-size: 0.78rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 12px; background: rgba(8, 13, 23, 0.5); padding: 10px 12px; border-radius: 4px; border: 1px solid rgba(66, 217, 245, 0.1);">'
        f'<div style="font-weight: 700; color: #f8fafc; margin-bottom: 4px; font-family: \'JetBrains Mono\', monospace; font-size: 0.74rem;">WHY WAS <code style="color: #42D9F5;">{raw_action}</code> SELECTED?</div>'
        f'{rationale_text}'
        f'</div>'
        f'<div style="border-top: 1px solid rgba(148, 163, 184, 0.12); padding-top: 8px; font-family: \'JetBrains Mono\', monospace; font-size: 0.7rem; color: #94a3b8; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;">'
        f'<span>EVALUATED: <b>{total_evaluated}</b></span>'
        f'<span>SCHEDULED: <b style="color: #45D6A0;">{scheduled_count}</b></span>'
        f'<span>DEFERRED: <b>{deferred_count}</b></span>'
        f'<span>POWER: <b>{allocated_power_w:.1f} / {max_power_budget_w:.0f} W</b></span>'
        f'</div>'
        f'</div>'
    )
    render_html(panel_html)


def _get_action_rationale(action: str, hazard: float, p_fail: float, orbit: str) -> str:
    """Generates the exact engineering rationale for the chosen action."""
    is_crew = "CREW" in orbit.upper() or "GAGANYAAN" in orbit.upper()

    if action == "ATTITUDE_SHIELD_TILT":
        if is_crew:
            return "Asset is a crewed module (Gaganyaan). Under elevated radiation flux, tilting the spacecraft's high-density forward shielding towards the Sun takes precedence over safe-mode shutdown to minimize crew acute absorbed dose."
        return f"Hazard ratio H<sub>j</sub> = {hazard:.2f} indicates imminent crossing of CME core envelope. Rotating spacecraft bus presents the maximum structural cross-section shielding toward the incoming proton flux vector."
    elif action == "ENTER_SAFE_MODE":
        return f"Severe risk condition triggered (H<sub>j</sub> = {hazard:.2f} ≥ 0.65 or P<sub>fail</sub> = {p_fail:.2f} ≥ 0.70). Unpowered payload bus protects CMOS optical detectors and solar array slip rings from irreversible single-event latchups."
    elif action == "POWER_DOWN_PAYLOAD":
        return f"Moderate risk threshold reached (H<sub>j</sub> = {hazard:.2f} ≥ 0.20 or P<sub>fail</sub> = {p_fail:.2f} ≥ 0.25). Scientific and Earth observation payloads are de-energized to standby mode while keeping satellite attitude control and housekeeping active."
    elif action == "ORBITAL_MANEUVER":
        return "Severe atmospheric drag spike anticipated in LEO. Reaction control thruster impulse compensates for orbital decay to preserve ground pass visibility."
    elif action == "ENHANCED_TELEMETRY_POLL":
        return f"Early anomaly precursor observed (H<sub>j</sub> = {hazard:.2f} ≥ 0.10 or P<sub>fail</sub> = {p_fail:.2f} ≥ 0.10). Telecommand elevates housekeeping sampling from 0.1 Hz to 1.0 Hz for close diagnostic observation."
    else:
        return "Asset remains within safe nominal flight margins. Scheduled action preserves nominal flight routine."
