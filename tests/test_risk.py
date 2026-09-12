"""Unit tests for the rule-based risk engine and helpers."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from backend.risk import compute_risk, patient_age, risk_features
from meditrack import vitals


def make_patient(vitals_history=None, height=175.0, weight=82.0, dob="1990-05-14",
                 allergies="penicillin,dust", visits=None):
    return SimpleNamespace(
        dob=datetime.strptime(dob, "%Y-%m-%d").date(),
        height_cm=height,
        weight_kg=weight,
        allergies=allergies,
        visits=visits or [],
        vitals_history=vitals_history or [],
    )


def make_reading(systolic=128, diastolic=84, heart_rate=78, temp=37.0):
    return SimpleNamespace(
        systolic=systolic, diastolic=diastolic,
        heart_rate=heart_rate, temperature_c=temp,
    )


def test_bmi_rules_reused_from_v1():
    # BMI 82 / (1.75^2) = 26.8 -> Normal range overlap: Overweight
    assert vitals.calculate_bmi(82, 175) == 26.8
    assert vitals.bmi_category(26.8) == "Overweight"
    assert vitals.bp_category(118, 76) == "Normal"


def test_low_risk_patient():
    p = make_patient([make_reading(118, 76, 70, 36.6)], weight=70, height=175)
    r = compute_risk(p)
    assert r["risk_score"] == 0
    assert r["risk_label"] == "LOW"


def test_high_risk_patient():
    p = make_patient(
        [make_reading(systolic=155, diastolic=98, heart_rate=105, temp=38.6)],
        weight=95, height=168,
    )
    r = compute_risk(p)
    # BMI 33.7 -> +30, BP stage2 -> +35, HR -> +15, fever -> +10 = 90
    assert r["risk_score"] == 90
    assert r["risk_label"] == "HIGH"
    assert r["has_fever"] is True


def test_risk_capped_at_100():
    p = make_patient([make_reading(200, 130, 130, 40.0)], weight=130, height=160)
    r = compute_risk(p)
    assert r["risk_score"] <= 100


def test_no_readings_no_penalty():
    """Missing vitals must not add BP/HR/fever points."""
    p = make_patient([], height=175, weight=60)  # BMI 19.6 clean
    r = compute_risk(p)
    assert r["risk_score"] == 0


def test_patient_age():
    p = make_patient(dob="2000-06-15")
    assert patient_age(p) >= 0


def test_risk_features_shape():
    p = make_patient([make_reading()], visits=[1, 2], allergies="penicillin,dust")
    f = risk_features(p)
    for key in ["age", "bmi", "systolic", "diastolic", "heart_rate",
                "temperature_c", "n_allergies", "n_visits"]:
        assert key in f
    assert f["n_allergies"] == 2
    assert f["n_visits"] == 2