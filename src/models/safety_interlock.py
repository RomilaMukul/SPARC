"""
SPARC-PM: Manual Override Interlock Safety Window
==================================================
Enforces mandatory 10-second safety interlock between manual override commands
to prevent conflicting or rapid-fire satellite control actions.

Complies with constraint: "mandatory 10-second manual override safety interlock"
"""

from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

INTERLOCK_DURATION_SEC = 10.0  # Mandatory 10-second safety window


class InterlockViolation(Exception):
    """Raised when a manual override would violate the safety interlock."""

    pass


class InterlockExpired(Exception):
    """Raised when attempting to release an interlock that hasn't been set."""

    pass


class SafetyInterlock:
    """
    Manages manual override safety interlocks for satellite command operations.
    Enforces a mandatory cooldown window between override commands to ensure
    ground operators can verify commands before the next action becomes available.
    """

    def __init__(self, interlock_duration_sec: float = INTERLOCK_DURATION_SEC):
        self.interlock_duration = interlock_duration_sec
        self._active_overrides: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def request_override(
        self,
        sat_id: str,
        action: str,
        operator_id: str = "GROUND_OP",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Requests a manual override for a satellite.

        Args:
            sat_id: Target satellite identifier.
            action: Command action to execute.
            operator_id: ID of the ground operator requesting override.
            parameters: Optional command parameters.

        Returns:
            Dict with interlock status and release timestamp.

        Raises:
            InterlockViolation: If another override for this satellite is active.
        """
        current_time = datetime.now(timezone.utc)

        # Check if an active interlock exists for this satellite
        if sat_id in self._active_overrides:
            active = self._active_overrides[sat_id]
            released_at = active.get("released_at")
            if released_at is None:
                raise InterlockViolation(
                    f"Interlock active for {sat_id}. "
                    f"Override by {active['operator_id']} until "
                    f"{active['release_at']}. Wait {self.interlock_duration}s."
                )

        # Create new interlock entry
        release_at = current_time + timedelta(seconds=self.interlock_duration)
        interlock_entry = {
            "sat_id": sat_id,
            "action": action,
            "operator_id": operator_id,
            "parameters": parameters or {},
            "requested_at": current_time.isoformat(),
            "release_at": release_at.isoformat(),
            "status": "ACTIVE",
        }

        self._active_overrides[sat_id] = interlock_entry
        self._history.append(interlock_entry.copy())

        return {
            "status": "INTERLOCK_ACTIVE",
            "sat_id": sat_id,
            "action": action,
            "operator_id": operator_id,
            "requested_at": interlock_entry["requested_at"],
            "release_at": interlock_entry["release_at"],
            "interlock_duration_sec": self.interlock_duration,
            "message": (
                f"Manual override for {sat_id} locked for "
                f"{self.interlock_duration:.0f}s. Release at {release_at.isoformat()}."
            ),
        }

    def release_override(self, sat_id: str) -> Dict[str, Any]:
        """
        Releases the interlock for a satellite after the mandatory window.

        Args:
            sat_id: Satellite identifier to release.

        Returns:
            Dict confirming the interlock was released.

        Raises:
            InterlockExpired: If no active interlock exists for this satellite.
        """
        current_time = datetime.now(timezone.utc)

        if sat_id not in self._active_overrides:
            return {
                "status": "ALREADY_RELEASED",
                "sat_id": sat_id,
                "message": "Interlock already released (possibly force-released by supervisor).",
            }

        entry = self._active_overrides[sat_id]
        requested_at = datetime.fromisoformat(entry["requested_at"])
        elapsed = (current_time - requested_at).total_seconds()

        if elapsed < self.interlock_duration:
            remaining = self.interlock_duration - elapsed
            raise InterlockViolation(
                f"Cannot release interlock for {sat_id}. "
                f"{remaining:.1f}s remaining. Mandatory 10s safety window."
            )

        entry["released_at"] = current_time.isoformat()
        entry["status"] = "RELEASED"
        entry["elapsed_sec"] = round(elapsed, 2)

        self._active_overrides.pop(sat_id)

        return {
            "status": "INTERLOCK_RELEASED",
            "sat_id": sat_id,
            "action": entry["action"],
            "operator_id": entry["operator_id"],
            "requested_at": entry["requested_at"],
            "released_at": entry["released_at"],
            "elapsed_sec": round(elapsed, 2),
            "message": f"Interlock for {sat_id} released after {elapsed:.1f}s.",
        }

    def force_release_override(
        self, sat_id: str, operator_id: str = "SUPERVISOR"
    ) -> Dict[str, Any]:
        """
        Forces release of an interlock (emergency use by supervisor).

        Args:
            sat_id: Satellite identifier.
            operator_id: ID of the supervising operator.

        Returns:
            Dict confirming forced release.
        """
        if sat_id not in self._active_overrides:
            return {
                "status": "NO_ACTIVE_INTERLOCK",
                "sat_id": sat_id,
                "message": "No active interlock to force release.",
            }

        entry = self._active_overrides[sat_id]
        entry["status"] = "FORCE_RELEASED"
        entry["forced_by"] = operator_id
        entry["forced_at"] = datetime.now(timezone.utc).isoformat()

        self._history.append(entry.copy())
        self._active_overrides.pop(sat_id)

        return {
            "status": "FORCE_RELEASED",
            "sat_id": sat_id,
            "action": entry["action"],
            "forced_by": operator_id,
            "original_operator": entry["operator_id"],
            "forced_at": entry["forced_at"],
            "message": f"EMERGENCY FORCE RELEASE: {sat_id} override by {operator_id}.",
        }

    def get_active_overrides(self) -> List[Dict[str, Any]]:
        """Returns all currently active interlock overrides."""
        current_time = datetime.now(timezone.utc)
        active = []
        for sat_id, entry in self._active_overrides.items():
            release_at = datetime.fromisoformat(entry["release_at"])
            remaining = (release_at - current_time).total_seconds()
            entry["remaining_sec"] = round(max(0.0, remaining), 2)
            entry["status"] = "ACTIVE" if remaining > 0 else "EXPIRED"
            if remaining > 0:
                active.append(entry)
        return active

    def check_override_available(self, sat_id: str) -> Dict[str, Any]:
        """
        Checks if a manual override is available for a satellite.

        Returns:
            Dict with availability status and details.
        """
        if sat_id not in self._active_overrides:
            return {
                "available": True,
                "sat_id": sat_id,
                "message": "Override available.",
            }

        entry = self._active_overrides[sat_id]
        release_at = datetime.fromisoformat(entry["release_at"])
        remaining = (release_at - datetime.now(timezone.utc)).total_seconds()

        return {
            "available": remaining <= 0,
            "sat_id": sat_id,
            "action": entry["action"],
            "operator_id": entry["operator_id"],
            "remaining_sec": round(max(0.0, remaining), 2),
            "status": "ACTIVE" if remaining > 0 else "EXPIRED",
        }

    def get_stats(self) -> Dict[str, Any]:
        """Returns interlock operation statistics."""
        return {
            "total_requests": len(self._history),
            "active_overrides": len(self.get_active_overrides()),
            "interlock_duration_sec": self.interlock_duration,
            "history": len(self._history),
        }


if __name__ == "__main__":
    print("🛡️ Initializing SPARC Safety Interlock System...")
    interlock = SafetyInterlock()

    # Test normal flow
    result = interlock.request_override("99001", "ATTITUDE_SHIELD_TILT", "OP_001")
    print(f"Override: {result['status']} — {result['message']}")

    # Check availability
    avail = interlock.check_override_available("99001")
    print(f"Override available: {avail['available']}")

    # Check active
    active = interlock.get_active_overrides()
    print(f"Active overrides: {len(active)}")

    # Try to request again (should fail)
    try:
        interlock.request_override("99001", "ENTER_SAFE_MODE", "OP_002")
    except Exception as e:
        print(f"Expected error: {e}")

    # Force release
    forced = interlock.force_release_override("99001", "SUPERVISOR")
    print(f"Forced: {forced['status']}")

    # Release
    released = interlock.release_override("99001")
    print(f"Released: {released['status']}")

    print(f"Stats: {interlock.get_stats()}")
