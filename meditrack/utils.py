# **Task:** Start a new file `meditrack/utils.py`. At the top, create a
#   constant `VALID_BLOOD_GROUPS` as a **frozenset** of the 8 blood groups
#   (`A+ A- B+ B- AB+ AB- O+ O-`).

import os
import random
import sys
from datetime import datetime, timedelta

VALID_BLOOD_GROUPS = frozenset(
    {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
)

# ==========================================================================================================================================

# **Task:** In `utils.py`, write a function `clen_name(raw_name)` that:
#   - removes leading/trailing spaces
#   - collapses multiple spaces between words into one
#   - capitalises each word (Title Case)
#   - returns the cleaned string


# `clean_name("   john   DOE ")` must return `"John Doe"`.

def clean_name(raw_name):
    return ' '.join(raw_name.strip().split()).title()


# ==========================================================================================================================================



# **Task:** In `utils.py`, write `is_valid_blood_group(bg)` that returns
#   `True`/`False` depending on whether `bg` (after `.strip().upper()`) is in
#   `VALID_BLOOD_GROUPS`.



def is_valid_blood_group(bg):
    return bg.strip().upper() in VALID_BLOOD_GROUPS


# ==========================================================================================================================================

# **Task:** In `utils.py`:
#   - `import random` at the top.
#   - Create a module-level variable `_id_counter = 1000`.
#   - Write `generate_patient_id()` that uses `global _id_counter`, increments it
#     by 1, adds a random 4-digit suffix, and returns a string like
#     `"PAT-1001-8842"`.

_id_counter = 1000
def generate_patient_id():
    global _id_counter
    _id_counter += 1
    random_suffix = random.randint(1000, 9999)
    return f"PAT-{_id_counter}-{random_suffix}"

# ==========================================================================================================================================

# **Task:** In `utils.py`, add `from datetime import datetime, timedelta`, then write:
#   - `today_str()` → returns today's date as `"YYYY-MM-DD"`.
#   - `calculate_age(dob_str)` → returns a person's age in whole years from their DOB.

def today_str():
    return datetime.now().strftime('%Y-%m-%d')

def calculate_age(dob_str):
    dob = datetime.strptime(dob_str, '%Y-%m-%d')
    today = datetime.now()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age

# ==========================================================================================================================================

# In `utils.py`, write a generator
#   `next_appointment_slots(start_hour=9, count=4, gap_minutes=30)` that `yield`s
#   formatted time strings (e.g. `"09:00 AM"`, `"09:30 AM"`, ...).

# Use `timedelta(minutes=gap_minutes * i)` inside a loop and
#   `strftime("%I:%M %p")`.


def next_appointment_slots(start_hour=9, count=4, gap_minutes=30):
    """GENERATOR of appointment time strings.

    Uses default parameters. Yields values lazily with `yield`"""
    base = datetime.now().replace(hour=start_hour, minute=0,
                                  second=0, microsecond=0)
    for i in range(count):
        slot = base + timedelta(minutes=gap_minutes * i)
        yield slot.strftime("%I:%M %p")

def clear_screen():
    if sys.platform.startswith("win"):
        os.system("cls")
    else:
        os.system("clear")

def divider(title=""):
    line = "=" * 52          
    if title:
        return f"{line}\n  {title.upper()}\n{line}"
    return line
