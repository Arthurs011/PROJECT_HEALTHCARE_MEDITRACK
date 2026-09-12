"""Train & evaluate risk-prediction models and persist artifacts.

Two classifiers are compared:
  - Logistic Regression (linear, interpretable baseline)
  - Random Forest        (non-linear, usually stronger)

The better model (by holdout ROC-AUC) is saved to `ml/artifacts/` along
with the fitted scaler, feature names and evaluation metrics.
"""

import json
import os
import pickle

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance

from backend.config import settings
from ml.generate_data import FEATURES, generate_patients

RANDOM_STATE = 42
TEST_SIZE = 0.25


def build_dataframe(n: int = 3000) -> pd.DataFrame:
    records = generate_patients(n)
    rows = [
        {
            "age": r.age,
            "bmi": r.weight_kg / (r.height_cm / 100) ** 2,
            "systolic": r.systolic,
            "diastolic": r.diastolic,
            "heart_rate": r.heart_rate,
            "temperature_c": r.temperature_c,
            "n_allergies": r.n_allergies,
            "n_visits": r.n_visits,
            "label": r.risk_label,
        }
        for r in records
    ]
    df = pd.DataFrame(rows)
    df["bmi"] = df["bmi"].round(1)
    return df


def evaluate(y_true, y_pred, y_proba) -> dict:
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary"
    )
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_proba)), 4),
    }


def main(n: int = 3000) -> None:
    df = build_dataframe(n)
    X = df[FEATURES]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    models = {
        "logistic_regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", RandomForestClassifier(
                    n_estimators=200, max_depth=10, random_state=RANDOM_STATE
                )),
            ]
        ),
    }

    results = {}
    best_name, best_score = None, -1.0
    for name, pipeline in models.items():
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1]
        results[name] = evaluate(y_test, y_pred, y_proba)
        print(f"\n===== {name} =====")
        print(classification_report(y_test, y_pred, digits=4))
        print(results[name])
        if results[name]["roc_auc"] > best_score:
            best_score, best_name = results[name]["roc_auc"], name

    best = models[best_name]
    print(f"\n>> Best model by ROC-AUC: {best_name} ({best_score:.4f})")

    # Feature importance for the chosen model (permutation, more honest)
    X_test_np = X_test.to_numpy()
    imp = permutation_importance(
        best, X_test_np, y_test, n_repeats=10, random_state=RANDOM_STATE
    )
    importance = {
        feat: round(float(imp.importances_mean[i]), 5)
        for i, feat in enumerate(FEATURES)
    }
    print("\nPermutation feature importance:")
    for feat, val in sorted(importance.items(), key=lambda kv: -kv[1]):
        print(f"   {feat:<15} {val}")

    os.makedirs(settings.model_artifact_dir, exist_ok=True)
    artifact = os.path.join(settings.model_artifact_dir, "risk_model.pkl")
    with open(artifact, "wb") as f:
        pickle.dump(
            {
                "model": best,
                "model_name": best_name,
                "features": FEATURES,
                "metrics": results,
                "best_metrics": results[best_name],
                "feature_importance": importance,
            },
            f,
        )

    metrics_path = os.path.join(settings.model_artifact_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(
            {
                "best_model": best_name,
                "metrics": results,
                "feature_importance": importance,
            },
            f,
            indent=2,
        )

    print(f"\nSaved model + metrics to {settings.model_artifact_dir}")


if __name__ == "__main__":
    main()