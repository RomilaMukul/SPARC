"""
Module: Solar Activity & Gaganyaan Crew Dosimetry Forecaster (LSTM)

Predicts 6-hour ahead solar proton flux trends using historical telemetry windows
and performs physical Simpson's-rule integration to compute cumulative radiation
dose (in mSv) for Gaganyaan crew members under spacecraft aluminum shielding.

Data in:  data/processed/aditya_l1_telemetry.csv
Models out: data/processed/lstm_forecaster.pt
"""

import os
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from scipy.integrate import simpson

TELEMETRY_INPUT = "data/processed/aditya_l1_telemetry.csv"
MODEL_PATH = "data/processed/lstm_forecaster.pt"
FORECAST_OUTPUT = "data/processed/dose_forecast.json"

# Physical constants for Gaganyaan crew dosimetry (derived from NASA/ISRO human spaceflight guidelines)
# Shielding attenuation factor for 5 g/cm^2 Aluminum equivalent spacecraft hull
ALUMINUM_SHIELDING_FACTOR = 1.25e-4  # mSv / (pfu * hour)
SAFETY_DOSE_LIMIT_MSV = 50.0        # 30-day NASA/ISRO astronaut radiation exposure limit (mSv)


class SolarFluxLSTM(nn.Module):
    def __init__(self, input_dim=3, hidden_dim=64, num_layers=2, forecast_steps=6, dropout=0.2):
        super(SolarFluxLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.forecast_steps = forecast_steps

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Linear(hidden_dim, forecast_steps)

    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        out, _ = self.lstm(x)
        last_hidden = out[:, -1, :]
        preds = self.fc(last_hidden)
        return preds


def prepare_sequences(df: pd.DataFrame, window_size=6, forecast_steps=6):
    """Create rolling sequences of input features and target proton flux."""
    features = df[["aspex_proton_flux", "papa_wind_velocity", "mag_bz_field"]].to_numpy(dtype=np.float32)
    target_flux = df["aspex_proton_flux"].to_numpy(dtype=np.float32)

    X, y = [], []
    for i in range(len(df) - window_size - forecast_steps + 1):
        X.append(features[i : i + window_size])
        y.append(target_flux[i + window_size : i + window_size + forecast_steps])

    return np.array(X), np.array(y)


def calculate_crew_dosimetry(predicted_flux: np.ndarray, time_step_hours: float = 1.0) -> dict:
    """Simpson's-rule integration of predicted solar proton flux over 6-hour window
    to compute expected cumulative crew dose (mSv) and alert status."""
    time_points = np.arange(len(predicted_flux)) * time_step_hours
    
    # Numerical integration using Simpson's rule
    cumulative_flux_integral = simpson(y=predicted_flux, x=time_points)
    
    # Calculate absorbed radiation dose in mSv
    dose_msv = cumulative_flux_integral * ALUMINUM_SHIELDING_FACTOR
    
    if dose_msv > SAFETY_DOSE_LIMIT_MSV:
        dose_status = "CRITICAL_EXPOSURE_RISK"
        action = "ORDER_CREW_TO_STORMSHELTER"
    elif dose_msv > 10.0:
        dose_status = "ELEVATED_RADIATION_WARNING"
        action = "MONITOR_DOSIMETRY_SENSOR_READINGS"
    else:
        dose_status = "NOMINAL_SAFE"
        action = "CONTINUE_STANDARD_EVA_OPERATIONS"

    return {
        "cumulative_flux_integral": round(float(cumulative_flux_integral), 2),
        "predicted_6hr_dose_msv": round(float(dose_msv), 4),
        "safety_limit_msv": SAFETY_DOSE_LIMIT_MSV,
        "dose_status": dose_status,
        "recommended_action": action,
    }


def train_and_evaluate_lstm():
    if not os.path.exists(TELEMETRY_INPUT):
        raise FileNotFoundError(f"'{TELEMETRY_INPUT}' not found. Run parse_aditya.py first.")

    df = pd.read_csv(TELEMETRY_INPUT).sort_values("timestamp").reset_index(drop=True)
    
    window_size = 12
    forecast_steps = 6
    X, y = prepare_sequences(df, window_size=window_size, forecast_steps=forecast_steps)

    # Chronological Split (80% Train, 20% Validation)
    split_idx = int(len(X) * 0.8)
    X_train, X_val = torch.tensor(X[:split_idx]), torch.tensor(X[split_idx:])
    y_train, y_val = torch.tensor(y[:split_idx]), torch.tensor(y[split_idx:])

    # Feature Normalization (per-feature mean & std)
    mean_X = X_train.mean(dim=(0, 1), keepdim=True)
    std_X = X_train.std(dim=(0, 1), keepdim=True)
    std_X[std_X == 0] = 1.0

    X_train_norm = (X_train - mean_X) / std_X
    X_val_norm = (X_val - mean_X) / std_X

    model = SolarFluxLSTM(input_dim=3, hidden_dim=64, num_layers=2, forecast_steps=forecast_steps, dropout=0.2)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.003)

    # Training Loop
    epochs = 25
    batch_size = 64
    dataset_train = torch.utils.data.TensorDataset(X_train_norm, y_train)
    loader = torch.utils.data.DataLoader(dataset_train, batch_size=batch_size, shuffle=False)

    model.train()
    for epoch in range(epochs):
        for bx, by in loader:
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()

    # Evaluation on Held-Out Validation Set
    model.eval()
    with torch.no_grad():
        preds_val = model(X_val_norm)
        val_mse = criterion(preds_val, y_val).item()
        val_rmse = float(np.sqrt(val_mse))

    print(f"LSTM Solar Flux Forecaster Trained Successfully.")
    print(f"Held-Out Validation RMSE: {val_rmse:.4f} pfu (vs. Literature Baseline BLEO Paper [6]: ~12.5 pfu)")

    # Save Trained Model & Normalization Stats
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    torch.save({
        "model_state_dict": model.state_dict(),
        "mean_X": mean_X,
        "std_X": std_X,
        "val_rmse": float(val_rmse)
    }, MODEL_PATH)

    # Run forecast on latest window
    latest_seq = torch.tensor(X[-1:]).float()
    latest_seq_norm = (latest_seq - mean_X) / std_X
    with torch.no_grad():
        latest_pred = model(latest_seq_norm).squeeze(0).numpy()

    dosimetry = calculate_crew_dosimetry(latest_pred)
    
    forecast_results = {
        "model_name": "SPARC 2-Layer LSTM Solar & Dose Forecaster",
        "val_rmse_pfu": round(float(val_rmse), 4),
        "sota_baseline_ref6_rmse": 12.50,
        "latest_predicted_6hr_flux": [round(float(v), 2) for v in latest_pred],
        "crew_dosimetry": dosimetry
    }

    import json
    with open(FORECAST_OUTPUT, "w") as f:
        json.dump(forecast_results, f, indent=2)

    return forecast_results


if __name__ == "__main__":
    results = train_and_evaluate_all = train_and_evaluate_lstm()
    print(f"\n6-Hour Solar Proton Flux Forecast (pfu): {results['latest_predicted_6hr_flux']}")
    print(f"Gaganyaan Crew Cumulative Dose: {results['crew_dosimetry']['predicted_6hr_dose_msv']} mSv ({results['crew_dosimetry']['dose_status']})")
