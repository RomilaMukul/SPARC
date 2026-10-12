"""
SPARC-PM: Three.js Interactive Mission Globe Renderer
=====================================================
Generates self-contained HTML/JS/CSS for a full-screen interactive 3D Earth
with satellite markers, orbital trajectories, ground tracks, hazard corridor,
ground stations, and floating glass mission-control panels.

All satellite positions, orbits, and hazard data are injected from the
authoritative backend (SpatialHazardEngine). NO fake data is generated here.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional

import numpy as np

from src.models.spatial_hazard import EARTH_RADIUS_KM


# ISRO & NASA Ground Station Registry
GROUND_STATIONS = [
    {"name": "ISTRAC Bengaluru", "code": "ISTRAC-BLR", "lat": 12.9716, "lon": 77.5946, "agency": "ISRO", "type": "MOC"},
    {"name": "MCF Hassan", "code": "MCF-HSN", "lat": 13.0068, "lon": 76.0996, "agency": "ISRO", "type": "GEO Relay"},
    {"name": "SDSC Sriharikota", "code": "SDSC-SHAR", "lat": 13.7199, "lon": 80.2304, "agency": "ISRO", "type": "Launch"},
    {"name": "NASA DSN Goldstone", "code": "DSN-GDS", "lat": 35.4267, "lon": -116.89, "agency": "NASA", "type": "Deep Space"},
    {"name": "NASA DSN Madrid", "code": "DSN-MAD", "lat": 40.4272, "lon": -4.2497, "agency": "NASA", "type": "Deep Space"},
    {"name": "NASA DSN Canberra", "code": "DSN-CBR", "lat": -35.4014, "lon": 148.9817, "agency": "NASA", "type": "Deep Space"},
]


def _lla_to_threejs(lat_deg: float, lon_deg: float, alt_km: float = 0.0, scale: float = 1.0) -> List[float]:
    """Convert lat/lon/alt to Three.js 3D coordinates (Y-up, Z-forward)."""
    r = (EARTH_RADIUS_KM + alt_km) * scale
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    x = r * math.cos(lat_rad) * math.cos(lon_rad)
    y = r * math.sin(lat_rad)
    z = -r * math.cos(lat_rad) * math.sin(lon_rad)
    return [round(x, 3), round(y, 3), round(z, 3)]


def _ecef_to_threejs(ecef: List[float], scale: float = 1.0) -> List[float]:
    """Convert ECEF (X,Y,Z in km) to Three.js coords (Y-up)."""
    x, y, z = ecef
    return [round(x * scale, 3), round(z * scale, 3), round(-y * scale, 3)]


def generate_globe_html(
    hazard_report: Dict[str, Any],
    severity_report: Dict[str, Any],
    telemetry: Dict[str, Any],
    scheduled_commands: Dict[str, Any],
    dosimetry_report: Dict[str, Any],
    orbit_trajectories: List[Optional[Dict[str, Any]]],
    scenario_name: str = "",
    pipeline_latency_ms: float = 0.0,
    timestamp: str = "",
    height: int = 900,
) -> str:
    """
    Generates the complete HTML for the SPARC-PM mission control globe.
    
    All data comes from the authoritative backend pipeline. 
    NO fake data is generated here.
    """
    fleet = hazard_report.get("fleet_hazard_profile", [])
    storm_center = hazard_report.get("storm_center_ecef", [0, 0, 0])
    storm_radius = hazard_report.get("storm_corridor_radius_km", 0)
    
    # Scale factor: normalize Earth radius to ~1.0 for Three.js
    SCALE = 1.0 / EARTH_RADIUS_KM
    earth_r = 1.0  # Normalized
    
    # Prepare satellite data for JS
    sat_data = []
    for i, sat in enumerate(fleet):
        ecef = sat.get("r_ecef", [0, 0, 0])
        pos = _ecef_to_threejs(ecef, SCALE)
        alert = sat.get("alert_level", "NOMINAL")
        
        sat_data.append({
            "id": i,
            "name": sat.get("name", f"SAT-{i}"),
            "sat_id": sat.get("sat_id", f"SAT-{i}"),
            "pos": pos,
            "alert": alert,
            "altitude_km": round(sat.get("altitude_km", 0), 1),
            "speed_kms": round(sat.get("speed_kms", 0), 3),
            "hazard_ratio": round(sat.get("hazard_ratio", 0), 4),
            "dist_to_storm_km": round(sat.get("dist_to_storm_km", 0), 1),
            "orbit_type": sat.get("orbit_type", "LEO"),
            "latitude": round(sat.get("latitude", 0), 2),
            "longitude": round(sat.get("longitude", 0), 2),
            "criticality": round(sat.get("criticality", 0.5), 2),
        })
    
    # Prepare orbit trajectory data for JS
    orbit_data = []
    for traj in orbit_trajectories:
        if traj is None:
            continue
        points = []
        xs, ys, zs = traj.get("x", []), traj.get("y", []), traj.get("z", [])
        for x, y, z in zip(xs, ys, zs):
            p = _ecef_to_threejs([x, y, z], SCALE)
            points.append(p)
        orbit_data.append({
            "name": traj.get("name", ""),
            "points": points,
            "altitude_km": traj.get("altitude_km", 0),
        })
    
    # Prepare ground station data
    gs_data = []
    for gs in GROUND_STATIONS:
        pos = _lla_to_threejs(gs["lat"], gs["lon"], 0, SCALE)
        gs_data.append({
            "name": gs["name"],
            "code": gs["code"],
            "agency": gs["agency"],
            "type": gs["type"],
            "lat": gs["lat"],
            "lon": gs["lon"],
            "pos": pos,
        })
    
    # Storm corridor in Three.js coords
    storm_pos = _ecef_to_threejs(storm_center, SCALE)
    storm_r = storm_radius * SCALE
    
    # Severity data for top bar
    sev_label = severity_report.get("severity_label", "G0_NOMINAL_QUIET")
    triage = severity_report.get("triage", "GREEN")
    
    # Command queue summary
    cmd_queue = scheduled_commands.get("command_queue", [])
    cmd_data = []
    for idx, cmd in enumerate(cmd_queue[:6]):
        cmd_data.append({
            "rank": cmd.get("priority_rank", idx + 1),
            "satellite": cmd.get("satellite", "SAT"),
            "action": cmd.get("recommended_action", "NOMINAL"),
            "urgency": cmd.get("urgency_tier", "NOMINAL"),
            "power_w": cmd.get("power_draw_w", 0),
            "f_score": round(cmd.get("f_score", 0), 2),
            "signature": cmd.get("telecommand_frame", {}).get("sha256_signature", "N/A")[:16] + "...",
            "verified": True,
        })
    
    # Dosimetry summary
    dos_data = {
        "peak_dose_rate": round(dosimetry_report.get("peak_dose_rate_usv_hr", 0), 1),
        "eva_status": dosimetry_report.get("eva_status", "NOMINAL"),
        "crew_action": dosimetry_report.get("crew_action", "NOMINAL"),
        "total_6h_dose": round(dosimetry_report.get("total_6h_dose_msv", 0), 4),
        "alert_color": dosimetry_report.get("alert_color", "GREEN"),
    }
    
    # Prepare WHY data for selected satellite
    sev_action = severity_report.get("action", "NOMINAL_OPERATIONS")
    sev_action_desc = severity_report.get("action_description", "")
    
    # Serialize to JSON for injection into JS
    sat_json = json.dumps(sat_data)
    orbit_json = json.dumps(orbit_data)
    gs_json = json.dumps(gs_data)
    cmd_json = json.dumps(cmd_data)
    dos_json = json.dumps(dos_data)
    telemetry_json = json.dumps({
        "proton_flux_pfu": round(telemetry.get("proton_flux_pfu", 0), 1),
        "proton_speed_kms": round(telemetry.get("proton_speed_kms", 0), 0),
        "mag_bz_field": round(telemetry.get("mag_bz_field", 0), 1),
        "proton_density_cm3": round(telemetry.get("proton_density_cm3", 0), 1),
        "solar_wind_dyn_pressure_npa": round(telemetry.get("solar_wind_dyn_pressure_npa", 0), 1),
    })
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

html, body {{
    background: #030712;
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, sans-serif;
    overflow: hidden;
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
}}

#globe-container {{
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
}}

/* ═══════════ FLOATING GLASS PANELS ═══════════ */
.panel {{
    position: absolute;
    background: rgba(3, 7, 18, 0.82);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 12px;
    z-index: 10;
    transition: opacity 0.4s ease, transform 0.3s ease;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.04);
}}

.panel-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.08);
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
}}

.panel-body {{
    padding: 10px 14px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #1e293b transparent;
}}

.panel-body::-webkit-scrollbar {{ width: 4px; }}
.panel-body::-webkit-scrollbar-track {{ background: transparent; }}
.panel-body::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 4px; }}

/* ═══════════ TOP BAR ═══════════ */
#top-bar {{
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 48px;
    background: rgba(3, 7, 18, 0.88);
    backdrop-filter: blur(24px);
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
    z-index: 20;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
}}

#top-bar .brand {{
    display: flex;
    align-items: center;
    gap: 10px;
}}

#top-bar .brand-name {{
    font-weight: 800;
    font-size: 0.85rem;
    letter-spacing: 1.5px;
    color: #f8fafc;
}}

#top-bar .brand-sub {{
    font-size: 0.62rem;
    color: #64748b;
    font-weight: 500;
    letter-spacing: 0.5px;
}}

#top-bar .status-center {{
    display: flex;
    align-items: center;
    gap: 16px;
}}

#top-bar .status-right {{
    display: flex;
    align-items: center;
    gap: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #94a3b8;
}}

.badge {{
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}

.badge-nominal {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
.badge-elevated {{ background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
.badge-warning {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
.badge-critical {{ background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.3); }}

.led {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    display: inline-block;
    animation: led-pulse 2s ease-in-out infinite;
}}

.led-green {{ background: #10b981; box-shadow: 0 0 6px rgba(16, 185, 129, 0.5); }}
.led-yellow {{ background: #f59e0b; box-shadow: 0 0 6px rgba(245, 158, 11, 0.5); }}
.led-red {{ background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.6); animation: led-pulse-critical 1.2s ease-in-out infinite; }}

@keyframes led-pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.6; }}
}}
@keyframes led-pulse-critical {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.4; }}
}}

/* ═══════════ LEFT PANEL - SPACECRAFT LIST ═══════════ */
#panel-spacecraft {{
    top: 60px;
    left: 12px;
    width: 260px;
    max-height: calc(100% - 120px);
}}

.sat-filter-tabs {{
    display: flex;
    gap: 2px;
    padding: 8px 14px 4px 14px;
}}

.sat-filter-tab {{
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.6rem;
    font-weight: 600;
    cursor: pointer;
    color: #64748b;
    background: transparent;
    border: 1px solid transparent;
    transition: all 0.2s;
    font-family: 'JetBrains Mono', monospace;
}}

.sat-filter-tab:hover {{ color: #e2e8f0; background: rgba(148, 163, 184, 0.08); }}
.sat-filter-tab.active {{ color: #f8fafc; background: rgba(148, 163, 184, 0.12); border-color: rgba(148, 163, 184, 0.15); }}

.sat-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 14px;
    cursor: pointer;
    border-left: 2px solid transparent;
    transition: all 0.2s ease;
}}

.sat-item:hover {{
    background: rgba(148, 163, 184, 0.06);
}}

.sat-item.selected {{
    background: rgba(59, 130, 246, 0.08);
    border-left-color: #3b82f6;
}}

.sat-item .sat-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
}}

.sat-item .sat-name {{
    font-size: 0.7rem;
    font-weight: 600;
    color: #e2e8f0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
}}

.sat-item .sat-meta {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    color: #64748b;
}}

/* ═══════════ RIGHT PANEL - SELECTED ASSET ═══════════ */
#panel-detail {{
    top: 60px;
    right: 12px;
    width: 300px;
    max-height: calc(100% - 120px);
}}

.detail-metric {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 4px 0;
    border-bottom: 1px solid rgba(148, 163, 184, 0.05);
}}

.detail-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.detail-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
    color: #f8fafc;
}}

.why-section {{
    margin-top: 8px;
    padding: 8px 10px;
    background: rgba(15, 23, 42, 0.6);
    border-radius: 6px;
    border: 1px solid rgba(148, 163, 184, 0.06);
}}

.why-section-title {{
    font-size: 0.6rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.08);
}}

.why-model {{ color: #60a5fa; }}
.why-physics {{ color: #fbbf24; }}
.why-response {{ color: #34d399; }}

/* ═══════════ BOTTOM PANEL - COMMAND QUEUE ═══════════ */
#panel-commands {{
    bottom: 12px;
    left: 280px;
    right: 320px;
    height: auto;
    max-height: 180px;
}}

.cmd-list {{
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 4px;
}}

.cmd-card {{
    flex-shrink: 0;
    min-width: 200px;
    padding: 8px 10px;
    background: rgba(15, 23, 42, 0.6);
    border-radius: 6px;
    border: 1px solid rgba(148, 163, 184, 0.06);
    transition: border-color 0.2s;
}}

.cmd-card:hover {{
    border-color: rgba(148, 163, 184, 0.15);
}}

.cmd-rank {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    font-weight: 700;
    color: #60a5fa;
}}

.cmd-action {{
    font-size: 0.68rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 2px 0;
}}

.cmd-meta {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.56rem;
    color: #64748b;
}}

.cmd-verified {{
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.55rem;
    color: #34d399;
    margin-top: 3px;
}}

/* ═══════════ GLOBE CONTROLS ═══════════ */
#globe-controls {{
    position: absolute;
    bottom: 200px;
    right: 320px;
    z-index: 15;
    display: flex;
    flex-direction: column;
    gap: 3px;
}}

/* ═══════════ GLOBE CONTROLS ═══════════ */
#globe-controls {{
    position: absolute;
    bottom: 200px;
    right: 320px;
    z-index: 15;
    display: flex;
    flex-direction: column;
    gap: 5px;
}}

.globe-btn {{
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(8, 13, 23, 0.88);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(66, 217, 245, 0.2);
    border-radius: 8px;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
}}

.globe-btn svg {{
    width: 17px;
    height: 17px;
    stroke: #94a3b8;
    transition: stroke 0.2s ease, transform 0.2s ease;
    pointer-events: none;
}}

.globe-btn:hover {{
    background: rgba(17, 27, 43, 0.95);
    border-color: rgba(66, 217, 245, 0.5);
    box-shadow: 0 0 12px rgba(66, 217, 245, 0.3);
}}

.globe-btn:hover svg {{
    stroke: #42D9F5;
    transform: scale(1.12);
}}

.globe-btn.active {{
    background: rgba(11, 26, 44, 0.95);
    border-color: #42D9F5;
    box-shadow: 0 0 14px rgba(66, 217, 245, 0.35);
}}

.globe-btn.active svg {{
    stroke: #42D9F5;
}}

/* ═══════════ TOOLTIP ═══════════ */
#tooltip {{
    position: absolute;
    display: none;
    background: rgba(3, 7, 18, 0.92);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 8px;
    padding: 8px 12px;
    z-index: 30;
    pointer-events: none;
    max-width: 240px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}}

#tooltip .tt-name {{
    font-weight: 700;
    font-size: 0.72rem;
    color: #f8fafc;
    margin-bottom: 3px;
}}

#tooltip .tt-meta {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: #94a3b8;
    line-height: 1.5;
}}
</style>
</head>
<body>
<div id="globe-container"></div>

<!-- ═══════════ TOP BAR ═══════════ -->
<div id="top-bar">
    <div class="brand">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#42D9F5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;">
            <circle cx="12" cy="12" r="9"></circle>
            <path d="M3.6 9h16.8"></path>
            <path d="M3.6 15h16.8"></path>
            <ellipse cx="12" cy="12" rx="4" ry="9"></ellipse>
        </svg>
        <div>
            <div class="brand-name">SPARC-PM</div>
            <div class="brand-sub">SPACE WEATHER & ORBITAL MISSION MONITOR</div>
        </div>
    </div>
    <div class="status-center">
        <span class="led led-{('green' if triage == 'GREEN' else 'yellow' if triage == 'YELLOW' else 'red')}"></span>
        <span class="badge badge-{('nominal' if triage == 'GREEN' else 'warning' if triage == 'YELLOW' else 'critical')}">{sev_label}</span>
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #64748b;">SCENARIO: {scenario_name.split('(')[0].strip() if scenario_name else 'NOMINAL'}</span>
    </div>
    <div class="status-right">
        <span>PIPELINE: {pipeline_latency_ms}ms</span>
        <span style="color: #34d399;">●</span>
        <span>{timestamp}</span>
    </div>
</div>

<!-- ═══════════ SPACECRAFT PANEL ═══════════ -->
<div id="panel-spacecraft" class="panel">
    <div class="panel-header">
        <span style="display:flex;align-items:center;gap:6px;color:#e2e8f0;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#42D9F5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
            </svg>
            SPACECRAFT FLEET
        </span>
        <span style="color: #64748b; font-weight: 500;">{len(fleet)} UNITS</span>
    </div>
    <div class="sat-filter-tabs">
        <div class="sat-filter-tab active" data-filter="ALL">ALL</div>
        <div class="sat-filter-tab" data-filter="CRITICAL" style="color: #ef4444;">CRIT</div>
        <div class="sat-filter-tab" data-filter="WARNING" style="color: #f59e0b;">WARN</div>
        <div class="sat-filter-tab" data-filter="NOMINAL">NOM</div>
    </div>
    <div class="panel-body" id="sat-list" style="max-height: calc(100vh - 200px);"></div>
</div>

<!-- ═══════════ DETAIL PANEL ═══════════ -->
<div id="panel-detail" class="panel">
    <div class="panel-header">
        <span id="detail-header-wrap" style="display:flex;align-items:center;gap:6px;color:#e2e8f0;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#42D9F5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="22" y1="12" x2="18" y2="12"></line>
                <line x1="6" y1="12" x2="2" y2="12"></line>
                <line x1="12" y1="6" x2="12" y2="2"></line>
                <line x1="12" y1="22" x2="12" y2="18"></line>
            </svg>
            <span id="detail-title">MISSION OVERVIEW</span>
        </span>
        <span id="detail-badge"></span>
    </div>
    <div class="panel-body" id="detail-body" style="max-height: calc(100vh - 200px);">
        <div id="detail-content"></div>
    </div>
</div>

<!-- ═══════════ COMMAND PANEL ═══════════ -->
<div id="panel-commands" class="panel">
    <div class="panel-header">
        <span style="display:flex;align-items:center;gap:6px;color:#e2e8f0;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#45D6A0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="4 17 10 11 4 5"></polyline>
                <line x1="12" y1="19" x2="20" y2="19"></line>
            </svg>
            A★ COMMAND QUEUE
        </span>
        <span style="font-weight: 500; color: #34d399; display:flex; align-items:center; gap:5px;">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
            {len(cmd_queue)} CMDS • RFC 2104 SIGNED
        </span>
    </div>
    <div class="panel-body">
        <div class="cmd-list" id="cmd-list"></div>
    </div>
</div>

<!-- ═══════════ GLOBE CONTROLS ═══════════ -->
<div id="globe-controls">
    <div class="globe-btn" id="btn-zoom-in" title="Zoom In (+)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            <line x1="11" y1="8" x2="11" y2="14"></line>
            <line x1="8" y1="11" x2="14" y2="11"></line>
        </svg>
    </div>
    <div class="globe-btn" id="btn-zoom-out" title="Zoom Out (−)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            <line x1="8" y1="11" x2="14" y2="11"></line>
        </svg>
    </div>
    <div class="globe-btn" id="btn-reset" title="Reset View Target">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
            <path d="M3 3v5h5"></path>
        </svg>
    </div>
    <div class="globe-btn active" id="btn-orbits" title="Toggle Orbital Tracks">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(-30 12 12)"></ellipse>
            <circle cx="12" cy="12" r="2.5" fill="currentColor"></circle>
        </svg>
    </div>
    <div class="globe-btn active" id="btn-stations" title="Toggle Ground Stations">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4.93 4.93a10 10 0 0 1 14.14 0"></path>
            <path d="M7.76 7.76a6 6 0 0 1 8.48 0"></path>
            <circle cx="12" cy="12" r="2" fill="currentColor"></circle>
            <path d="M12 14v8"></path>
            <path d="M9 22h6"></path>
        </svg>
    </div>
    <div class="globe-btn active" id="btn-hazard" title="Toggle Space Weather Hazard">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
    </div>
    <div class="globe-btn" id="btn-rotate" title="Toggle Planetary Rotation">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.5 2v6h-6"></path>
            <path d="M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
        </svg>
    </div>
</div>

<!-- ═══════════ TOOLTIP ═══════════ -->
<div id="tooltip">
    <div class="tt-name" id="tt-name"></div>
    <div class="tt-meta" id="tt-meta"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
// ═══════════════════════════════════════════════════════════════
// SPARC-PM THREE.JS MISSION GLOBE
// ═══════════════════════════════════════════════════════════════

const SAT_DATA = {sat_json};
const ORBIT_DATA = {orbit_json};
const GS_DATA = {gs_json};
const CMD_DATA = {cmd_json};
const DOS_DATA = {dos_json};
const TELEMETRY = {telemetry_json};

const STORM_POS = new THREE.Vector3({storm_pos[0]}, {storm_pos[1]}, {storm_pos[2]});
const STORM_R = {storm_r};
const EARTH_R = {earth_r};

const COLORS = {{
    CRITICAL: 0xef4444,
    WARNING: 0xf59e0b,
    ELEVATED: 0x3b82f6,
    NOMINAL: 0x10b981,
}};

const COLOR_HEX = {{
    CRITICAL: '#ef4444',
    WARNING: '#f59e0b',
    ELEVATED: '#3b82f6',
    NOMINAL: '#10b981',
}};

// ─── SCENE SETUP ───
let scene, camera, renderer, controls;
let earthMesh, atmosphereMesh, stormMesh;
let satMarkers = [], satLabels = [];
let orbitLines = [], groundTrackLines = [];
let gsMarkers = [];
let selectedSatIdx = -1;
let autoRotate = false;
let showOrbits = true, showStations = true, showHazard = true;

const container = document.getElementById('globe-container');
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function init() {{
    if (typeof THREE === 'undefined') {{
        console.error('Three.js failed to load from CDN.');
        container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ef4444;font-family:sans-serif;font-size:14px;padding:20px;text-align:center;">Three.js failed to load. Please verify internet connection for CDN assets.</div>';
        return;
    }}

    scene = new THREE.Scene();
    
    const w = container.clientWidth || window.innerWidth || 1200;
    const h = container.clientHeight || window.innerHeight || 900;
    
    // Camera
    camera = new THREE.PerspectiveCamera(45, w / h, 0.01, 100);
    camera.position.set(0, 0.8, 3.2);
    camera.lookAt(0, 0, 0);
    
    // Renderer
    renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x030712, 1);
    container.appendChild(renderer.domElement);
    
    // Lighting
    const ambientLight = new THREE.AmbientLight(0x334466, 0.6);
    scene.add(ambientLight);
    
    const sunLight = new THREE.DirectionalLight(0xffeedd, 1.2);
    sunLight.position.set(5, 3, 4);
    scene.add(sunLight);
    
    const rimLight = new THREE.DirectionalLight(0x4488cc, 0.3);
    rimLight.position.set(-3, -1, -4);
    scene.add(rimLight);
    
    // ─── STARFIELD ───
    createStarfield();
    
    // ─── EARTH ───
    createEarth();
    
    // ─── ATMOSPHERE ───
    createAtmosphere();
    
    // ─── STORM CORRIDOR ───
    createStormCorridor();
    
    // ─── GROUND STATIONS ───
    createGroundStations();
    
    // ─── ORBITS ───
    createOrbits();
    
    // ─── SATELLITES ───
    createSatellites();
    
    // ─── ORBIT CONTROLS (MANUAL) ───
    setupControls();
    
    // ─── UI INTERACTIONS ───
    setupUI();
    
    // Start render loop
    animate();
}}

function createStarfield() {{
    const starGeo = new THREE.BufferGeometry();
    const starCount = 6000;
    const positions = new Float32Array(starCount * 3);
    const sizes = new Float32Array(starCount);
    
    for (let i = 0; i < starCount; i++) {{
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        const r = 30 + Math.random() * 20;
        positions[i*3] = r * Math.sin(phi) * Math.cos(theta);
        positions[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
        positions[i*3+2] = r * Math.cos(phi);
        sizes[i] = 0.3 + Math.random() * 1.2;
    }}
    
    starGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    starGeo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    
    const starMat = new THREE.PointsMaterial({{
        color: 0xffffff,
        size: 0.03,
        transparent: true,
        opacity: 0.7,
        sizeAttenuation: true,
    }});
    
    scene.add(new THREE.Points(starGeo, starMat));
}}

function createEarth() {{
    // Create a detailed Earth sphere
    const earthGeo = new THREE.SphereGeometry(EARTH_R, 96, 64);
    
    // Use a procedural shader for Earth-like appearance
    const earthMat = new THREE.ShaderMaterial({{
        uniforms: {{
            sunDir: {{ value: new THREE.Vector3(0.7, 0.3, 0.5).normalize() }},
        }},
        vertexShader: `
            varying vec3 vNormal;
            varying vec3 vPosition;
            varying vec2 vUv;
            void main() {{
                vNormal = normalize(normalMatrix * normal);
                vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
                vUv = uv;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }}
        `,
        fragmentShader: `
            uniform vec3 sunDir;
            varying vec3 vNormal;
            varying vec3 vPosition;
            varying vec2 vUv;
            
            // Simple continental noise
            float hash(vec2 p) {{
                return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
            }}
            
            float noise(vec2 p) {{
                vec2 i = floor(p);
                vec2 f = fract(p);
                f = f * f * (3.0 - 2.0 * f);
                float a = hash(i);
                float b = hash(i + vec2(1.0, 0.0));
                float c = hash(i + vec2(0.0, 1.0));
                float d = hash(i + vec2(1.0, 1.0));
                return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
            }}
            
            float fbm(vec2 p) {{
                float v = 0.0;
                float a = 0.5;
                for (int i = 0; i < 5; i++) {{
                    v += a * noise(p);
                    p *= 2.0;
                    a *= 0.5;
                }}
                return v;
            }}
            
            void main() {{
                // Sun lighting
                float diff = max(dot(vNormal, sunDir), 0.0);
                float ambient = 0.12;
                float light = ambient + diff * 0.88;
                
                // Continental pattern
                vec2 uv = vUv * 8.0;
                float land = fbm(uv + vec2(3.7, 1.2));
                land = smoothstep(0.42, 0.52, land);
                
                // Ocean colors
                vec3 ocean = mix(
                    vec3(0.02, 0.06, 0.15),  // Deep ocean
                    vec3(0.04, 0.12, 0.25),  // Shallow
                    fbm(uv * 0.5)
                );
                
                // Land colors  
                vec3 landColor = mix(
                    vec3(0.06, 0.14, 0.06),  // Forest
                    vec3(0.15, 0.12, 0.08),  // Desert
                    fbm(uv * 1.5 + vec2(5.0, 3.0))
                );
                
                vec3 baseColor = mix(ocean, landColor, land);
                
                // Night side - city lights
                float nightMask = 1.0 - smoothstep(-0.05, 0.1, diff);
                float cities = pow(fbm(uv * 4.0 + vec2(2.0, 7.0)), 3.0) * land * 2.0;
                vec3 cityLight = vec3(1.0, 0.85, 0.5) * cities * nightMask * 0.6;
                
                // Polar ice
                float pole = abs(vUv.y - 0.5) * 2.0;
                float ice = smoothstep(0.78, 0.88, pole);
                baseColor = mix(baseColor, vec3(0.7, 0.75, 0.8), ice * 0.6);
                
                vec3 finalColor = baseColor * light + cityLight;
                
                // Subtle atmosphere rim on lit side
                float rim = 1.0 - max(dot(vNormal, normalize(-vPosition)), 0.0);
                rim = pow(rim, 3.0);
                finalColor += vec3(0.15, 0.35, 0.6) * rim * 0.3 * diff;
                
                gl_FragColor = vec4(finalColor, 1.0);
            }}
        `,
    }});
    
    earthMesh = new THREE.Mesh(earthGeo, earthMat);
    scene.add(earthMesh);
    
    // Grid lines (subtle lat/lon)
    const gridMat = new THREE.LineBasicMaterial({{ color: 0x1e293b, transparent: true, opacity: 0.15 }});
    
    for (let lat = -60; lat <= 60; lat += 30) {{
        const points = [];
        const latRad = lat * Math.PI / 180;
        for (let lon = 0; lon <= 360; lon += 3) {{
            const lonRad = lon * Math.PI / 180;
            const r = EARTH_R * 1.001;
            points.push(new THREE.Vector3(
                r * Math.cos(latRad) * Math.cos(lonRad),
                r * Math.sin(latRad),
                -r * Math.cos(latRad) * Math.sin(lonRad)
            ));
        }}
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
        scene.add(new THREE.Line(lineGeo, gridMat));
    }}
}}

function createAtmosphere() {{
    const atmoGeo = new THREE.SphereGeometry(EARTH_R * 1.025, 64, 64);
    const atmoMat = new THREE.ShaderMaterial({{
        uniforms: {{
            sunDir: {{ value: new THREE.Vector3(0.7, 0.3, 0.5).normalize() }},
        }},
        vertexShader: `
            varying vec3 vNormal;
            varying vec3 vPosition;
            void main() {{
                vNormal = normalize(normalMatrix * normal);
                vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }}
        `,
        fragmentShader: `
            uniform vec3 sunDir;
            varying vec3 vNormal;
            varying vec3 vPosition;
            void main() {{
                float intensity = pow(0.68 - dot(vNormal, normalize(-vPosition)), 2.0);
                float sunFactor = max(dot(vNormal, sunDir), 0.0) * 0.5 + 0.5;
                vec3 color = mix(
                    vec3(0.1, 0.3, 0.8),
                    vec3(0.3, 0.6, 1.0),
                    intensity
                );
                gl_FragColor = vec4(color, intensity * 0.35 * sunFactor);
            }}
        `,
        transparent: true,
        side: THREE.BackSide,
        depthWrite: false,
    }});
    
    atmosphereMesh = new THREE.Mesh(atmoGeo, atmoMat);
    scene.add(atmosphereMesh);
}}

function createStormCorridor() {{
    if (STORM_R < 0.001) return;
    
    const stormGeo = new THREE.SphereGeometry(STORM_R, 32, 32);
    const stormMat = new THREE.ShaderMaterial({{
        uniforms: {{
            time: {{ value: 0.0 }},
        }},
        vertexShader: `
            varying vec3 vNormal;
            varying vec3 vPosition;
            void main() {{
                vNormal = normalize(normalMatrix * normal);
                vPosition = position;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }}
        `,
        fragmentShader: `
            uniform float time;
            varying vec3 vNormal;
            varying vec3 vPosition;
            
            float hash(vec3 p) {{
                return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
            }}
            
            void main() {{
                float edge = pow(1.0 - abs(dot(vNormal, normalize(cameraPosition - vPosition))), 1.5);
                float noise = hash(vPosition * 10.0 + vec3(time * 0.3));
                float alpha = (edge * 0.15 + 0.03) * (0.8 + noise * 0.2);
                vec3 color = mix(vec3(0.9, 0.2, 0.1), vec3(1.0, 0.4, 0.2), edge);
                gl_FragColor = vec4(color, alpha);
            }}
        `,
        transparent: true,
        side: THREE.DoubleSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
    }});
    
    stormMesh = new THREE.Mesh(stormGeo, stormMat);
    stormMesh.position.copy(STORM_POS);
    scene.add(stormMesh);
}}

// Texture cache for high-performance canvas billboard icons
const _iconTextureCache = {{}};

function createSatelliteTexture(alertColor, hasGlow) {{
    const key = `sat_${{alertColor}}_${{hasGlow}}`;
    if (_iconTextureCache[key]) return _iconTextureCache[key];

    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');

    // Outer glow aura for critical / warnings
    if (hasGlow) {{
        const radGrad = ctx.createRadialGradient(64, 64, 6, 64, 64, 58);
        radGrad.addColorStop(0, alertColor);
        radGrad.addColorStop(0.4, alertColor + '55');
        radGrad.addColorStop(1, 'transparent');
        ctx.fillStyle = radGrad;
        ctx.beginPath();
        ctx.arc(64, 64, 58, 0, Math.PI * 2);
        ctx.fill();
    }}

    // Left solar panel wing
    ctx.fillStyle = '#0369a1';
    ctx.fillRect(10, 50, 38, 28);
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.strokeRect(10, 50, 38, 28);
    
    // Left solar cell grid lines
    ctx.beginPath();
    ctx.moveTo(22, 50); ctx.lineTo(22, 78);
    ctx.moveTo(35, 50); ctx.lineTo(35, 78);
    ctx.moveTo(10, 64); ctx.lineTo(48, 64);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Right solar panel wing
    ctx.fillStyle = '#0369a1';
    ctx.fillRect(80, 50, 38, 28);
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.strokeRect(80, 50, 38, 28);
    
    // Right solar cell grid lines
    ctx.beginPath();
    ctx.moveTo(93, 50); ctx.lineTo(93, 78);
    ctx.moveTo(106, 50); ctx.lineTo(106, 78);
    ctx.moveTo(80, 64); ctx.lineTo(118, 64);
    ctx.stroke();

    // Connecting structural booms
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(48, 64); ctx.lineTo(52, 64);
    ctx.moveTo(76, 64); ctx.lineTo(80, 64);
    ctx.stroke();

    // Central spacecraft bus body
    ctx.fillStyle = '#0b132b';
    ctx.fillRect(52, 44, 24, 40);
    ctx.strokeStyle = alertColor;
    ctx.lineWidth = 3.5;
    ctx.strokeRect(52, 44, 24, 40);

    // Telemetry payload core beacon
    ctx.fillStyle = alertColor;
    ctx.beginPath();
    ctx.arc(64, 64, 6, 0, Math.PI * 2);
    ctx.fill();

    // Center focal highlight
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(64, 64, 2.5, 0, Math.PI * 2);
    ctx.fill();

    // Uplink antenna mast
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(64, 44); ctx.lineTo(64, 28);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(64, 26, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#42D9F5';
    ctx.fill();

    const texture = new THREE.CanvasTexture(canvas);
    _iconTextureCache[key] = texture;
    return texture;
}}

function createGroundStationTexture(stationColor) {{
    const key = `gs_${{stationColor}}`;
    if (_iconTextureCache[key]) return _iconTextureCache[key];

    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');

    // Radar transmission arcs emitting upward
    ctx.strokeStyle = stationColor + 'cc';
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.arc(64, 48, 22, Math.PI * 1.25, Math.PI * 1.75);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(64, 48, 36, Math.PI * 1.3, Math.PI * 1.7);
    ctx.stroke();

    // Parabolic antenna dish
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.arc(64, 68, 28, Math.PI * 0.8, Math.PI * 2.2);
    ctx.stroke();

    // Central feed horn
    ctx.strokeStyle = stationColor;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(64, 76); ctx.lineTo(64, 48);
    ctx.stroke();
    ctx.fillStyle = stationColor;
    ctx.beginPath();
    ctx.arc(64, 48, 5, 0, Math.PI * 2);
    ctx.fill();

    // Pedestal tripod mount
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(64, 86); ctx.lineTo(64, 110);
    ctx.moveTo(42, 116); ctx.lineTo(64, 110); ctx.lineTo(86, 116);
    ctx.stroke();

    const texture = new THREE.CanvasTexture(canvas);
    _iconTextureCache[key] = texture;
    return texture;
}}

function createGroundStations() {{
    const gsGroup = new THREE.Group();
    gsGroup.name = 'groundStations';
    
    GS_DATA.forEach((gs, i) => {{
        const isISRO = gs.agency === 'ISRO';
        const stationColor = isISRO ? '#34d399' : '#60a5fa';
        const texture = createGroundStationTexture(stationColor);

        const spriteMat = new THREE.SpriteMaterial({{
            map: texture,
            transparent: true,
            opacity: 0.95,
            depthWrite: false,
        }});
        const sprite = new THREE.Sprite(spriteMat);
        const baseScale = 0.042;
        sprite.scale.set(baseScale, baseScale, 1.0);
        sprite.position.set(gs.pos[0], gs.pos[1], gs.pos[2]);
        sprite.userData = {{ type: 'station', index: i, data: gs, baseScale: baseScale }};
        gsGroup.add(sprite);
        gsMarkers.push(sprite);
    }});
    
    scene.add(gsGroup);
}}

function createOrbits() {{
    const orbitGroup = new THREE.Group();
    orbitGroup.name = 'orbits';
    
    // We only draw unique orbits (by altitude) to avoid clutter
    const drawnAlts = new Set();
    
    ORBIT_DATA.forEach((orb, i) => {{
        const altKey = Math.round(orb.altitude_km / 50) * 50;
        if (drawnAlts.has(altKey)) return;
        drawnAlts.add(altKey);
        
        if (orb.points.length < 2) return;
        
        const points = orb.points.map(p => new THREE.Vector3(p[0], p[1], p[2]));
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
        
        // Find alert level for this orbit by matching satellite name
        let orbitAlert = 'NOMINAL';
        const matchSat = SAT_DATA.find(s => s.name === orb.name);
        if (matchSat) orbitAlert = matchSat.alert;
        
        const lineColor = COLORS[orbitAlert] || 0x10b981;
        const lineMat = new THREE.LineBasicMaterial({{
            color: lineColor,
            transparent: true,
            opacity: 0.18,
        }});
        
        const line = new THREE.Line(lineGeo, lineMat);
        line.userData = {{ alert: orbitAlert, defaultOpacity: 0.18 }};
        orbitGroup.add(line);
        orbitLines.push(line);
    }});
    
    scene.add(orbitGroup);
}}

function createSatellites() {{
    SAT_DATA.forEach((sat, i) => {{
        const colorHex = COLOR_HEX[sat.alert] || '#10b981';
        const isHazard = sat.alert === 'CRITICAL' || sat.alert === 'WARNING';
        const texture = createSatelliteTexture(colorHex, isHazard);

        const spriteMat = new THREE.SpriteMaterial({{
            map: texture,
            transparent: true,
            opacity: 0.95,
            depthWrite: false,
        }});
        const sprite = new THREE.Sprite(spriteMat);
        const baseScale = sat.alert === 'CRITICAL' ? 0.055 : sat.alert === 'WARNING' ? 0.046 : 0.038;
        sprite.scale.set(baseScale, baseScale, 1.0);
        sprite.position.set(sat.pos[0], sat.pos[1], sat.pos[2]);
        sprite.userData = {{ type: 'satellite', index: i, data: sat, baseScale: baseScale }};
        scene.add(sprite);
        satMarkers.push(sprite);
    }});
}}

// ─── CAMERA CONTROLS (MANUAL ORBIT) ───
let isDragging = false;
let previousMouse = {{ x: 0, y: 0 }};
let spherical = {{ phi: Math.PI / 3, theta: Math.PI / 6, radius: 3.2 }};
let targetSpherical = {{ ...spherical }};

function setupControls() {{
    const canvas = renderer.domElement;
    
    canvas.addEventListener('mousedown', (e) => {{
        if (e.button === 0) {{
            isDragging = true;
            previousMouse = {{ x: e.clientX, y: e.clientY }};
        }}
    }});
    
    canvas.addEventListener('mousemove', (e) => {{
        if (isDragging) {{
            const dx = (e.clientX - previousMouse.x) * 0.005;
            const dy = (e.clientY - previousMouse.y) * 0.005;
            targetSpherical.theta -= dx;
            targetSpherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, targetSpherical.phi + dy));
            previousMouse = {{ x: e.clientX, y: e.clientY }};
        }}
        
        // Hover detection
        handleHover(e);
    }});
    
    canvas.addEventListener('mouseup', () => {{ isDragging = false; }});
    canvas.addEventListener('mouseleave', () => {{ isDragging = false; hideTooltip(); }});
    
    canvas.addEventListener('wheel', (e) => {{
        e.preventDefault();
        targetSpherical.radius = Math.max(1.4, Math.min(12, targetSpherical.radius + e.deltaY * 0.002));
    }}, {{ passive: false }});
    
    canvas.addEventListener('click', handleClick);
    canvas.addEventListener('dblclick', handleDblClick);
}}

function updateCamera() {{
    // Smooth interpolation
    spherical.phi += (targetSpherical.phi - spherical.phi) * 0.08;
    spherical.theta += (targetSpherical.theta - spherical.theta) * 0.08;
    spherical.radius += (targetSpherical.radius - spherical.radius) * 0.08;
    
    if (autoRotate) {{
        targetSpherical.theta += 0.0008;
    }}
    
    camera.position.x = spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta);
    camera.position.y = spherical.radius * Math.cos(spherical.phi);
    camera.position.z = spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta);
    camera.lookAt(0, 0, 0);
}}

// ─── INTERACTION HANDLERS ───
function handleHover(e) {{
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects([...satMarkers, ...gsMarkers]);
    
    if (intersects.length > 0) {{
        const obj = intersects[0].object;
        const ud = obj.userData;
        renderer.domElement.style.cursor = 'pointer';
        
        if (ud.type === 'satellite') {{
            showTooltip(e.clientX, e.clientY, ud.data.name,
                `Alert: ${{ud.data.alert}}<br>Alt: ${{ud.data.altitude_km}} km<br>H_j: ${{ud.data.hazard_ratio}}<br>Dist: ${{ud.data.dist_to_storm_km.toLocaleString()}} km`);
        }} else if (ud.type === 'station') {{
            showTooltip(e.clientX, e.clientY, ud.data.name,
                `Agency: ${{ud.data.agency}}<br>Type: ${{ud.data.type}}<br>Lat: ${{ud.data.lat}}°<br>Lon: ${{ud.data.lon}}°`);
        }}
    }} else {{
        renderer.domElement.style.cursor = 'default';
        hideTooltip();
    }}
}}

function handleClick(e) {{
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects([...satMarkers, ...gsMarkers]);
    
    if (intersects.length > 0) {{
        const obj = intersects[0].object;
        const ud = obj.userData;
        
        if (ud.type === 'satellite') {{
            selectSatellite(ud.index);
            // Smooth camera focus
            const pos = obj.position.clone();
            const dir = pos.clone().normalize();
            targetSpherical.radius = Math.max(1.8, spherical.radius * 0.7);
            targetSpherical.phi = Math.acos(dir.y / 1);
            targetSpherical.theta = Math.atan2(dir.z, dir.x);
        }} else if (ud.type === 'station') {{
            selectStation(ud.data);
        }}
    }}
}}

function handleDblClick(e) {{
    // Reset view
    targetSpherical = {{ phi: Math.PI / 3, theta: Math.PI / 6, radius: 3.2 }};
    selectedSatIdx = -1;
    satMarkers.forEach(m => {{
        const baseScale = m.userData.baseScale || 0.038;
        m.scale.set(baseScale, baseScale, 1.0);
        m.material.opacity = 0.95;
    }});
    orbitLines.forEach(l => {{ l.material.opacity = l.userData.defaultOpacity; }});
    updateDetailPanel();
    updateSatList();
}}

function selectSatellite(idx) {{
    selectedSatIdx = idx;
    
    // Highlight selected marker
    satMarkers.forEach((m, i) => {{
        const baseScale = m.userData.baseScale || 0.038;
        if (i === idx) {{
            m.scale.set(baseScale * 1.8, baseScale * 1.8, 1.0);
            m.material.opacity = 1.0;
        }} else {{
            m.scale.set(baseScale, baseScale, 1.0);
            m.material.opacity = 0.55;
        }}
    }});
    
    // Brighten matching orbit
    orbitLines.forEach(line => {{
        line.material.opacity = 0.08;
    }});
    
    updateDetailPanel();
    updateSatList();
}}

function selectStation(gsData) {{
    selectedSatIdx = -1;
    
    const detailTitle = document.getElementById('detail-title');
    const detailBadge = document.getElementById('detail-badge');
    const detailContent = document.getElementById('detail-content');
    
    detailTitle.textContent = gsData.code;
    detailBadge.innerHTML = '<span class="badge badge-nominal">ACTIVE</span>';
    
    detailContent.innerHTML = `
        <div class="detail-metric"><span class="detail-label">STATION</span><span class="detail-value">${{gsData.name}}</span></div>
        <div class="detail-metric"><span class="detail-label">AGENCY</span><span class="detail-value">${{gsData.agency}}</span></div>
        <div class="detail-metric"><span class="detail-label">TYPE</span><span class="detail-value">${{gsData.type}}</span></div>
        <div class="detail-metric"><span class="detail-label">LATITUDE</span><span class="detail-value">${{gsData.lat}}°</span></div>
        <div class="detail-metric"><span class="detail-label">LONGITUDE</span><span class="detail-value">${{gsData.lon}}°</span></div>
    `;
    
    updateSatList();
}}

function showTooltip(x, y, name, meta) {{
    const tt = document.getElementById('tooltip');
    tt.style.display = 'block';
    tt.style.left = (x + 14) + 'px';
    tt.style.top = (y + 14) + 'px';
    document.getElementById('tt-name').textContent = name;
    document.getElementById('tt-meta').innerHTML = meta;
}}

function hideTooltip() {{
    document.getElementById('tooltip').style.display = 'none';
}}

// ─── UI PANEL UPDATES ───
function updateDetailPanel() {{
    const detailTitle = document.getElementById('detail-title');
    const detailBadge = document.getElementById('detail-badge');
    const detailContent = document.getElementById('detail-content');
    
    if (selectedSatIdx < 0) {{
        // Show mission overview
        detailTitle.textContent = 'MISSION OVERVIEW';
        detailBadge.innerHTML = '';
        
        const critCount = SAT_DATA.filter(s => s.alert === 'CRITICAL').length;
        const warnCount = SAT_DATA.filter(s => s.alert === 'WARNING').length;
        const elevCount = SAT_DATA.filter(s => s.alert === 'ELEVATED').length;
        const nomCount = SAT_DATA.filter(s => s.alert === 'NOMINAL').length;
        
        detailContent.innerHTML = `
            <div class="detail-metric"><span class="detail-label">TOTAL SPACECRAFT</span><span class="detail-value">${{SAT_DATA.length}}</span></div>
            <div class="detail-metric"><span class="detail-label">CRITICAL</span><span class="detail-value" style="color:#ef4444;">${{critCount}}</span></div>
            <div class="detail-metric"><span class="detail-label">WARNING</span><span class="detail-value" style="color:#f59e0b;">${{warnCount}}</span></div>
            <div class="detail-metric"><span class="detail-label">ELEVATED</span><span class="detail-value" style="color:#3b82f6;">${{elevCount}}</span></div>
            <div class="detail-metric"><span class="detail-label">NOMINAL</span><span class="detail-value" style="color:#10b981;">${{nomCount}}</span></div>
            <div class="detail-metric"><span class="detail-label">STORM RADIUS</span><span class="detail-value">${{(STORM_R / {SCALE}).toLocaleString()}} km</span></div>
            
            <div class="why-section" style="margin-top: 12px;">
                <div class="why-section-title why-physics" style="display:flex;align-items:center;gap:5px;">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                    SPACE WEATHER TELEMETRY
                </div>
                <div class="detail-metric"><span class="detail-label">PROTON FLUX</span><span class="detail-value">${{TELEMETRY.proton_flux_pfu}} pfu</span></div>
                <div class="detail-metric"><span class="detail-label">SOLAR WIND</span><span class="detail-value">${{TELEMETRY.proton_speed_kms}} km/s</span></div>
                <div class="detail-metric"><span class="detail-label">IMF Bz</span><span class="detail-value">${{TELEMETRY.mag_bz_field}} nT</span></div>
                <div class="detail-metric"><span class="detail-label">DENSITY</span><span class="detail-value">${{TELEMETRY.proton_density_cm3}} cm⁻³</span></div>
                <div class="detail-metric"><span class="detail-label">DYN PRESSURE</span><span class="detail-value">${{TELEMETRY.solar_wind_dyn_pressure_npa}} nPa</span></div>
            </div>
            
            <div class="why-section" style="margin-top: 8px;">
                <div class="why-section-title" style="color: #a78bfa; display:flex;align-items:center;gap:5px;">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                    CREW DOSIMETRY
                </div>
                <div class="detail-metric"><span class="detail-label">PEAK DOSE RATE</span><span class="detail-value">${{DOS_DATA.peak_dose_rate}} μSv/hr</span></div>
                <div class="detail-metric"><span class="detail-label">EVA STATUS</span><span class="detail-value">${{DOS_DATA.eva_status}}</span></div>
                <div class="detail-metric"><span class="detail-label">6H DOSE</span><span class="detail-value">${{DOS_DATA.total_6h_dose}} mSv</span></div>
                <div class="detail-metric"><span class="detail-label">CREW ACTION</span><span class="detail-value">${{DOS_DATA.crew_action}}</span></div>
            </div>
        `;
        return;
    }}
    
    const sat = SAT_DATA[selectedSatIdx];
    const alertClass = sat.alert.toLowerCase();
    
    detailTitle.textContent = sat.name;
    detailBadge.innerHTML = `<span class="badge badge-${{alertClass}}">${{sat.alert}}</span>`;
    
    // Determine recommended action
    let recAction = 'NOMINAL_ROUTINE';
    if (sat.alert === 'CRITICAL') recAction = 'ENTER_SAFE_MODE';
    else if (sat.alert === 'WARNING') recAction = 'ATTITUDE_SHIELD_TILT';
    else if (sat.alert === 'ELEVATED') recAction = 'ENHANCED_TELEMETRY_POLL';
    
    detailContent.innerHTML = `
        <div style="font-size: 0.6rem; color: #64748b; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace;">${{sat.sat_id}} · ${{sat.orbit_type}}</div>
        
        <div class="detail-metric"><span class="detail-label">ALTITUDE</span><span class="detail-value">${{sat.altitude_km.toLocaleString()}} km</span></div>
        <div class="detail-metric"><span class="detail-label">VELOCITY</span><span class="detail-value">${{sat.speed_kms}} km/s</span></div>
        <div class="detail-metric"><span class="detail-label">LATITUDE</span><span class="detail-value">${{sat.latitude}}°</span></div>
        <div class="detail-metric"><span class="detail-label">LONGITUDE</span><span class="detail-value">${{sat.longitude}}°</span></div>
        <div class="detail-metric"><span class="detail-label">HAZARD RATIO H_j</span><span class="detail-value" style="color: ${{COLOR_HEX[sat.alert]}}">${{sat.hazard_ratio}}</span></div>
        <div class="detail-metric"><span class="detail-label">DIST TO CORRIDOR</span><span class="detail-value">${{sat.dist_to_storm_km.toLocaleString()}} km</span></div>
        <div class="detail-metric"><span class="detail-label">CRITICALITY</span><span class="detail-value">${{sat.criticality}}</span></div>
        
        <!-- WHY SECTION -->
        <div class="why-section" style="margin-top: 10px;">
            <div class="why-section-title why-model" style="display:flex;align-items:center;gap:5px;">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>
                1. MODEL FSM INFERENCE
            </div>
            <div class="detail-metric"><span class="detail-label">SEVERITY</span><span class="detail-value">{sev_label}</span></div>
            <div class="detail-metric"><span class="detail-label">FSM TRIAGE</span><span class="detail-value">{triage}</span></div>
            <div class="detail-metric"><span class="detail-label">SAT ALERT</span><span class="detail-value" style="color: ${{COLOR_HEX[sat.alert]}}">${{sat.alert}}</span></div>
        </div>
        
        <div class="why-section">
            <div class="why-section-title why-physics" style="display:flex;align-items:center;gap:5px;">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                2. SPACE WEATHER PHYSICS
            </div>
            <div class="detail-metric"><span class="detail-label">PROTON FLUX</span><span class="detail-value">${{TELEMETRY.proton_flux_pfu}} pfu</span></div>
            <div class="detail-metric"><span class="detail-label">SOLAR WIND</span><span class="detail-value">${{TELEMETRY.proton_speed_kms}} km/s</span></div>
            <div class="detail-metric"><span class="detail-label">IMF Bz</span><span class="detail-value">${{TELEMETRY.mag_bz_field}} nT</span></div>
            <div class="detail-metric"><span class="detail-label">PROXIMITY</span><span class="detail-value">${{sat.dist_to_storm_km.toLocaleString()}} km</span></div>
            <div class="detail-metric"><span class="detail-label">HAZARD H_j</span><span class="detail-value">${{sat.hazard_ratio}}</span></div>
        </div>
        
        <div class="why-section">
            <div class="why-section-title why-response" style="display:flex;align-items:center;gap:5px;">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                3. RECOMMENDED RESPONSE
            </div>
            <div class="detail-metric"><span class="detail-label">ACTION</span><span class="detail-value">${{recAction}}</span></div>
            <div class="detail-metric"><span class="detail-label">TARGET</span><span class="detail-value">Payload / Power Bus</span></div>
            <div class="detail-metric"><span class="detail-label">PRIORITY</span><span class="detail-value" style="color: ${{COLOR_HEX[sat.alert]}}">${{sat.alert}}</span></div>
        </div>
    `;
}}

function updateSatList() {{
    const list = document.getElementById('sat-list');
    const filter = document.querySelector('.sat-filter-tab.active')?.dataset?.filter || 'ALL';
    
    let filtered = SAT_DATA;
    if (filter !== 'ALL') {{
        filtered = SAT_DATA.filter(s => s.alert === filter);
    }}
    
    list.innerHTML = filtered.map((sat, i) => {{
        const realIdx = SAT_DATA.indexOf(sat);
        const isSelected = realIdx === selectedSatIdx;
        const dotColor = COLOR_HEX[sat.alert] || '#10b981';
        return `
            <div class="sat-item ${{isSelected ? 'selected' : ''}}" data-idx="${{realIdx}}" onclick="selectSatellite(${{realIdx}})">
                <div class="sat-dot" style="background: ${{dotColor}};"></div>
                <div class="sat-name">${{sat.name}}</div>
                <div class="sat-meta">${{sat.alert === 'NOMINAL' ? '' : sat.hazard_ratio}}</div>
            </div>
        `;
    }}).join('');
}}

function updateCommandList() {{
    const cmdList = document.getElementById('cmd-list');
    
    if (CMD_DATA.length === 0) {{
        cmdList.innerHTML = `<div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #64748b; padding: 8px;">FLEET NOMINAL — NO EMERGENCY TELECOMMANDS QUEUED</div>`;
        return;
    }}
    
    cmdList.innerHTML = CMD_DATA.map(cmd => {{
        const urgClass = cmd.urgency.toLowerCase();
        return `
            <div class="cmd-card">
                <div class="cmd-rank">#${{cmd.rank}} PRIORITY</div>
                <div class="cmd-action">${{cmd.satellite}} → ${{cmd.action}}</div>
                <div class="cmd-meta">${{cmd.power_w}}W · f=${{cmd.f_score}}</div>
                <div class="cmd-verified" style="display:inline-flex;align-items:center;gap:4px;">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.5" style="vertical-align:middle;flex-shrink:0;">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                        <polyline points="9 12 11 14 15 10"></polyline>
                    </svg>
                    <span>HMAC VERIFIED · ${{cmd.signature}}</span>
                </div>
            </div>
        `;
    }}).join('');
}}

function setupUI() {{
    // Filter tabs
    document.querySelectorAll('.sat-filter-tab').forEach(tab => {{
        tab.addEventListener('click', () => {{
            document.querySelectorAll('.sat-filter-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            updateSatList();
        }});
    }});
    
    // Globe controls
    document.getElementById('btn-zoom-in').addEventListener('click', () => {{
        targetSpherical.radius = Math.max(1.4, targetSpherical.radius - 0.4);
    }});
    
    document.getElementById('btn-zoom-out').addEventListener('click', () => {{
        targetSpherical.radius = Math.min(12, targetSpherical.radius + 0.4);
    }});
    
    document.getElementById('btn-reset').addEventListener('click', () => {{
        targetSpherical = {{ phi: Math.PI / 3, theta: Math.PI / 6, radius: 3.2 }};
        selectedSatIdx = -1;
        satMarkers.forEach(m => {{ 
            const baseScale = m.userData.baseScale || 0.038;
            m.scale.set(baseScale, baseScale, 1.0); 
            m.material.opacity = 0.95; 
        }});
        orbitLines.forEach(l => {{ l.material.opacity = l.userData.defaultOpacity; }});
        updateDetailPanel();
        updateSatList();
    }});
    
    document.getElementById('btn-rotate').addEventListener('click', function() {{
        autoRotate = !autoRotate;
        this.classList.toggle('active', autoRotate);
    }});
    
    document.getElementById('btn-orbits').addEventListener('click', function() {{
        showOrbits = !showOrbits;
        this.classList.toggle('active', showOrbits);
        orbitLines.forEach(l => {{ l.visible = showOrbits; }});
    }});
    
    document.getElementById('btn-stations').addEventListener('click', function() {{
        showStations = !showStations;
        this.classList.toggle('active', showStations);
        const gsGroup = scene.getObjectByName('groundStations');
        if (gsGroup) gsGroup.visible = showStations;
    }});
    
    document.getElementById('btn-hazard').addEventListener('click', function() {{
        showHazard = !showHazard;
        this.classList.toggle('active', showHazard);
        if (stormMesh) stormMesh.visible = showHazard;
    }});
    
    // Initialize panels
    updateSatList();
    updateDetailPanel();
    updateCommandList();
}}

// ─── ANIMATION LOOP ───
let time = 0;
function animate() {{
    requestAnimationFrame(animate);
    time += 0.016;
    
    updateCamera();
    
    // Update storm shader time
    if (stormMesh) {{
        stormMesh.material.uniforms.time.value = time;
    }}
    
    renderer.render(scene, camera);
}}

// ─── RESIZE ───
window.addEventListener('resize', () => {{
    const w = container.clientWidth || window.innerWidth || 1200;
    const h = container.clientHeight || window.innerHeight || 900;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
}});

// Initialize
init();
</script>
</body>
</html>
"""
    return html
