"""
Module: Space weather severity classifier (Naive Bayes)

Classifies each telemetry reading from Aditya-L1 into one of four severity
classes: Calm / Watch / Warning / Emergency.

IMPORTANT — how the labels are made:
Aditya-L1's public archive does not ship a ready-made "severity" label, so
there is no ground truth to train on directly. We bootstrap one: physically
motivated thresholds (based on typical quiet-Sun vs. disturbed-Sun ranges
for proton flux, solar wind speed, and the Bz component of the IMF) assign
a weak label to every row, and Naive Bayes is then trained to reproduce
that thresholding as a smooth, probabilistic classifier instead of a hard
if/else rule. This is a deliberate simplification for DA1 — documented here
and in the report's Feasibility Note — and should be revisited once a
validated event catalogue (e.g. NOAA SWPC's Kp-index history) is used to
replace the threshold-based labels with real historical ground truth.

Data in:  data/processed/aditya_l1_telemetry.csv
Data out: data/processed/severity_predictions.csv, plus a saved model
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

TELEMETRY_INPUT = "data/processed/aditya_l1_telemetry.csv"
PREDICTIONS_OUTPUT = "data/processed/severity_predictions.csv"
MODEL_OUTPUT = "data/processed/naive_bayes_model.joblib"

FEATURE_COLUMNS = ["aspex_proton_flux", "papa_wind_velocity", "mag_bz_field"]
SEVERITY_CLASSES = ["Calm", "Watch", "Warning", "Emergency"]


def weak_label(row) -> str:
    """Rule-based bootstrap label. Thresholds are illustrative, based on
    commonly cited quiet-vs-disturbed solar wind ranges (~300-500 km/s
    quiet, >600 km/s disturbed) and proton-flux flare-spike behaviour."""
    flux = row["aspex_proton_flux"]
    speed = row["papa_wind_velocity"]
    bz = row["mag_bz_field"]

    # Emergency: strong southward Bz (geo-effective) + high flux/speed
    if (bz < -8 and flux > 100) or flux > 500:
        return "Emergency"
    # Warning: elevated flux or fast wind stream with southward Bz
    if flux > 50 or (speed > 550 and bz < -4):
        return "Warning"
    # Watch: mild elevation above quiet-Sun baseline
    if flux > 15 or speed > 480 or bz < -2:
        return "Watch"
    return "Calm"


def build_training_set() -> pd.DataFrame:
    if not os.path.exists(TELEMETRY_INPUT):
        raise FileNotFoundError(
            f"'{TELEMETRY_INPUT}' not found. Run parse_aditya.py first."
        )
    df = pd.read_csv(TELEMETRY_INPUT)
    df = df.dropna(subset=FEATURE_COLUMNS)
    df["severity"] = df.apply(weak_label, axis=1)
    return df


def train_classifier(df: pd.DataFrame) -> GaussianNB:
    # .to_numpy() (not .values) forces a plain NumPy array even when pandas
    # is backed by PyArrow dtypes, which scikit-learn's internal indexing
    # does not handle reliably (see: TypeError in _safe_indexing).
    X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y = df["severity"].astype(str).to_numpy()

    # Guard against a degenerate split if one class barely appears
    class_counts = pd.Series(y).value_counts()
    stratify = y if class_counts.min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )

    model = GaussianNB()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("📊 Held-out validation report (vs. bootstrap threshold labels):")
    print(classification_report(y_test, y_pred, zero_division=0))

    return model


def classify_all(df: pd.DataFrame, model: GaussianNB) -> pd.DataFrame:
    X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    df["predicted_severity"] = model.predict(X)
    probs = model.predict_proba(X)
    for i, cls in enumerate(model.classes_):
        df[f"prob_{cls}"] = np.round(probs[:, i], 3)
    return df


def get_current_severity() -> dict:
    """Convenience function for the dashboard: trains (or loads) the model
    and returns the severity classification for the most recent reading."""
    df = build_training_set()

    if os.path.exists(MODEL_OUTPUT):
        model = joblib.load(MODEL_OUTPUT)
    else:
        model = train_classifier(df)
        os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
        joblib.dump(model, MODEL_OUTPUT)

    latest = df.sort_values("timestamp").iloc[-1]
    latest_X = latest[FEATURE_COLUMNS].to_numpy(dtype=float).reshape(1, -1)
    predicted = model.predict(latest_X)[0]
    probs = dict(zip(model.classes_, model.predict_proba(latest_X)[0].round(3)))

    return {
        "timestamp": latest["timestamp"],
        "severity": predicted,
        "probabilities": probs,
        "raw_values": {c: latest[c] for c in FEATURE_COLUMNS},
    }


if __name__ == "__main__":
    dataset = build_training_set()
    print(f"📖 Loaded {len(dataset)} telemetry rows, bootstrap label distribution:")
    print(dataset["severity"].value_counts())

    clf = train_classifier(dataset)

    os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
    joblib.dump(clf, MODEL_OUTPUT)
    print(f"💾 Model saved -> '{MODEL_OUTPUT}'")

    labeled = classify_all(dataset, clf)
    labeled.to_csv(PREDICTIONS_OUTPUT, index=False)
    print(f"✅ Wrote predictions -> '{PREDICTIONS_OUTPUT}'")

    current = get_current_severity()
    print(f"\n🚦 Current severity: {current['severity']}  (t = {current['timestamp']})")
    print(f"   Probabilities: {current['probabilities']}")