import os
import pandas as pd
import numpy as np


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
    """
    if df.empty:
        return df

    # Common solar feature aliases
    if "proton_flux_pfu" in df.columns:
        df["proton_flux"] = df["proton_flux_pfu"]

    if "proton_speed_kms" in df.columns:
        df["solar_wind_speed_kms"] = df["proton_speed_kms"]

    if "mag_bz_field" in df.columns:
        df["bz_field_nT"] = df["mag_bz_field"]

    # Storm severity encoding
    if "proton_flux_pfu" in df.columns:
        df["storm_severity"] = np.select(
            [
                df["proton_flux_pfu"] > 100,
                df["proton_flux_pfu"] > 40,
                df["proton_flux_pfu"] > 10,
            ],
            [3, 2, 1],
            default=0
        )

    # Risk score
    if "proton_flux_pfu" in df.columns and "proton_speed_kms" in df.columns:
        df["risk_score"] = (
            0.6 * df["proton_flux_pfu"].fillna(0)
            + 0.4 * df["proton_speed_kms"].fillna(0)
        ) / 1000.0

    # Fleet-friendly status tag
    if "storm_severity" in df.columns:
        df["alert_level"] = np.where(
            df["storm_severity"] >= 3, "EMERGENCY",
            np.where(df["storm_severity"] >= 2, "WARNING", "NORMAL")
        )

    return df


def preprocess_pipeline():
    """
    Main preprocessing pipeline:
    1. load telemetry and fleet data
    2. clean time series
    3. engineer model-friendly features
    4. save output
    """
    df_solar, df_fleet = load_inputs()

    df_solar = clean_dataframe(df_solar)
    df_solar = engineer_features(df_solar)

    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "cleaned_training_dataset.csv")
    df_solar.to_csv(output_path, index=False)

    print(f"✅ Cleaned dataset saved to: {output_path}")
    print(f"Rows: {len(df_solar)}")
    print(f"Columns: {list(df_solar.columns)}")

    return df_solar, df_fleet


if __name__ == "__main__":
    preprocess_pipeline()