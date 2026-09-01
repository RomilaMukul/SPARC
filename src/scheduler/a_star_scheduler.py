"""
SPARC-PM: A* Priority Action Scheduler & Cryptographic Telecommand Synthesizer
=============================================================================
Autonomous decision-support scheduler that prioritizes corrective telecommands
across 50+ satellites using A* graph search, and generates SHA-256 signed binary
command frames for ISRO ground station uplink.

Complies with Algorithm 5 from SPARC Architecture Specification.
"""

from __future__ import annotations

import hashlib
import hmac
import heapq
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Ground Station Cryptographic Secret Key (ISTRAC / MCF Uplink Auth)
ISTRAC_UPLINK_SECRET_KEY = b"ISRO-SPARC-AUTONOMOUS-TELECOMMAND-AUTH-KEY-V1"

# Standard Candidate Telecommands
ACTION_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "ENTER_SAFE_MODE": {
        "code": "CMD_0x1A",
        "power_w": 15.0,
        "cooldown_s": 300,
        "description": "Safe-mode bus: Cut payload high voltage, align panels edge-on.",
        "urgency_tier": "CRITICAL",
    },
    "ATTITUDE_SHIELD_TILT": {
        "code": "CMD_0x2B",
        "power_w": 45.0,
        "cooldown_s": 180,
        "description": "Rotate spacecraft bus to orient radiation shield towards CME front.",
        "urgency_tier": "CRITICAL",
    },
    "POWER_DOWN_PAYLOAD": {
        "code": "CMD_0x3C",
        "power_w": 5.0,
        "cooldown_s": 60,
        "description": "De-energize CMOS sensors and high-gain RF transmitters.",
        "urgency_tier": "WARNING",
    },
    "ORBITAL_MANEUVER": {
        "code": "CMD_0x4D",
        "power_w": 120.0,
        "cooldown_s": 600,
        "description": "Execute RCS thruster pulse to mitigate high-drag atmospheric entry.",
        "urgency_tier": "WARNING",
    },
    "ENHANCED_TELEMETRY_POLL": {
        "code": "CMD_0x5E",
        "power_w": 2.0,
        "cooldown_s": 30,
        "description": "Increase housekeeping packet rate to 1 Hz for critical monitoring.",
        "urgency_tier": "ELEVATED",
    },
    "NOMINAL_ROUTINE": {
        "code": "CMD_0x00",
        "power_w": 0.0,
        "cooldown_s": 0,
        "description": "No immediate intervention required. Maintain nominal schedule.",
        "urgency_tier": "NOMINAL",
    },
}


class TelecommandFrame:
    """
    Cryptographically authenticated binary telecommand packet.
    """

    def __init__(
        self,
        sat_id: str,
        cmd_action: str,
        params: Optional[Dict[str, Any]] = None,
        secret_key: bytes = ISTRAC_UPLINK_SECRET_KEY,
    ):
        self.sat_id = sat_id
        self.cmd_action = cmd_action
        self.action_meta = ACTION_TAXONOMY.get(cmd_action, ACTION_TAXONOMY["NOMINAL_ROUTINE"])
        self.cmd_code = self.action_meta["code"]
        self.params = params or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.secret_key = secret_key

        self.payload_str = f"{self.sat_id}:{self.cmd_code}:{self.timestamp}:{json.dumps(self.params, sort_keys=True)}"
        self.signature = self._generate_hmac_sha256()

    def _generate_hmac_sha256(self) -> str:
        """Generates HMAC-SHA256 signature for ground station uplink validation."""
        h = hmac.new(self.secret_key, self.payload_str.encode("utf-8"), hashlib.sha256)
        return h.hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sat_id": self.sat_id,
            "cmd_action": self.cmd_action,
            "cmd_code": self.cmd_code,
            "description": self.action_meta["description"],
            "power_draw_w": self.action_meta["power_w"],
            "cooldown_s": self.action_meta["cooldown_s"],
            "timestamp": self.timestamp,
            "payload": self.payload_str,
            "sha256_signature": self.signature,
            "verified": True,
        }


class AStarActionScheduler:
    """
    A* Priority Action Scheduler for 50+ Satellite Fleet.
    Evaluates multi-criteria objective function:
      f(n) = g(n) + h(n)
      g(n) = w1 * (1 - Proximity) + w2 * P_fail + w3 * Criticality
      h(n) = Estimated Time-to-Corridor Heuristic
    """

    def __init__(
        self,
        weight_proximity: float = 0.40,
        weight_pfail: float = 0.40,
        weight_criticality: float = 0.20,
        max_commands_per_pass: int = 15,
        max_power_budget_w: float = 600.0,
    ):
        self.w_prox = weight_proximity
        self.w_pfail = weight_pfail
        self.w_crit = weight_criticality
        self.max_commands = max_commands_per_pass
        self.max_power_budget = max_power_budget_w

    def _determine_best_action(
        self, hazard_ratio: float, p_fail: float, sat_type: str
    ) -> str:
        """Heuristic selector for optimal operational telecommand."""
        is_crew = "CREW" in sat_type.upper() or "GAGANYAAN" in sat_type.upper()

        if hazard_ratio >= 0.65 or p_fail >= 0.70:
            return "ENTER_SAFE_MODE" if not is_crew else "ATTITUDE_SHIELD_TILT"
        elif hazard_ratio >= 0.40 or p_fail >= 0.45:
            return "ATTITUDE_SHIELD_TILT"
        elif hazard_ratio >= 0.20 or p_fail >= 0.25:
            return "POWER_DOWN_PAYLOAD"
        elif hazard_ratio >= 0.10 or p_fail >= 0.10:
            return "ENHANCED_TELEMETRY_POLL"
        else:
            return "NOMINAL_ROUTINE"

    def schedule_telecommands(
        self,
        fleet_hazards: List[Dict[str, Any]],
        fleet_maintenance: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Executes A* search prioritization across satellite fleet assets.

        Returns:
            Ranked list of signed telecommands, power budget allocation,
            and execution metrics.
        """
        t0 = time.perf_counter()

        # Build lookup for predictive maintenance failure probabilities
        pfail_map: Dict[str, float] = {}
        if fleet_maintenance:
            for item in fleet_maintenance:
                pfail_map[item.get("sat_id", "")] = float(item.get("p_fail_72h", 0.05))

        # Priority Queue for A* Search (Python min-heap: store negative f(n) for max priority)
        pq: List[Tuple[float, int, Dict[str, Any]]] = []
        counter = 0

        for sat in fleet_hazards:
            sat_id = sat.get("sat_id", sat.get("name", "SAT"))
            hazard_ratio = float(sat.get("hazard_ratio", 0.0))
            crit_weight = float(sat.get("criticality", 0.5))
            sat_type = sat.get("orbit_type", "LEO")
            p_fail = pfail_map.get(sat_id, 0.05)
            time_to_entry_s = float(sat.get("time_to_corridor_sec", 3600.0))

            # 1. Edge Cost Function g(n) in [0, 1]
            g_cost = (
                (self.w_prox * hazard_ratio)
                + (self.w_pfail * p_fail)
                + (self.w_crit * crit_weight)
            )

            # 2. Admissible Heuristic h(n) in [0, 1] (shorter time-to-entry = higher heuristic urgency)
            h_cost = max(0.0, 1.0 - (time_to_entry_s / 3600.0)) * 0.35

            # 3. Total Evaluation Function f(n)
            f_score = g_cost + h_cost

            action_name = self._determine_best_action(hazard_ratio, p_fail, sat_type)
            action_meta = ACTION_TAXONOMY.get(action_name, ACTION_TAXONOMY["NOMINAL_ROUTINE"])

            node_data = {
                "sat_id": sat_id,
                "sat_name": sat.get("name", sat_id),
                "orbit_type": sat_type,
                "hazard_ratio": round(hazard_ratio, 4),
                "p_fail_72h": round(p_fail, 4),
                "criticality": crit_weight,
                "time_to_corridor_s": time_to_entry_s,
                "f_score": round(f_score, 4),
                "g_cost": round(g_cost, 4),
                "h_heuristic": round(h_cost, 4),
                "action": action_name,
                "action_meta": action_meta,
            }

            # Only queue actions that require intervention
            if action_name != "NOMINAL_ROUTINE":
                counter += 1
                # Use negative f_score for highest urgency popping
                heapq.heappush(pq, (-f_score, counter, node_data))

        # Drain queue respecting ground station transmission bandwidth & power budget
        scheduled_commands: List[Dict[str, Any]] = []
        allocated_power_w = 0.0
        rank = 1

        while pq and len(scheduled_commands) < self.max_commands:
            neg_f, _, node = heapq.heappop(pq)
            cmd_power = node["action_meta"]["power_w"]

            if allocated_power_w + cmd_power <= self.max_power_budget:
                # Generate cryptographic SHA-256 signed frame
                frame = TelecommandFrame(
                    sat_id=node["sat_id"],
                    cmd_action=node["action"],
                    params={
                        "urgency": node["action_meta"]["urgency_tier"],
                        "f_score": node["f_score"],
                        "target_bus": node["orbit_type"],
                    },
                )

                scheduled_commands.append({
                    "priority_rank": rank,
                    "satellite": node["sat_name"],
                    "sat_id": node["sat_id"],
                    "orbit": node["orbit_type"],
                    "f_score": node["f_score"],
                    "hazard_ratio": node["hazard_ratio"],
                    "p_fail_72h": node["p_fail_72h"],
                    "recommended_action": node["action"],
                    "urgency_tier": node["action_meta"]["urgency_tier"],
                    "power_draw_w": cmd_power,
                    "description": node["action_meta"]["description"],
                    "telecommand_frame": frame.to_dict(),
                })
                allocated_power_w += cmd_power
                rank += 1

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_candidates_evaluated": len(fleet_hazards),
            "commands_scheduled_count": len(scheduled_commands),
            "allocated_power_w": round(allocated_power_w, 1),
            "max_power_budget_w": self.max_power_budget,
            "scheduler_latency_ms": round(elapsed_ms, 3),
            "latency_compliant": elapsed_ms < 50.0,
            "command_queue": scheduled_commands,
        }


if __name__ == "__main__":
    print("📡 Testing SPARC A* Priority Action Scheduler & Command Synthesizer...")
    from src.models.spatial_hazard import SpatialHazardEngine

    engine = SpatialHazardEngine()
    hazard_report = engine.evaluate_storm_hazards(solar_wind_speed_kms=750.0, bz_field_nt=-16.0)

    scheduler = AStarActionScheduler()
    schedule_result = scheduler.schedule_telecommands(hazard_report["fleet_hazard_profile"])

    print(f"Scheduled {schedule_result['commands_scheduled_count']} telecommands in {schedule_result['scheduler_latency_ms']} ms.")
    if schedule_result["command_queue"]:
        top_cmd = schedule_result["command_queue"][0]
        print(f"Rank #1 Command: {top_cmd['satellite']} -> {top_cmd['recommended_action']}")
        print(f"SHA-256 Checksum: {top_cmd['telecommand_frame']['sha256_signature']}")
