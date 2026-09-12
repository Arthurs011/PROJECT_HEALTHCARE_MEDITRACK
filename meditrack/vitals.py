# **Task:** Create `meditrack/vitals.py`. Write `calculate_bmi(weight_kg, height_cm)`:
#   - convert height cm → metres
#   - compute `weight / (height_m ** 2)`
#   - return it rounded to 1 decimal place

def calculate_bmi(weight_kg, height_cm):
    if height_cm <= 0 or weight_kg <= 0:
        return 0.0
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 1)

# =====================================================================================================================================

# In `vitals.py`, add:
#   - `bmi_category(bmi)` → `"Underweight" / "Normal" / "Overweight" / "Obese"`.
#   - `bp_category(systolic, diastolic)` → returns a BP stage string.
#   - `has_fever(temperature_c)` → returns a **bool** (`True` if temp ≥ 38.0).


# bmi_category
# bmi <= -> N/A
# bmi < 18.5 -> Underweight
# bmi < 25 -> Normal
# bmi < 30 -> Overweight
# else Obese

# bp_category
# systolic <120 and diastolic <80 -> Normal
# systolic <130 and diastolic <80 -> Elevated
# systolic <140 and diastolic <90 -> Hypertesion Stage 1
# otherwise -> Hypertesion Stage 2

def bmi_category(bmi):
    if bmi <= 0:
        return "N/A"
    elif bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"
    
def bp_category(systolic, diastolic):
    if systolic < 120 and diastolic < 80:
        return "Normal"
    elif systolic < 130 and diastolic < 80:
        return "Elevated"
    elif systolic < 140 or diastolic < 90:
        return "Hypertension Stage 1"
    else:
        return "Hypertension Stage 2"

def has_fever(temperature_c):
    return temperature_c >= 38.0


# =====================================================================================================================================


# In `vitals.py`, write `risk_score(patient)`:
#   - start `score = 0`
#   - add points for high BMI, high BP stage, abnormal heart rate, and fever
#   - cap the final score at 100 and return it

        # BMI Contribution
        # if bmi >= 30 -> score += 30
        # if bmi >= 25 -> score += 15

        # BP Contribution
        # if stage = Hypertesion Stage 2 -> score += 35
        # if stage = Hypertesion Stage 1 -> score += 20
        # if stage = Elevated -> score += 10

        # Heart Rate Contribution
        # Heart-rate > 100 or Heart-rate < 50 -> score += 15

        # Fever Contribution
        # if patient has fever then  score += 10

        # the value we are areturning from this function is score and should not pass 100

        # return min(score, 100)

        # Also write `risk_label(score)` → `"HIGH"` (≥60), `"MODERATE"` (≥30), else `"LOW"`.

        # print(calculate_bmi(90, 175))

def risk_score(patient):
    v = patient.get('vitals', {})
    bmi = calculate_bmi(v.get('weight_kg', 0), v.get('height_cm', 0))

    score = 0

    # BMI Contribution
    if bmi >= 30:
        score += 30
    elif bmi >= 25:
        score += 15

    # Blood-pressure contribution
    stage = bp_category(v["systolic"], v["diastolic"])
    if stage == "Hypertension Stage 2":
        score += 35
    elif stage == "Hypertension Stage 1":
        score += 20
    elif stage == "Elevated":
        score += 10

    # Heart-rate contribution
    if v["heart_rate"] > 100 or v["heart_rate"] < 50:
        score += 15

    # Fever contribution
    if has_fever(v["temperature_c"]):
        score += 10   

    return min((score, 100))
            
# write `risk_label(score)` → `"HIGH"` (≥60), `"MODERATE"` (≥30), else `"LOW"`.

def risk_label(score):
    if score >= 60:
        return "HIGH"
    elif score >= 30:
        return "MODERATE"
    else:
        return "LOW"

# ==========================================================================================================================================


# if __name__ == '__main__':
#     patient = {
#             "id": "PAT-1001-4821",
#             "name": "Aarav Sharma",
#             "dob": "1990-05-14",
#             "gender": "M",
#             "blood_group": "O+",
#             "allergies": {"penicillin", "dust"},          # set
#             "vitals": {                                    # nested dict
#                 "height_cm": 175.0,
#                 "weight_kg": 82.0,
#                 "systolic": 128,
#                 "diastolic": 84,
#                 "heart_rate": 78,
#                 "temperature_c": 37.0,
#             },
#             "visits": [                                    # list of tuples
#                 ("2026-06-10", "Routine checkup"),
#                 ("2026-07-02", "Fever"),
#             ],
#         }


#     print(risk_score(patient))