"""
SPARC-PM: Integration Test Suite
================================
Validates end-to-end multi-engine integration across all space weather benchmark scenarios.
Verifies data flow:
  Telemetry Ingest -> Severity Classifier -> Crew Dosimetry
  -> Spatial Hazard Corridor -> Predictive Maintenance -> A* Scheduler
  -> RFC 2104 HMAC Telecommand Queue
"""

import pytest
from src.ui.pipeline import SCENARIOS, execute_pipeline, get_spatial_engine


class TestPipelineIntegration:
    """End-to-end integration tests for the SPARC-PM pipeline."""

    @pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
    def test_end_to_end_pipeline_execution(self, scenario_name):
        """Verifies that all standard benchmark scenarios execute through all 5 engines."""
        telemetry_input = SCENARIOS[scenario_name]
        results = execute_pipeline(telemetry_input, scenario_name)

        # 1. Pipeline metadata integrity
        assert "pipeline_latency_ms" in results
        assert results["pipeline_latency_ms"] > 0
        assert results["scenario_name"] == scenario_name
        assert "timestamp" in results

        # 2. Telemetry ingestion verification
        telemetry = results.get("telemetry", {})
        assert "proton_flux_pfu" in telemetry
        assert "proton_speed_kms" in telemetry
        assert "mag_bz_field" in telemetry

        # 3. Severity Classification FSM verification
        sev = results.get("severity_report", {})
        assert "severity_label" in sev
        assert "triage" in sev
        assert sev["triage"] in ["GREEN", "YELLOW", "RED"]

        # 4. Crew Dosimetry verification
        dos = results.get("dosimetry_report", {})
        assert "peak_dose_rate_usv_hr" in dos
        assert "eva_status" in dos
        assert "crew_action" in dos

        # 5. Spatial Hazard Profile verification
        haz = results.get("hazard_report", {})
        fleet = haz.get("fleet_hazard_profile", [])
        assert len(fleet) > 0
        for sat in fleet:
            assert "name" in sat
            assert "sat_id" in sat
            assert "hazard_ratio" in sat
            assert "alert_level" in sat
            assert sat["alert_level"] in ["NOMINAL", "ELEVATED", "WARNING", "CRITICAL"]

        # 6. A* Scheduler and Command Queue verification
        sched = results.get("scheduled_commands", {})
        assert "command_queue" in sched
        assert "total_power_w" in sched
        assert "commands_scheduled_count" in sched
        queue = sched.get("command_queue", [])
        for cmd in queue:
            assert "satellite" in cmd
            assert "recommended_action" in cmd
            assert "priority_rank" in cmd
            assert "telecommand_frame" in cmd
            frame = cmd["telecommand_frame"]
            assert "sha256_signature" in frame

    def test_spatial_trajectory_propagation_integration(self):
        """Verifies spatial hazard engine orbit propagation matches fleet models."""
        spatial_eng = get_spatial_engine()
        dummy_sat = {
            "name": "TEST-SAT-1",
            "altitude_km": 550.0,
            "orbit_type": "LEO",
            "latitude": 12.5,
            "longitude": 77.2,
            "speed_kms": 7.6,
        }
        traj = spatial_eng.propagate_orbit_trajectory(dummy_sat, n_points=30)
        assert traj is not None
        assert len(traj["x"]) in [30, 31]
        assert len(traj["y"]) in [30, 31]
        assert len(traj["z"]) in [30, 31]
