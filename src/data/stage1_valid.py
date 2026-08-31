import os
import pandas as pd

required_files = [
    "data/processed/aditya_l1_telemetry.csv",
    "data/processed/fleet_orbital_parameters.csv",
    "data/processed/cleaned_training_dataset.csv",
    "data/processed/synthetic_fleet_telemetry.csv",
]

missing = [f for f in required_files if not os.path.exists(f)]

if missing:
    print("Missing files:")
    for f in missing:
        print(f" - {f}")
else:
    print("All required Stage 1 files exist.")

    for f in required_files:
        df = pd.read_csv(f)
        print(f"{f}: rows={len(df)}, cols={list(df.columns[:8])}")

    print("Stage 1 validation passed.")