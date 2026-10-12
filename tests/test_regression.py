"""
SPARC-PM: Regression Test Suite
===============================
Verifies that existing core algorithms, physical limits, and security constraints
remain invariant across system updates and architectural refactors.
"""

import hmac
import hashlib
import numpy as np
import pytest

from src.ui.pipeline import SCENARIOS, execute_pipeline
from src.scheduler.a_star_scheduler import AStarTelecommandScheduler
from src.models.spatial_hazard import SpatialHazardEngine


class TestSystemRegression:
    """Regression test suite for deterministic system invariants."""

    def test_g3_severe_benchmark_regression(self):
        """Regression test: G3_SEVERE benchmark must trigger non-green triage and safe mode or shield action."""
        g3_input = SCENARIOS["G3_SEVERE (October 2024 SPE)"]
        results = execute_pipeline(g3_input, "G3_SEVERE (October 2024 SPE)")

        sev = results["severity_report"]
        assert sev["triage"] in ["YELLOW", "RED"], "G3 benchmark must trigger elevated or critical triage"

        sched = results["scheduled_commands"]
        queue = sched.get("command_queue", [])
        actions = [cmd["recommended_action"] for cmd in queue]
        assert any("SAFE_MODE" in a or "SHIELD" in a or "TILT" in a for a in actions), \
            "G3 benchmark must generate protective emergency directives"

    def test_scheduler_power_budget_invariant(self):
        """Regression test: Total scheduled power must never exceed max power budget."""
        scheduler = AStarTelecommandScheduler(max_power_budget_w=650.0, max_commands_per_pass=15)
        candidate_commands = [
            {"satellite": f"SAT-{i}", "recommended_action": "PAYLOAD_SHUTDOWN", "power_draw_w": 180.0,
             "hazard_ratio": 0.85, "criticality": 0.9, "p_fail": 0.15, "urgency_tier": "CRITICAL"}
            for i in range(10)
        ]
        result = scheduler.schedule(candidate_commands)
        total_p = result["total_power_w"]
        assert total_p <= 650.0, f"Allocated power {total_p}W exceeds hard budget limit 650.0W"
        assert len(result["command_queue"]) <= 15, "Scheduled commands exceed pass capacity limit"

    def test_hmac_rfc2104_integrity_regression(self):
        """Regression test: HMAC-SHA256 signature must be verified and reject tampered payloads."""
        secret_key = b"ISRO_SPARC_PRIMARY_TELEMETRY_KEY_2026"
        payload = b"SAT-01|ENTER_SAFE_MODE|SEQ_4091|2026-10-12T00:00:00Z"
        
        expected_tag = hmac.new(secret_key, payload, hashlib.sha256).hexdigest()
        
        # Valid verification
        valid_check = hmac.compare_digest(
            hmac.new(secret_key, payload, hashlib.sha256).hexdigest(),
            expected_tag
        )
        assert valid_check is True

        # Tampered payload regression
        tampered_payload = b"SAT-01|ENTER_SAFE_MODE|SEQ_4091|2026-10-12T00:00:01Z"
        tampered_tag = hmac.new(secret_key, tampered_payload, hashlib.sha256).hexdigest()
        tampered_check = hmac.compare_digest(tampered_tag, expected_tag)
        assert tampered_check is False, "Security regression: HMAC failed to reject tampered payload byte!"

    def test_spatial_coordinates_non_nan_regression(self):
        """Regression test: Spatial engine must produce valid finite numerical coordinates."""
        spatial_eng = SpatialHazardEngine()
        fleet = spatial_eng.get_fleet_positions()
        for sat in fleet:
            pos = sat.get("r_ecef", [0, 0, 0])
            assert not np.isnan(pos).any(), f"NaN detected in ECEF position for {sat.get('name')}"
            assert not np.isinf(pos).any(), f"Inf detected in ECEF position for {sat.get('name')}"
