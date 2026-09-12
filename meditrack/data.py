PATIENTS = [
    {
        "id": "PAT-1001-4821",
        "name": "Aarav Sharma",
        "dob": "1990-05-14",
        "gender": "M",
        "blood_group": "O+",
        "allergies": {"penicillin", "dust"},          # set
        "vitals": {                                    # nested dict
            "height_cm": 175.0,
            "weight_kg": 82.0,
            "systolic": 128,
            "diastolic": 84,
            "heart_rate": 78,
            "temperature_c": 37.0,
        },
        "visits": [                                    # list of tuples
            ("2026-06-10", "Routine checkup"),
            ("2026-07-02", "Fever"),
        ],
    },
    {
        "id": "PAT-1002-7734",
        "name": "Diya Patel",
        "dob": "1985-11-22",
        "gender": "F",
        "blood_group": "A+",
        "allergies": set(),                            # empty set
        "vitals": {
            "height_cm": 162.0,
            "weight_kg": 55.0,
            "systolic": 118,
            "diastolic": 76,
            "heart_rate": 70,
            "temperature_c": 36.6,
        },
        "visits": [("2026-07-15", "Migraine")],
    },
    {
        "id": "PAT-1003-9012",
        "name": "Kabir Nair",
        "dob": "1972-02-08",
        "gender": "M",
        "blood_group": "B-",
        "allergies": {"sulfa"},
        "vitals": {
            "height_cm": 168.0,
            "weight_kg": 95.0,
            "systolic": 148,
            "diastolic": 96,
            "heart_rate": 88,
            "temperature_c": 37.4,
        },
        "visits": [
            ("2026-05-30", "High BP follow-up"),
            ("2026-06-28", "Chest discomfort"),
            ("2026-07-20", "Medication review"),
        ],
    },
]

# In `data.py`, add a **nested** `HOSPITAL` dict: a name plus a
#   `departments` list, where each department can have its own `sub` list of
#   departments

HOSPITAL = {
    "name": "MediTrack General Hospital",
    "departments": [
        {
            "name": "Internal Medicine",
            "sub": [
                {"name": "Cardiology", "sub": []},
                {"name": "Endocrinology", "sub": []},
            ],
        },
        {
            "name": "Surgery",
            "sub": [
                {"name": "Orthopedics", "sub": []},
                {
                    "name": "Neurosurgery",
                    "sub": [{"name": "Spine Unit", "sub": []}],
                },
            ],
        },
        {"name": "Pediatrics", "sub": []},
    ],
}