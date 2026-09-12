"""Rule-based clinical risk engine.

This is the v2 bridge to the v1 console project: it reuses
`meditrack.vitals` (BMI / BP / fever / risk-label rules) as the
*explainable baseline* the ML model is later benchmarked against.
"""

from meditrack import utils, vitals


def latest_vitals(patient):
    """Return the most recent vitals reading for a patient, or None."""
    history = patient.vitals_history
    return history[-1] if history else None


def patient_age(patient) -> int:
    return utils.calculate_age(patient.dob.isoformat())


def compute_risk(patient) -> dict:
    """Compute the rule-based risk summary for a patient ORM object."""
    v = latest_vitals(patient)
    bmi = vitals.calculate_bmi(patient.weight_kg or 0.0, patient.height_cm or 0.0)

    score = 0

    # BMI contribution (same weights as v1)
    if bmi >= 30:
        score += 30
    elif bmi >= 25:
        score += 15

    if v is not None:
        bp = vitals.bp_category(v.systolic, v.diastolic)
        fever = vitals.has_fever(v.temperature_c)
    else:
        bp = "No readings"
        fever = False

    # Blood-pressure contribution
    if bp == "Hypertension Stage 2":
        score += 35
    elif bp == "Hypertension Stage 1":
        score += 20
    elif bp == "Elevated":
        score += 10

    # Heart-rate contribution
    if v is not None and (v.heart_rate > 100 or v.heart_rate < 50):
        score += 15

    # Fever contribution
    if fever:
        score += 10

    score = min(score, 100)

    return {
        "bmi": bmi,
        "bmi_category": vitals.bmi_category(bmi),
        "bp_category": bp,
        "has_fever": fever,
        "risk_score": score,
        "risk_label": vitals.risk_label(score),
    }


def risk_features(patient) -> dict:
    """Extract the ML feature vector for a patient (same schema as training)."""
    v = latest_vitals(patient)
    age = patient_age(patient)
    return {
        "age": age,
        "bmi": vitals.calculate_bmi(patient.weight_kg or 0.0, patient.height_cm or 0.0),
        "systolic": v.systolic if v else 0,
        "diastolic": v.diastolic if v else 0,
        "heart_rate": v.heart_rate if v else 0,
        "temperature_c": v.temperature_c if v else 0.0,
        "n_allergies": len([a for a in (patient.allergies or "").split(",") if a]),
        "n_visits": len(patient.visits),
    }