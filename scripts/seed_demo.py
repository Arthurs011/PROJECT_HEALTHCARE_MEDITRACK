"""Seed the database with realistic demo patients via the public API.

Usage:
    uv run python -m scripts.seed_demo

Ideal right after `uv run python -m ml.train` and before opening the
dashboard for a demo.
"""

import httpx

BASE = "http://127.0.0.1:8000"


DEMO = [
    # name, dob, gender, blood, allergies, height, weight, [(vitals), ...], [(visit, note)]
    ("Aarav Sharma", "1990-05-14", "M", "O+", ["penicillin", "dust"],
     175, 82, [(128, 84, 78, 37.0), (132, 86, 80, 36.9)], [("Routine checkup", "")]),
    ("Diya Patel", "1985-11-22", "F", "A+", [],
     162, 55, [(118, 76, 70, 36.6)], [("Migraine", "prescribed paracetamol")]),
    ("Kabir Nair", "1972-02-08", "M", "B-", ["sulfa"],
     168, 95, [(148, 96, 88, 37.4), (150, 95, 90, 37.0)], [("High BP follow-up", ""), ("Chest discomfort", "ECG ordered")]),
    ("Ravi Kumar", "1980-03-15", "M", "B+", ["aspirin"],
     170, 95, [(155, 98, 102, 38.5), (140, 90, 80, 37.0)], [("Chest pain", "ECG recommended")]),
    ("Sana Kazi", "1999-08-21", "F", "AB+", ["latex"],
     158, 47, [(112, 72, 65, 36.5)], [("Allergy consult", "")]),
    ("Meera Iyer", "1998-03-19", "F", "AB-", ["aspirin", "latex"],
     160, 90, [(150, 95, 92, 36.8)], [("Obesity review", "diet plan shared")]),
]


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=10) as c:
        r = c.post("/auth/login", data={"username": "admin", "password": "admin123"})
        r.raise_for_status()
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        existing = c.get("/patients", headers=h).json()
        existing_names = {p["name"] for p in existing}

        for name, dob, gender, bg, allergies, height, weight, vitals, visits in DEMO:
            if name in existing_names:
                print(f"  skip  {name} (already present)")
                continue
            r = c.post("/patients", headers=h, json={
                "name": name, "dob": dob, "gender": gender, "blood_group": bg,
                "allergies": allergies, "height_cm": height, "weight_kg": weight,
            })
            r.raise_for_status()
            pid = r.json()["patient_id"]

            for s, d, hr, t in vitals:
                c.post(f"/patients/{pid}/vitals", headers=h,
                       json={"systolic": s, "diastolic": d, "heart_rate": hr,
                             "temperature_c": t}).raise_for_status()
            for reason, notes in visits:
                c.post(f"/patients/{pid}/visits", headers=h,
                       json={"reason": reason, "notes": notes}).raise_for_status()
            print(f"  added {name} ({pid})")

    print("\nSeeding complete.")


if __name__ == "__main__":
    main()