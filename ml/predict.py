"""Load the trained model and expose a prediction helper for the API."""

import os
import pickle

from backend.config import settings

_MODEL = None


def _load():
    global _MODEL
    if _MODEL is None:
        artifact = os.path.join(settings.model_artifact_dir, "risk_model.pkl")
        with open(artifact, "rb") as f:
            _MODEL = pickle.load(f)
    return _MODEL


def available() -> bool:
    artifact = os.path.join(settings.model_artifact_dir, "risk_model.pkl")
    return os.path.exists(artifact)


def predict(features: dict) -> tuple[float, str]:
    """Return (probability_of_high_risk, label) for a feature dict."""
    bundle = _load()
    pipeline = bundle["model"]
    row = [[features.get(f, 0) for f in bundle["features"]]]
    proba = float(pipeline.predict_proba(row)[0, 1])
    pred = int(pipeline.predict(row)[0])
    label = "HIGH" if (pred == 1 or proba >= 0.5) else "LOW"
    return proba, label