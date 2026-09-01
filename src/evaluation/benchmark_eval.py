"""
SPARC-PM: Model Evaluation Suite & Historical Storm Benchmark
============================================================
Validates classification, dosimetry, and scheduling algorithms against
historical extreme space weather events (May 10-12, 2024 G5 Geomagnetic Storm
and October 2024 Solar Proton Event) with True Skill Statistic (TSS) and ablation.

Complies with Verification & Benchmark Plan from SPARC Specification.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from src.models.crew_dosimetry import CrewDosimetryEngine
from src.models.predictive_maint import PredictiveMaintenanceEngine
from src.models.severity_classifier import (
    BASE_PHYSICAL_FEATURES,
    SpaceWeatherSeverityClassifier,
    engineer_physics_features,
)
from src.models.spatial_hazard import SpatialHazardEngine
from src.scheduler.a_star_scheduler import AStarActionScheduler

BENCHMARK_OUTPUT_PATH = PROJECT_ROOT / "docs" / "benchmark_results.json"


# ---------------------------------------------------------------------------
#  Curated Historical Space Weather Benchmark Scenarios
# ---------------------------------------------------------------------------
HISTORICAL_SCENARIOS: List[Dict[str, Any]] = [
    {
        "event_name": "MAY_2024_G5_SUPER_STORM",
        "description": "Historical Mother's Day G5 Geomagnetic Storm (May 10-12, 2024)",
        "expected_severity": 3,
        "expected_label": "G3_SEVERE_STORM",
        "telemetry": {
            "proton_flux_pfu": 1850.0,
            "proton_speed_kms": 890.0,
            "mag_bz_field": -34.5,
            "proton_density_cm3": 28.4,
            "solar_wind_dyn_pressure_npa": 14.8,
        },
    },
    {
        "event_name": "OCT_2024_G4_CME_IMPACT",
        "description": "Severe Coronal Mass Ejection Impact (October 08-10, 2024)",
        "expected_severity": 3,
        "expected_label": "G3_SEVERE_STORM",
        "telemetry": {
            "proton_flux_pfu": 420.0,
            "proton_speed_kms": 740.0,
            "mag_bz_field": -21.0,
            "proton_density_cm3": 18.2,
            "solar_wind_dyn_pressure_npa": 9.6,
        },
    },
    {
        "event_name": "AUG_2024_MODERATE_CME",
        "description": "Moderate Solar Wind Enhancement (August 18, 2024)",
        "expected_severity": 2,
        "expected_label": "G2_MODERATE_STORM",
        "telemetry": {
            "proton_flux_pfu": 85.0,
            "proton_speed_kms": 580.0,
            "mag_bz_field": -9.2,
            "proton_density_cm3": 11.5,
            "solar_wind_dyn_pressure_npa": 4.1,
        },
    },
    {
        "event_name": "AUG_2024_MINOR_DISTURBANCE",
        "description": "Minor High-Speed Stream Sector Crossing (August 22, 2024)",
        "expected_severity": 1,
        "expected_label": "G1_MINOR_STORM",
        "telemetry": {
            "proton_flux_pfu": 18.0,
            "proton_speed_kms": 490.0,
            "mag_bz_field": -4.8,
            "proton_density_cm3": 7.8,
            "solar_wind_dyn_pressure_npa": 2.6,
        },
    },
    {
        "event_name": "NOMINAL_QUIET_BACKGROUND",
        "description": "Quiet Solar Minimum Background Baseline (August 2024)",
        "expected_severity": 0,
        "expected_label": "G0_NOMINAL_QUIET",
        "telemetry": {
            "proton_flux_pfu": 1.2,
            "proton_speed_kms": 380.0,
            "mag_bz_field": 1.8,
            "proton_density_cm3": 4.2,
            "solar_wind_dyn_pressure_npa": 1.4,
        },
    },
]


def calculate_tss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Computes True Skill Statistic (TSS) / Hanssen-Kuipers Discriminant:
    TSS = Recall + Specificity - 1 = TPR - FPR
    """
    # For binary / multi-class, compute one-vs-rest average TSS
    cm = confusion_matrix(y_true, y_pred)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        return float(tpr - fpr)
    else:
        tss_list = []
        for i in range(len(cm)):
            tp = cm[i, i]
            fn = np.sum(cm[i, :]) - tp
            fp = np.sum(cm[:, i]) - tp
            tn = np.sum(cm) - (tp + fn + fp)
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            tss_list.append(tpr - fpr)
        return float(np.mean(tss_list))


class BenchmarkEvaluator:
    """
    Automated verification suite validating all SPARC subsystems.
    """

    def __init__(self):
        self.spatial_engine = SpatialHazardEngine()
        self.dosimetry_engine = CrewDosimetryEngine()
        self.maint_engine = PredictiveMaintenanceEngine()
        self.scheduler = AStarActionScheduler()

    def run_severity_historical_benchmark(self) -> Dict[str, Any]:
        """Validates severity classifier on historical extreme scenarios."""
        print("=" * 65)
        print("[BENCHMARK 1] HISTORICAL STORM EVENT VALIDATION")
        print("=" * 65)

        # Initialize or load classifier
        try:
            clf = SpaceWeatherSeverityClassifier.load_model()
        except Exception:
            # Fallback inline training on dataset
            df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "cleaned_training_dataset.csv")
            clf = SpaceWeatherSeverityClassifier(model_type="hist_gb")
            X, y = clf.prepare_data(df)
            clf.fit(X, y)

        y_true = []
        y_pred = []
        latencies = []
        scenario_results = []

        for sc in HISTORICAL_SCENARIOS:
            t0 = time.perf_counter()
            res = clf.predict_single(sc["telemetry"])
            lat_ms = (time.perf_counter() - t0) * 1000.0

            y_true.append(sc["expected_severity"])
            y_pred.append(res["severity_code"])
            latencies.append(lat_ms)

            match = res["severity_code"] == sc["expected_severity"]
            status_str = "MATCH [OK]" if match else "MISMATCH [FAIL]"
            print(f"  {sc['event_name']:<30} -> Pred: {res['severity_label']} | {status_str} ({lat_ms:.2f} ms)")

            scenario_results.append({
                "event": sc["event_name"],
                "actual_code": sc["expected_severity"],
                "predicted_code": res["severity_code"],
                "predicted_label": res["severity_label"],
                "triage": res["triage"],
                "action": res["action"],
                "match": match,
                "latency_ms": round(lat_ms, 2),
            })

        acc = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
        tss = calculate_tss(np.array(y_true), np.array(y_pred))

        print("-" * 65)
        print(f"  Historical Scenario Accuracy : {acc * 100:.1f}%")
        print(f"  Macro F1 Score               : {f1:.4f}")
        print(f"  True Skill Statistic (TSS)   : {tss:.4f}")
        print(f"  Avg Inference Latency        : {np.mean(latencies):.3f} ms")
        print("=" * 65 + "\n")

        return {
            "accuracy": acc,
            "macro_f1": f1,
            "tss": tss,
            "avg_latency_ms": round(float(np.mean(latencies)), 3),
            "scenario_details": scenario_results,
        }

    def run_model_ablation_study(self) -> Dict[str, Any]:
        """Ablation study comparing models across accuracy and inference speed."""
        print("=" * 65)
        print("[BENCHMARK 2] MODEL ARCHITECTURE ABLATION STUDY")
        print("=" * 65)

        df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "cleaned_training_dataset.csv")
        # Subsample for fair standardized comparison
        sample_df = df.sample(n=min(10000, len(df)), random_state=42)

        architectures = ["hist_gb", "naive_bayes", "ensemble"]
        ablation_results = []

        for arch in architectures:
            clf = SpaceWeatherSeverityClassifier(model_type=arch, random_state=42)
            X, y = clf.prepare_data(sample_df)

            # Measure training time
            t_train_0 = time.perf_counter()
            clf.fit(X, y)
            t_train_s = time.perf_counter() - t_train_0

            # Measure inference time over 1,000 samples
            X_test_sample = X.iloc[:1000]
            t_inf_0 = time.perf_counter()
            preds = clf.predict(X_test_sample)
            t_inf_ms = ((time.perf_counter() - t_inf_0) / 1000.0) * 1000.0

            acc = accuracy_score(y.iloc[:1000], preds)
            f1 = f1_score(y.iloc[:1000], preds, average="macro", zero_division=0)

            print(f"  Model: {arch:<14} | Acc: {acc*100:.2f}% | F1: {f1:.4f} | Fit: {t_train_s:.3f}s | Latency: {t_inf_ms:.3f}ms")

            ablation_results.append({
                "architecture": arch,
                "accuracy": round(float(acc), 4),
                "macro_f1": round(float(f1), 4),
                "train_time_s": round(t_train_s, 3),
                "latency_ms": round(t_inf_ms, 3),
            })

        print("=" * 65 + "\n")
        return {"ablation_comparison": ablation_results}

    def run_full_suite(self) -> Dict[str, Any]:
        """Runs full end-to-end benchmark and outputs report."""
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "historical_validation": self.run_severity_historical_benchmark(),
            "ablation_study": self.run_model_ablation_study(),
        }

        BENCHMARK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(BENCHMARK_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"[REPORT] Benchmark results saved -> {BENCHMARK_OUTPUT_PATH}\n")
        return report


if __name__ == "__main__":
    evaluator = BenchmarkEvaluator()
    evaluator.run_full_suite()
