from naive_bayes_classifier import get_current_severity
from orbital_position import compute_fleet_risk


def get_dashboard_snapshot() -> dict:
    severity_info = get_current_severity()
    risk_table = compute_fleet_risk(severity=severity_info["severity"])

    return {
        "severity": severity_info["severity"],
        "severity_probabilities": severity_info["probabilities"],
        "severity_timestamp": severity_info["timestamp"],
        "raw_values": severity_info.get("raw_values", {}),
        "satellite_risk_table": risk_table,
    }


if __name__ == "__main__":
    snapshot = get_dashboard_snapshot()
    print(f"Current severity: {snapshot['severity']}")
    print(snapshot["satellite_risk_table"].to_string(index=False))