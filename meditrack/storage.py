"""
storage.py  -- Saving & loading data to files.

Concepts practiced here:
- open() + the `with` context manager (auto-closes the file)
- text modes  : 'w' (write/overwrite), 'a' (append), 'r' (read)
- methods     : write(), writelines(), read(), readline(), readlines()
- cursor      : tell() and seek()
- iterating a file line by line
- handling FileNotFoundError when a file does not exist yet
- os module to build safe file paths / make folders
"""

import os

# ---- Build file paths relative to the PROJECT folder  ----
# __file__ = .../meditrack/storage.py -> go up one level to the project root.
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_PROJECT_DIR, "data")
PATIENTS_FILE = os.path.join(DATA_DIR, "patients.txt")
VISIT_LOG_FILE = os.path.join(DATA_DIR, "patient_visits.txt")

# The order of columns we write into the patients file.
_HEADER = ("id|name|dob|gender|blood_group|allergies|"
           "height_cm|weight_kg|systolic|diastolic|heart_rate|temperature_c")


def _ensure_data_dir():
    """Create the data/ folder if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


# ------------------------------------------------------------------ #
#  SAVE  -- write mode 'w' + writelines()
# ------------------------------------------------------------------ #
def save_patients(patients, path=PATIENTS_FILE):
    """Write every patient to a text file, one record per line.

    Mode 'w' CREATES the file (or ERASES its old contents first), then we
    write fresh data. Each field is separated by '|', allergies by ','.
    """
    _ensure_data_dir()
    lines = [_HEADER + "\n"]                      # first line = column header
    for p in patients:
        v = p["vitals"]
        allergy_csv = ",".join(sorted(p["allergies"]))   # set -> 'a,b,c'
        # Build one delimited line for this patient.
        line = "|".join([
            p["id"], p["name"], p["dob"], p["gender"], p["blood_group"],
            allergy_csv,
            str(v["height_cm"]), str(v["weight_kg"]),
            str(v["systolic"]), str(v["diastolic"]),
            str(v["heart_rate"]), str(v["temperature_c"]),
        ]) + "\n"
        lines.append(line)

    # `with` auto-closes the file even if an error happens inside the block.
    with open(path, "w") as f:                    # 'w' = write/overwrite
        f.writelines(lines)                       # write a list of lines
    return len(patients)                          # how many we saved


# ------------------------------------------------------------------ #
#  LOAD  -- read mode 'r' + readlines() + FileNotFoundError handling
# ------------------------------------------------------------------ #
def load_patients(path=PATIENTS_FILE):
    """Read patients back from the text file into a list of dicts.

    If the file has never been created, we catch FileNotFoundError and
    simply return an empty list instead of crashing.
    """
    patients = []
    try:
        with open(path, "r") as f:                # 'r' = read only
            lines = f.readlines()                 # list, one string per line
    except FileNotFoundError:
        return patients                           # nothing saved yet

    for line in lines[1:]:                        # skip the header row
        line = line.strip()                       # drop the trailing newline
        if not line:
            continue                              # skip blank lines
        parts = line.split("|")                   # reverse of our join
        if len(parts) != 12:
            continue                              # skip malformed lines
        (pid, name, dob, gender, bg, allergy_csv,
         height, weight, sys_bp, dia_bp, hr, temp) = parts

        # Rebuild the nested structures we flattened when saving.
        allergies = {a for a in allergy_csv.split(",") if a}   # set
        patient = {
            "id": pid, "name": name, "dob": dob,
            "gender": gender, "blood_group": bg,
            "allergies": allergies,
            "vitals": {
                "height_cm": float(height), "weight_kg": float(weight),
                "systolic": int(sys_bp), "diastolic": int(dia_bp),
                "heart_rate": int(hr), "temperature_c": float(temp),
            },
            "visits": [],   # visits live in the separate visit-log file
        }
        patients.append(patient)
    return patients


# ------------------------------------------------------------------ #
#  VISIT LOG  -- append mode 'a'
# ------------------------------------------------------------------ #
def log_visit(patient_id, name, symptom, path=VISIT_LOG_FILE):
    """Append ONE visit line to the log file.

    Mode 'a' keeps existing content and adds to the END of the file,
    so previous visits are never lost.
    """
    _ensure_data_dir()
    with open(path, "a") as f:                    # 'a' = append
        f.write(f"{patient_id}, {name}, {symptom}\n")


def read_visit_log(path=VISIT_LOG_FILE):
    """Return every visit line as a list (iterate the file line by line)."""
    log = []
    try:
        with open(path, "r") as f:
            for line in f:                        # a file is iterable!
                line = line.strip()
                if line:
                    log.append(line)
    except FileNotFoundError:
        return log
    return log


# ------------------------------------------------------------------ #
#  PREVIEW  -- demonstrates readline() + tell()/seek() cursor control
# ------------------------------------------------------------------ #
def preview_file(path, n_lines=3):
    """Return the first `n_lines` of a file using readline(), and report the
    cursor position with tell(). Shows seek() by rewinding to the start."""
    preview = []
    try:
        with open(path, "r") as f:
            for _ in range(n_lines):
                line = f.readline()               # read ONE line at a time
                if not line:                      # end of file reached
                    break
                preview.append(line.strip())
            position = f.tell()                   # where is the cursor now?
            f.seek(0)                             # rewind to the beginning
    except FileNotFoundError:
        return [], 0
    return preview, position