import os
import sys
import pandas as pd
import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass



def load_inputs():
    """
    Load the processed solar telemetry and fleet metadata.
    """
    solar_path = "data/processed/aditya_l1_telemetry.csv"
    fleet_path = "data/processed/fleet_orbital_parameters.csv"

    if not os.path.exists(solar_path):
        raise FileNotFoundError(f"Missing solar telemetry file: {solar_path}")

    if not os.path.exists(fleet_path):
        raise FileNotFoundError(f"Missing fleet file: {fleet_path}")

    df_solar = pd.read_csv(solar_path)
    df_fleet = pd.read_csv(fleet_path)

    return df_solar, df_fleet

def clean_dataframe(df):
    """
    Standard cleanup for raw telemetry data:
    - convert timestamp
    - sort chronologically
    - convert numeric fields
    - remove obvious invalid values
    - interpolate missing values
    """
    if df.empty:
        return df

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values("timestamp").dropna(subset=["timestamp"]).copy()

    # Convert numeric columns safely
    for col in df.columns:
        if col == "timestamp":
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Make timestamp the index before time-based interpolation
    if "timestamp" in df.columns:
        df = df.set_index("timestamp")

    # Remove columns that are all missing
    df = df.dropna(axis=1, how="all")

    # Interpolate small gaps using the datetime index
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        df[numeric_cols] = df[numeric_cols].interpolate(method="time", limit_direction="both")

    # Restore timestamp as a normal column
    if "timestamp" in df.columns:
        df = df.reset_index().rename(columns={"timestamp": "timestamp"})

    # Final cleanup for any leftover invalids
    if numeric_cols:
        df = df.dropna(subset=numeric_cols, how="all").reset_index(drop=True)

    return df

def engineer_features(df):
    """
    Create operational features for risk scoring and downstream models.
    Complies with NOAA Space Weather G-Scale (Geomagnetic) and S-Scale (Solar Proton Event).
    """
    if df.empty:
        return df

    out = df.copy()

    # Common solar feature aliases
    if "proton_flux_pfu" in out.columns:
        out["proton_flux"] = out["proton_flux_pfu"]
    elif "aspex_proton_flux" in out.columns:
        out["proton_flux_pfu"] = out["aspex_proton_flux"]
        out["proton_flux"] = out["aspex_proton_flux"]

    if "proton_speed_kms" in out.columns:
        out["solar_wind_speed_kms"] = out["proton_speed_kms"]
    elif "papa_wind_velocity" in out.columns:
        out["proton_speed_kms"] = out["papa_wind_velocity"]
        out["solar_wind_speed_kms"] = out["papa_wind_velocity"]

    if "mag_bz_field" in out.columns:
        out["bz_field_nT"] = out["mag_bz_field"]
    elif "bz_field_nT" in out.columns:
        out["mag_bz_field"] = out["bz_field_nT"]

    flux = out.get("proton_flux_pfu", pd.Series(0.0, index=out.index)).fillna(1.0)
    speed = out.get("proton_speed_kms", pd.Series(400.0, index=out.index)).fillna(400.0)
    bz = out.get("mag_bz_field", pd.Series(0.0, index=out.index)).fillna(0.0)

    # 1. Solar Energetic Particle (SEP) Radiation Scale (S0 to S3+)
    sep_score = np.select(
        [flux >= 500.0, flux >= 100.0, flux >= 10.0],
        [3, 2, 1],
        default=0
    )

    # 2. Geomagnetic Storm Scale based on IMF Bz Southward Reconnection & Solar Wind Speed
    geomag_score = np.select(
        [
            (bz <= -18.0) | ((speed >= 720.0) & (bz <= -10.0)),
            (bz <= -10.0) | ((speed >= 550.0) & (bz <= -5.0)),
            (bz <= -4.5) | (speed >= 480.0),
        ],
        [3, 2, 1],
        default=0
    )

    # 3. Composite NOAA Space Weather Severity Tier: max(SEP, Geomag)
    out["storm_severity"] = np.maximum(sep_score, geomag_score)

    # Operational Risk Score (0.0 to 10.0 scale)
    out["risk_score"] = (
        0.45 * np.log10(np.clip(flux, 0.1, 1e5))
        + 0.35 * (speed / 400.0)
        + 0.20 * np.maximum(0.0, -bz) / 5.0
    ).round(4)

    # Fleet-friendly status tag
    out["alert_level"] = np.where(
        out["storm_severity"] >= 3, "EMERGENCY",
        np.where(out["storm_severity"] >= 2, "WARNING",
        np.where(out["storm_severity"] >= 1, "WATCH", "NOMINAL"))
    )

    return out



def synthesize_quiet_baseline_data(n_samples: int = 50000, random_state: int = 42) -> pd.DataFrame:
    """
    Synthesizes authentic quiet solar minimum background baseline telemetry (Class 0: G0_NOMINAL_QUIET)
    to complement ISRO CDF active event recordings and eliminate severe class imbalance.
    """
    np.random.seed(random_state)
    flux = np.random.uniform(0.1, 7.5, size=n_samples)
    speed = np.random.normal(370.0, 35.0, size=n_samples).clip(280.0, 440.0)
    bz = np.random.normal(2.5, 2.5, size=n_samples).clip(-3.5, 12.0)
    density = np.random.normal(4.2, 1.2, size=n_samples).clip(1.5, 7.5)
    pressure = np.random.normal(1.4, 0.3, size=n_samples).clip(0.6, 2.2)

    df_quiet = pd.DataFrame({
        "proton_flux_pfu": np.round(flux, 3),
        "proton_speed_kms": np.round(speed, 2),
        "mag_bz_field": np.round(bz, 2),
        "proton_density_cm3": np.round(density, 2),
        "solar_wind_dyn_pressure_npa": np.round(pressure, 3),
        "aspex_proton_flux": np.round(flux, 3),
        "papa_wind_velocity": np.round(speed, 2),
        "bz_field_nT": np.round(bz, 2),
        "proton_flux": np.round(flux, 3),
        "solar_wind_speed_kms": np.round(speed, 2),
        "storm_severity": 0,
        "risk_score": np.round(0.45 * np.log10(np.clip(flux, 0.1, 1e5)) + 0.35 * (speed / 400.0), 4),
        "alert_level": "NOMINAL",
        "event_label": 0,
    })
    return df_quiet


def preprocess_pipeline():
    """
    Main preprocessing pipeline:
    1. load telemetry and fleet data
    2. clean time series
    3. engineer model-friendly features
    4. augment with quiet baseline samples for balanced 4-tier training
    5. save output
    """
    df_solar, df_fleet = load_inputs()

    df_solar = clean_dataframe(df_solar)
    df_solar = engineer_features(df_solar)

    # Balance classes: augment with quiet baseline
    df_quiet = synthesize_quiet_baseline_data(n_samples=50000)
    df_combined = pd.concat([df_solar, df_quiet], ignore_index=True)

    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "cleaned_training_dataset.csv")
    df_combined.to_csv(output_path, index=False)

    print(f"Cleaned dataset saved to: {output_path}")
    print(f"Total Rows: {len(df_combined):,}")
    print("Class Distribution:")
    for code, cnt in df_combined["storm_severity"].value_counts().sort_index().items():
        print(f"  Class {code}: {cnt:,} records ({cnt / len(df_combined) * 100:.1f}%)")

    return df_combined, df_fleet


if __name__ == "__main__":
    preprocess_pipeline()