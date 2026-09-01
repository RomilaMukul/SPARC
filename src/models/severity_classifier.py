import pandas as pd
import numpy as np
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, f1_score, confusion_matrix


class SpaceWeatherClassifier:
    def __init__(self):
        self.model = GaussianNB()

        # Real, independently-measured physical features only.
        # None of these are used to construct the label — that's the
        # whole point: the model has to genuinely learn the relationship.
        self.feature_columns = [
            "proton_flux_pfu",
            "proton_speed_kms",
            "mag_bz_field",
            "proton_density_cm3",
            "solar_wind_dyn_pressure_npa",
        ]

        # event_label is treated as the target because — unlike risk_score/
        # severity_label — it is (per the data description) an independently
        # recorded outcome, not a formula built from the feature columns.
        # IMPORTANT: verify this yourself before trusting it — see the
        # trace_label_origin() method below.
        self.target_column = "event_label"

    def trace_label_origin(self, df):
        """
        Sanity-check that the target isn't secretly derived from the
        feature columns. Run this BEFORE trusting any accuracy score.
        """
        print("=== Label leakage check ===")
        if df[self.target_column].nunique() <= 10:
            corr_report = {}
            for col in self.feature_columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    corr_report[col] = df[col].corr(
                        df[self.target_column].astype("category").cat.codes
                    )
            corr_series = pd.Series(corr_report).sort_values(key=abs, ascending=False)
            print(corr_series)
            suspicious = corr_series[abs(corr_series) > 0.95]
            if not suspicious.empty:
                print(f"\n⚠️  WARNING: near-perfect correlation with {list(suspicious.index)}. "
                      f"This may indicate the label is derived from that feature — verify the "
                      f"data source before trusting results.")
            else:
                print("\nNo suspiciously perfect correlations found. Looks like a genuine target.")
        print()

    def prepare_data(self, df):
        """Prepare the dataset for training — no label-derived features included."""
        df = df.copy()

        # Normalize magnetic field column name without faking missing data.
        if "mag_bz_field" not in df.columns:
            if "bz_field_nT" in df.columns:
                df["mag_bz_field"] = df["bz_field_nT"]
            else:
                raise ValueError(
                    "Missing magnetic field column: expected 'mag_bz_field' or 'bz_field_nT'."
                )

        missing = [c for c in self.feature_columns + [self.target_column] if c not in df.columns]
        if missing:
            raise ValueError(
                f"Missing required columns: {missing}. "
                f"This script expects real measured columns, not a synthetic risk_score label."
            )

        if df[self.feature_columns].isnull().any().any():
            raise ValueError("Feature columns contain missing values; clean the data first.")

        X = df[self.feature_columns]
        y = df[self.target_column]

        return X, y

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def evaluate(self, X_test, y_test):
        preds = self.predict(X_test)
        acc = accuracy_score(y_test, preds)
        macro_f1 = f1_score(y_test, preds, average="macro")

        print(f"Accuracy: {acc:.4f}")
        print(f"Macro F1: {macro_f1:.4f}")
        print(classification_report(y_test, preds, zero_division=0))

        print("Confusion matrix (rows = actual, cols = predicted):")
        labels = sorted(y_test.unique())
        cm = confusion_matrix(y_test, preds, labels=labels)
        print(pd.DataFrame(cm, index=labels, columns=labels))

        return acc, macro_f1


if __name__ == "__main__":
    df = pd.read_csv("data/processed/cleaned_training_dataset.csv")

    clf = SpaceWeatherClassifier()

    # Step 1: check whether event_label is trustworthy BEFORE training on it.
    clf.trace_label_origin(df)

    # Step 2: prepare data using only genuine physical features.
    X, y = clf.prepare_data(df)

    # Step 3: check class balance before splitting.
    print("Class balance:")
    print(y.value_counts())
    print()

    class_counts = y.value_counts()
    stratify_arg = y if class_counts.min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify_arg
    )

    clf.fit(X_train, y_train)
    clf.evaluate(X_test, y_test)