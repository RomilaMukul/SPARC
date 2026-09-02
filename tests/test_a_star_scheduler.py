"""
Unit & Integration Tests for A* Priority Action Scheduler & Telecommand Synthesizer
==================================================================================
Tests A* priority queue ranking, power budget allocation, HMAC-SHA256 frame signing, and latency.
"""

import time
import pytest
from src.scheduler.a_star_scheduler import (
    AStarActionScheduler,
    TelecommandFrame,
    ACTION_TAXONOMY,
)


def test_telecommand_frame_signature_generation():
    """Verify HMAC-SHA256 cryptographic signature calculation."""
    frame = TelecommandFrame(
        sat_id="99001",
        cmd_action="ENTER_SAFE_MODE",
        params={"urgency": "CRITICAL"},
        secret_key=b"TEST-SECRET-KEY-1234",
    )

    frame_dict = frame.to_dict()
    assert "sha256_signature" in frame_dict
    assert len(frame_dict["sha256_signature"]) == 64  # SHA-256 hex string length
    assert frame_dict["sat_id"] == "99001"
    assert frame_dict["cmd_code"] == ACTION_TAXONOMY["ENTER_SAFE_MODE"]["code"]


def test_a_star_scheduler_telecommand_generation(sample_fleet_hazard_profile):
    """Verify A* scheduler ranks satellite candidates and stays within power budget."""
    scheduler = AStarActionScheduler(max_power_budget_w=600.0)
    result = scheduler.schedule_telecommands(fleet_hazards=sample_fleet_hazard_profile)

    assert "command_queue" in result
    assert "allocated_power_w" in result
    assert result["allocated_power_w"] <= 600.0
    assert result["commands_scheduled_count"] > 0

    top_command = result["command_queue"][0]
    assert "priority_rank" in top_command
    assert top_command["priority_rank"] == 1
    # Crew module with high hazard should be ranked #1
    assert top_command["sat_id"] == "99001"
    assert "sha256_signature" in top_command["telecommand_frame"]


def test_a_star_scheduler_latency_constraint(sample_fleet_hazard_profile):
    """Verify A* scheduler executes within 50ms (sub-50ms requirement)."""
    scheduler = AStarActionScheduler()

    t0 = time.perf_counter()
    result = scheduler.schedule_telecommands(fleet_hazards=sample_fleet_hazard_profile)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert latency_ms < 50.0, f"Scheduler latency ({latency_ms:.2f} ms) exceeded 50ms limit"
    assert result["latency_compliant"] is True
