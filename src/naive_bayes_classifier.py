import os
import joblib
import numpy as np
import pandas as pd
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support, confusion_matrix

TELEMETRY_INPUT = "data/processed/aditya_l1_telemetry.csv"
PREDICTIONS_OUTPUT = "data/processed/severity_predictions.csv"
MODEL_OUTPUT = "data/processed/naive_bayes_model.joblib"

FEATURE_COLUMNS = ["aspex_proton_flux", "papa_wind_velocity", "mag_bz_field"]
SEVERITY_CLASSES = ["Calm", "Watch", "Warning", "Emergency"]


def assign_ground_truth(df: pd.DataFrame) -> pd.Series:
    """Ground-truth severity labeling using NOAA SWPC Kp-index standard when available,
    falling back to robust self-calibrated percentile bootstrap if Kp column is missing or single-class."""
    if "noaa_kp_index" in df.columns:
        kp = df["noaa_kp_index"]
        labels = []
        for val in kp:
            if val >= 7.0:
                labels.append("Emergency")
            elif val >= 5.0:
                labels.append("Warning")
            elif val >= 4.0:
                labels.append("Watch")
            else:
                labels.append("Calm")
        s = pd.Series(labels, index=df.index)
        if len(s.unique()) >= 2:
            return s
            
    return weak_label(df)



def weak_label(df: pd.DataFrame) -> pd.Series:
    """Percentile-based bootstrap labeling fallback."""
    flux = df["aspex_proton_flux"]
    speed = df["papa_wind_velocity"]
    bz = df["mag_bz_field"]

    def robust_z(s: pd.Series) -> pd.Series:
        median = s.median()
        mad = (s - median).abs().median() + 1e-9
        return (s - median) / mad

    disturbance = robust_z(flux) + robust_z(speed) + robust_z(-bz)

    q99 = disturbance.quantile(0.99)
    q95 = disturbance.quantile(0.95)
    q80 = disturbance.quantile(0.80)

    def label_for(score):
        if score >= q99:
            return "Emergency"
        if score >= q95:
            return "Warning"
        if score >= q80:
            return "Watch"
        return "Calm"

    return disturbance.apply(label_for)


def rule_based_kp_baseline(df: pd.DataFrame) -> np.ndarray:
    """Dumb baseline: Operational practice simple thresholding rule.
    Emergency if flux > 500 or speed > 600 or Bz < -10, etc."""
    preds = []
    for _, row in df.iterrows():
        f = row["aspex_proton_flux"]
        s = row["papa_wind_velocity"]
        bz = row["mag_bz_field"]
        if f > 300.0 or bz < -12.0:
            preds.append("Emergency")
        elif f > 50.0 or bz < -6.0:
            preds.append("Warning")
        elif f > 20.0 or s > 500.0:
            preds.append("Watch")
        else:
            preds.append("Calm")
    return np.array(preds)


def compute_true_skill_statistic(y_true, y_pred, pos_class="Emergency"):
    """Compute True Skill Statistic (TSS = Sensitivity + Specificity - 1) for binary/pos class."""
    yt = (np.array(y_true) == pos_class).astype(int)
    yp = (np.array(y_pred) == pos_class).astype(int)
    
    tp = np.sum((yt == 1) & (yp == 1))
    tn = np.sum((yt == 0) & (yp == 0))
    fp = np.sum((yt == 0) & (yp == 1))
    fn = np.sum((yt == 1) & (yp == 0))
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    tss = sensitivity + specificity - 1.0
    return round(float(tss), 4)


def build_training_set() -> pd.DataFrame:
    if not os.path.exists(TELEMETRY_INPUT):
        raise FileNotFoundError(
            f"'{TELEMETRY_INPUT}' not found. Run parse_aditya.py first."
        )
    df = pd.read_csv(TELEMETRY_INPUT)
    df = df.dropna(subset=FEATURE_COLUMNS)
    df["severity"] = assign_ground_truth(df)
    return df


def train_and_evaluate_all_models(df: pd.DataFrame):
    """Train Naive Bayes, Logistic Regression, and evaluate vs. Rule-based baseline
    using a strict chronological train/validate split (80/20)."""
    df_sorted = df.sort_values("timestamp").reset_index(drop=True)
    
    X = df_sorted[FEATURE_COLUMNS].to_numpy(dtype=float)
    y = df_sorted["severity"].astype(str).to_numpy()
    
    # Chronological Split (matching DA1 §4.4 specification)
    split_idx = int(len(df_sorted) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    test_df = df_sorted.iloc[split_idx:].copy()

    # 1. Naive Bayes
    nb_model = GaussianNB()
    nb_model.fit(X_train, y_train)
    y_pred_nb = nb_model.predict(X_test)
    
    # 2. Logistic Regression
    lr_model = LogisticRegression(max_iter=1000)
    lr_model.fit(X_train, y_train)
    y_pred_lr = lr_model.predict(X_test)

    # 3. Rule-based baseline
    y_pred_rule = rule_based_kp_baseline(test_df)

    def summarize_metrics(y_true, y_pred, name):
        acc = accuracy_score(y_true, y_pred)
        p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
        tss = compute_true_skill_statistic(y_true, y_pred, pos_class="Emergency")
        print(f"\n--- Model Evaluation: {name} ---")
        print(f"Accuracy: {acc:.4f} | Weighted F1: {f1:.4f} | Precision: {p:.4f} | Recall: {r:.4f} | Emergency TSS: {tss:.4f}")
        return {
            "model_name": name,
            "accuracy": round(float(acc), 4),
            "weighted_f1": round(float(f1), 4),
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "emergency_tss": tss,
        }

    res_nb = summarize_metrics(y_test, y_pred_nb, "Naive Bayes (SPARC Core)")
    res_lr = summarize_metrics(y_test, y_pred_lr, "Logistic Regression Baseline")
    res_rule = summarize_metrics(y_test, y_pred_rule, "Rule-Based Kp Threshold Operational Baseline")

    print("\nNaive Bayes Classification Report:")
    print(classification_report(y_test, y_pred_nb, zero_division=0))

    return nb_model, {
        "naive_bayes": res_nb,
        "logistic_regression": res_lr,
        "rule_baseline": res_rule
    }


def classify_all(df: pd.DataFrame, model: GaussianNB) -> pd.DataFrame:
    X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    df["predicted_severity"] = model.predict(X)
    probs = model.predict_proba(X)
    for i, cls in enumerate(model.classes_):
        df[f"prob_{cls}"] = np.round(probs[:, i], 3)
    return df


def get_current_severity() -> dict:
    df = build_training_set()

    if os.path.exists(MODEL_OUTPUT):
        model = joblib.load(MODEL_OUTPUT)
    else:
        model, _ = train_and_evaluate_all_models(df)
        os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
        joblib.dump(model, MODEL_OUTPUT)

    latest = df.sort_values("timestamp").iloc[-1]
    latest_X = latest[FEATURE_COLUMNS].to_numpy(dtype=float).reshape(1, -1)
    predicted = model.predict(latest_X)[0]
    probs = {str(cls): float(prob) for cls, prob in zip(model.classes_, model.predict_proba(latest_X)[0].round(3))}

    return {
        "timestamp": latest["timestamp"],
        "severity": predicted,
        "probabilities": probs,
        "raw_values": {c: latest[c] for c in FEATURE_COLUMNS},
    }


if __name__ == "__main__":
    dataset = build_training_set()
    print(f"Loaded {len(dataset)} telemetry rows, ground-truth label distribution:")
    print(dataset["severity"].value_counts())

    clf, eval_results = train_and_evaluate_all_models(dataset)

    os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
    joblib.dump(clf, MODEL_OUTPUT)
    print(f"Model saved -> '{MODEL_OUTPUT}'")

    labeled = classify_all(dataset, clf)
    labeled.to_csv(PREDICTIONS_OUTPUT, index=False)
    print(f"Wrote predictions -> '{PREDICTIONS_OUTPUT}'")

    current = get_current_severity()
    print(f"\nCurrent severity: {current['severity']}  (t = {current['timestamp']})")
    print(f"   Probabilities: {current['probabilities']}")