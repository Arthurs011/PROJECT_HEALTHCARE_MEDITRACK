"""Synthetic clinical dataset generator.

Produces realistic patient records whose *ground-truth risk label* is
computed by the v1 rule engine (`meditrack.vitals.risk_score`) with a small
amount of label noise, mimicking real-world irreducible uncertainty.

The ML model then learns to predict that risk label from raw vitals.
"""

import random
from dataclasses import dataclass

from meditrack import vitals, utils

random.seed(42)

FEATURES = [
    "age",
    "bmi",
    "systolic",
    "diastolic",
    "heart_rate",
    "temperature_c",
    "n_allergies",
    "n_visits",
]


@dataclass
class Record:
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    systolic: int
    diastolic: int
    heart_rate: int
    temperature_c: float
    n_allergies: int
    n_visits: int
    risk_label: int


def _roll_vitals(rng: random.Random, age: int, bmi: float, fever: bool) -> tuple:
    """Realistic vitals that correlate with age / BMI / fever."""
    systolic = int(round(110 + age * 0.35 + bmi * 0.9 + rng.gauss(0, 7)))
    diastolic = int(round(60 + age * 0.20 + bmi * 0.4 + rng.gauss(0, 5)))
    systolic = min(max(systolic, 95), 200)
    diastolic = min(max(diastolic, 55), 130)

    heart_rate = int(round(rng.gauss(76, 9)))
    if fever:
        heart_rate += rng.randint(8, 22)

    temperature = round(36.7 + rng.gauss(0, 0.25), 1)
    if fever:
        temperature = round(rng.uniform(38.1, 40.2), 1)

    return systolic, diastolic, heart_rate, temperature


def generate_patients(n: int = 3000) -> list[Record]:
    rng = random.Random(42)
    records = []
    for _ in range(n):
        age = rng.randint(18, 88)
        gender = rng.choice(["M", "F"])

        height_cm = round(rng.gauss(173 if gender == "M" else 160, 7.5), 1)
        weight_kg = round(max(40.0, rng.gauss(72, 13)), 1)
        bmi = round(weight_kg / (height_cm / 100) ** 2, 1)

        # ~7% fever patients, more common in younger ones
        fever = rng.random() < 0.07

        systolic, diastolic, heart_rate, temperature = _roll_vitals(
            rng, age, bmi, fever
        )

        n_allergies = rng.choices([0, 1, 2, 3, 4], weights=[45, 25, 15, 10, 5])[0]
        n_visits = max(0, int(rng.gauss(2.2, 1.4)))

        # Ground-truth label from the rule engine
        patient = {
            "vitals": {
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "systolic": systolic,
                "diastolic": diastolic,
                "heart_rate": heart_rate,
                "temperature_c": temperature,
            }
        }
        score = vitals.risk_score(patient)
        label = 1 if score >= 60 else 0
        if rng.random() < 0.02:  # 2% label noise
            label = 1 - label

        records.append(
            Record(
                age=age,
                gender=gender,
                height_cm=height_cm,
                weight_kg=weight_kg,
                systolic=systolic,
                diastolic=diastolic,
                heart_rate=heart_rate,
                temperature_c=temperature,
                n_allergies=n_allergies,
                n_visits=n_visits,
                risk_label=label,
            )
        )
    return records


if __name__ == "__main__":
    rs = generate_patients()
    labels = [r.risk_label for r in rs]
    print(f"generated {len(rs)} records")
    print(f"high-risk (label=1): {sum(labels)} ({sum(labels)/len(labels):.1%})")