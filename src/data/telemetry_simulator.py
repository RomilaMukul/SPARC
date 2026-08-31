import pandas as pd
import numpy as np


def generate_time_index(minutes=1440):
    """
    Create a 1-minute timestamp series for synthetic telemetry.
    """
    start_time = pd.Timestamp.utcnow().floor("min") - pd.Timedelta(minutes=minutes - 1)
    return pd.date_range(start=start_time, periods=minutes, freq="min")


def generate_satellite_id(index):
    """
    Create a simple satellite ID naming pattern.
    """
    return f"SAT-{index:03d}"


def generate_satellite_profile(sat_index, storm_severity=0):
    """
    Create realistic baseline values per satellite with minor random variation.
    """
    base_voltage = 28.0 + (sat_index % 7) * 0.5
    base_temp = 22.0 + (sat_index % 9) * 2.5
    base_gyro = 0.15 + (sat_index % 8) * 0.04
    base_dose = 20 + (sat_index % 11) * 6

    if storm_severity == 0:
        voltage_bias = 0.0
        temp_bias = 0.0
        gyro_bias = 0.0
        dose_bias = 0.0
    elif storm_severity == 1:
        voltage_bias = -1.2
        temp_bias = 4.0
        gyro_bias = 0.18
        dose_bias = 30
    elif storm_severity == 2:
        voltage_bias = -2.6
        temp_bias = 8.0
        gyro_bias = 0.4
        dose_bias = 70
    else:
        voltage_bias = -4.5
        temp_bias = 13.0
        gyro_bias = 0.8
        dose_bias = 140

    return {
        "sat_id": generate_satellite_id(sat_index),
        "battery_voltage": base_voltage + voltage_bias + np.random.normal(0, 0.5),
        "subsystem_temp_c": base_temp + temp_bias + np.random.normal(0, 1.4),
        "gyro_drift_deg_hr": base_gyro + gyro_bias + np.random.normal(0, 0.08),
        "dosimeter_count": base_dose + dose_bias + np.random.normal(0, 8),
    }


def generate_fleet_telemetry(num_satellites=50, timesteps=1440):
    """
    Generate synthetic fleet telemetry for N satellites over T minutes.
    """
    timestamps = generate_time_index(minutes=timesteps)

    records = []

    for sat_index in range(1, num_satellites + 1):
        severity = sat_index % 4  # 0,1,2,3 cycling patterns

        for ts in timestamps:
            profile = generate_satellite_profile(sat_index, storm_severity=severity)

            risk_score = (
                max(0.0, 30 - profile["battery_voltage"]) * 0.4
                + max(0.0, profile["subsystem_temp_c"] - 30) * 0.5
                + profile["gyro_drift_deg_hr"] * 18
                + profile["dosimeter_count"] * 0.09
            )

            row = {
                "timestamp": ts,
                "sat_id": profile["sat_id"],
                "battery_voltage": round(profile["battery_voltage"], 3),
                "subsystem_temp_c": round(profile["subsystem_temp_c"], 3),
                "gyro_drift_deg_hr": round(profile["gyro_drift_deg_hr"], 4),
                "dosimeter_count": round(profile["dosimeter_count"], 2),
                "storm_severity": severity,
                "risk_score": round(risk_score, 4),
            }
            records.append(row)

    df = pd.DataFrame(records)

    output_path = "data/processed/synthetic_fleet_telemetry.csv"
    df.to_csv(output_path, index=False)

    print(f"✅ Synthetic fleet telemetry saved to: {output_path}")
    print(f"Rows generated: {len(df)}")
    print(f"Satellites: {num_satellites}")
    print(f"Minutes: {timesteps}")

    return df


if __name__ == "__main__":
    generate_fleet_telemetry()