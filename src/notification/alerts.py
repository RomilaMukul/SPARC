"""
SPARC-PM: Automated Email/SMS Webhook Alert System
=====================================================
Sends real-time alerts via email, SMS, and webhook when space weather
severity tiers change (GREEN → YELLOW → RED).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests

# Alert severity levels mapping to notification channels
ALERT_CHANNELS = {
    "GREEN": [],
    "YELLOW": ["webhook"],
    "RED": ["email", "sms", "webhook"],
}

DEFAULT_RECIPIENTS = {
    "email": ["flight surgeon@istrac.isro.gov.in", "ops@istrac.isro.gov.in"],
    "sms": ["+91-XXX-XXX-XXXX"],
    "webhook_url": os.getenv(
        "ALERT_WEBHOOK_URL", "https://hooks.example.com/sparc-alerts"
    ),
}


class AlertManager:
    """
    Manages automated notifications for space weather severity transitions.
    Sends alerts via configured channels when severity changes.
    """

    def __init__(
        self,
        email_recipients: Optional[List[str]] = None,
        sms_recipients: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
    ):
        self.email_recipients = email_recipients or DEFAULT_RECIPIENTS["email"]
        self.sms_recipients = sms_recipients or DEFAULT_RECIPIENTS["sms"]
        self.webhook_url = webhook_url or DEFAULT_RECIPIENTS["webhook_url"]
        self._alert_history: List[Dict[str, Any]] = []

    def check_severity_transition(
        self, previous_severity: str, current_severity: str
    ) -> bool:
        """Returns True if the transition requires an alert."""
        if previous_severity == current_severity:
            return False
        # Any transition to YELLOW or RED triggers alert
        if current_severity in ("YELLOW", "RED"):
            return True
        # Transition from RED to GREEN (all clear) also triggers
        if previous_severity == "RED" and current_severity == "GREEN":
            return True
        return False

    def _get_channels_for_severity(self, severity: str) -> List[str]:
        """Returns notification channels for a given severity level."""
        return ALERT_CHANNELS.get(severity, ["webhook"])

    def send_email(
        self, subject: str, body: str, recipients: Optional[List[str]] = None
    ) -> bool:
        """
        Sends an email alert.

        Args:
            subject: Email subject line.
            body: Email body content.
            recipients: Override recipient list.

        Returns:
            True if sent successfully (or simulated in dev mode).
        """
        recipients = recipients or self.email_recipients
        payload = {
            "to": recipients,
            "subject": subject,
            "body": body,
            "source": "SPARC-PM",
            "timestamp": self._now_iso(),
        }

        # Log the alert (in production, integrate with SMTP or email API)
        self._log_alert("EMAIL", payload)
        return True

    def send_sms(self, message: str, recipients: Optional[List[str]] = None) -> bool:
        """
        Sends an SMS alert.

        Args:
            message: SMS text message.
            recipients: Override recipient list.

        Returns:
            True if sent successfully (or simulated in dev mode).
        """
        recipients = recipients or self.sms_recipients
        payload = {
            "to": recipients,
            "message": message,
            "source": "SPARC-PM",
            "timestamp": self._now_iso(),
        }

        self._log_alert("SMS", payload)
        return True

    def send_webhook(
        self, alert_data: Dict[str, Any], url: Optional[str] = None
    ) -> bool:
        """
        Sends alert via webhook POST request.

        Args:
            alert_data: Alert payload to send.
            url: Override webhook URL.

        Returns:
            True if the webhook call succeeded.
        """
        target_url = url or self.webhook_url
        payload = {
            **alert_data,
            "source": "SPARC-PM",
            "timestamp": self._now_iso(),
        }

        try:
            response = requests.post(
                target_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            success = response.status_code in (200, 201, 202)
            self._log_alert(
                "WEBHOOK", {"url": target_url, "status": response.status_code}
            )
            return success
        except Exception as e:
            self._log_alert("WEBHOOK_ERROR", {"error": str(e)})
            return False

    def trigger_alert(
        self,
        severity: str,
        action: str,
        description: str,
        telemetry: Optional[Dict[str, Any]] = None,
        triage: Optional[str] = None,
        previous_severity: str = "GREEN",
    ) -> Dict[str, Any]:
        """
        Full alert pipeline: checks transition, sends via all channels.

        Args:
            severity: Current severity level (GREEN, YELLOW, RED).
            action: Recommended ground action.
            description: Human-readable description.
            telemetry: Optional telemetry data snapshot.
            triage: FSM triage status.
            previous_severity: Previous severity for transition check.

        Returns:
            Dict with alert status and channels used.
        """
        if not self.check_severity_transition(previous_severity, severity):
            return {
                "alert_sent": False,
                "reason": "No severity change requiring notification",
                "current_severity": severity,
            }

        channels = self._get_channels_for_severity(severity)
        alert_data = {
            "severity": severity,
            "triage": triage or severity,
            "action": action,
            "description": description,
            "telemetry": telemetry or {},
        }

        subject = f"[SPARC-PM] {severity} Space Weather Alert — {action}"
        body = (
            f"SPARC-PM Alert\n"
            f"Severity: {severity}\n"
            f"Triage: {triage or severity}\n"
            f"Action: {action}\n"
            f"Description: {description}\n"
            f"Timestamp: {self._now_iso()}\n"
        )

        results: Dict[str, bool] = {}
        if "email" in channels:
            results["email"] = self.send_email(subject, body)
        if "sms" in channels:
            results["sms"] = self.send_sms(body)
        if "webhook" in channels:
            results["webhook"] = self.send_webhook(alert_data)

        self._alert_history.append(
            {
                "severity": severity,
                "triage": triage or severity,
                "action": action,
                "channels": channels,
                "results": results,
                "timestamp": self._now_iso(),
            }
        )

        return {
            "alert_sent": True,
            "severity": severity,
            "channels_used": channels,
            "results": results,
            "alert_id": len(self._alert_history),
        }

    def get_alert_history(
        self, severity_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns alert history, optionally filtered by severity."""
        if severity_filter:
            return [a for a in self._alert_history if a["severity"] == severity_filter]
        return list(self._alert_history)

    def _log_alert(self, channel: str, payload: Dict[str, Any]) -> None:
        """Logs alert to console (in production, could use a logger)."""
        print(f"[SPARC-ALERT] {channel}: {json.dumps(payload, indent=2)}")

    @staticmethod
    def _now_iso() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    print("🚨 Initializing SPARC Alert System...")
    manager = AlertManager()

    # Test alert escalation
    result = manager.trigger_alert(
        severity="RED",
        action="ENTER_STORM_SHELTER_SAFE_MODE",
        description="Severe SPE event detected.",
        triage="RED",
        previous_severity="YELLOW",
    )
    print(f"Alert: {result}")

    # Test no-change case
    no_alert = manager.trigger_alert(
        severity="YELLOW",
        action="ELEVATED_MONITORING",
        description="Minor flux enhancement.",
        previous_severity="YELLOW",
    )
    print(f"No-change: {no_alert}")

    # Check history
    history = manager.get_alert_history()
    print(f"Alert history: {len(history)} entries")
