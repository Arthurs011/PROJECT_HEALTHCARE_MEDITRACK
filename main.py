"""
main.py  -- MediTrack entry point (the program you actually run).

    python3 main.py            -> interactive menu
    python3 main.py --demo     -> runs an automated demo of every feature
"""

import sys


from meditrack import data, utils, vitals, patients, analytics, storage


# ------------------------------------------------------------------ #
#  Presentation helpers
# ------------------------------------------------------------------ #
def show_patient(p):
    """Pretty-print one patient record."""
    v = p["vitals"]
    bmi = vitals.calculate_bmi(v["weight_kg"], v["height_cm"])
    score = vitals.risk_score(p)
    allergies = ", ".join(sorted(p["allergies"])) or "None"

    print(utils.divider(p["name"]))
    print(f"  ID           : {p['id']}")
    print(f"  Age / Gender : {utils.calculate_age(p['dob'])} / {p['gender']}")
    print(f"  Blood group  : {p['blood_group']}")
    print(f"  Allergies    : {allergies}")
    print(f"  BMI          : {bmi} ({vitals.bmi_category(bmi)})")
    print(f"  Blood press. : {v['systolic']}/{v['diastolic']} "
          f"({vitals.bp_category(v['systolic'], v['diastolic'])})")
    print(f"  Risk score   : {score} ({vitals.risk_label(score)})")
    print(f"  Visits       : {len(p['visits'])}")
    for date, reason in p["visits"]:
        print(f"     - {date}: {reason}")


def show_all():
    print(utils.divider("All Patients"))
    # consume a GENERATOR line by line
    for line in analytics.risk_report_lines(data.PATIENTS):
        print(" ", line)


# ------------------------------------------------------------------ #
#  Automated demo -- exercises every module at once
# ------------------------------------------------------------------ #
def run_demo():
    print(utils.divider("MediTrack Demo"))

    show_all()

    # *args / **kwargs when adding a patient
    print("\n>> Adding a new patient (Meera Iyer) via *args/**kwargs ...")
    new_p = patients.add_patient(
        "  meera   iyer ", "1998-03-19", "f", "ab+",
        "aspirin", "latex",                       # *allergies
        height_cm=160, weight_kg=90, systolic=150, diastolic=95,  # **extra
    )
    show_patient(new_p)

    # add_visit with default date + *args reasons
    patients.add_visit(new_p["id"], None, "Follow-up", "BP check")

    # filter / lambda -> high-risk patients
    print("\n>> High-risk patients (filter + lambda):")
    for p in analytics.high_risk_patients(data.PATIENTS):
        print(f"   * {p['name']}")

    # map -> summaries
    print("\n>> Risk summaries (map):")
    for s in analytics.summarise(data.PATIENTS):
        print(f"   {s['name']:<14} -> {s['risk']} ({s['label']})")

    # reduce -> average age
    avg = analytics.average_age(data.PATIENTS, utils.calculate_age)
    print(f"\n>> Average patient age (reduce): {avg}")

    # iterator (iter/next)
    fh = analytics.first_high_risk(data.PATIENTS)
    print(f">> First high-risk patient (iter/next): "
          f"{fh['name'] if fh else 'None'}")

    # set union of all allergies
    print(f">> All allergies on file (set union): "
          f"{', '.join(sorted(patients.all_allergies()))}")

    # recursion over the department tree
    print(f"\n>> Hospital has {analytics.count_departments(data.HOSPITAL)} "
          f"departments (recursion):")
    for line in analytics.list_departments(data.HOSPITAL):
        print("   " + line)

    # generator + datetime -> appointment slots
    print("\n>> Next appointment slots (generator + datetime):")
    for slot in utils.next_appointment_slots(count=4):
        print(f"   {slot}")

    # FILE HANDLING -- save, log a visit, then read both back.
    print("\n>> Saving patients to file (write mode 'w'):")
    n = storage.save_patients(data.PATIENTS)
    print(f"   wrote {n} records to {storage.PATIENTS_FILE}")

    print(">> Logging a visit to file (append mode 'a'):")
    storage.log_visit(new_p["id"], new_p["name"], "Demo visit")
    for entry in storage.read_visit_log():         # iterate the file
        print(f"   {entry}")

    print(">> Reloading patients from file (read mode 'r'):")
    reloaded = storage.load_patients()
    print(f"   read back {len(reloaded)} records "
          f"(first: {reloaded[0]['name'] if reloaded else 'none'})")

    print(">> File preview via readline()/tell()/seek():")
    lines, pos = storage.preview_file(storage.PATIENTS_FILE, n_lines=2)
    for ln in lines:
        print(f"   {ln}")
    print(f"   cursor was at byte {pos} after 2 lines")

    print("\n" + utils.divider("Demo complete"))


# ------------------------------------------------------------------ #
#  Interactive menu
# ------------------------------------------------------------------ #
MENU = """
Choose an option:
  1) List all patients
  2) View a patient by ID
  3) Search patients by name
  4) Add a new patient
  5) Add a visit
  6) High-risk report
  7) Hospital departments
  8) Run full demo
  9) Save patients to file
 10) Load patients from file
 11) View visit log
  0) Exit
> """


def ask_number(prompt, default, as_int=False):
    """Read a number from the user

    - Blank input  -> return the default (parameter with a default value).
    - Bad input    -> print a message and ask again (loop + try/except).
    """
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return default
        try:
            return int(raw) if as_int else float(raw)
        except ValueError:
            print("    Please enter a number (or press Enter to skip).")


def menu_loop():
    while True:
        choice = input(MENU).strip()

        if choice == "0":
            print("Goodbye!")
            break
        elif choice == "1":
            show_all()
        elif choice == "2":
            pid = input("Enter patient ID: ").strip()
            p = patients.find_by_id(pid)
            show_patient(p) if p else print("Not found.")
        elif choice == "3":
            kw = input("Name contains: ").strip()
            results = patients.search_by_name(kw)
            print(f"{len(results)} match(es).")
            for p in results:
                print(f"   {p['id']}  {p['name']}")
        elif choice == "4":
            name = input("Name: ")
            dob = input("DOB (YYYY-MM-DD): ")
            gender = input("Gender (M/F): ")
            bg = input("Blood group: ")
            # Collect vitals (blank = use the default, so BMI/risk can compute)
            print("  -- Vitals (press Enter to skip a field) --")
            vitals_in = {
                "height_cm": ask_number("  Height (cm): ", 0.0),
                "weight_kg": ask_number("  Weight (kg): ", 0.0),
                "systolic": ask_number("  Systolic BP: ", 120, as_int=True),
                "diastolic": ask_number("  Diastolic BP: ", 80, as_int=True),
                "heart_rate": ask_number("  Heart rate: ", 72, as_int=True),
                "temperature_c": ask_number("  Temperature (C): ", 36.6),
            }
            try:
                # **vitals_in unpacks the dict into keyword args
                p = patients.add_patient(name, dob, gender, bg, **vitals_in)
                print(f"Added {p['name']} with ID {p['id']}")
            except ValueError as e:
                print(f"Error: {e}")
        elif choice == "5":
            pid = input("Patient ID: ").strip()
            reason = input("Reason: ").strip()
            ok = patients.add_visit(pid, None, reason)
            if ok:
                p = patients.find_by_id(pid)
                storage.log_visit(pid, p["name"], reason)
                print("Visit added (and logged to file).")
            else:
                print("Patient not found.")
        elif choice == "6":
            print(utils.divider("High-risk"))
            for p in analytics.high_risk_patients(data.PATIENTS):
                s = vitals.risk_score(p)
                print(f"   {p['name']:<16} {s} ({vitals.risk_label(s)})")
        elif choice == "7":
            print(f"Total departments: "
                  f"{analytics.count_departments(data.HOSPITAL)}")
            for line in analytics.list_departments(data.HOSPITAL):
                print("   " + line)
        elif choice == "8":
            run_demo()
        elif choice == "9":
            count = storage.save_patients(data.PATIENTS)
            print(f"Saved {count} patients to {storage.PATIENTS_FILE}")
        elif choice == "10":
            loaded = storage.load_patients()
            if loaded:
                data.PATIENTS[:] = loaded          # replace list in place
                print(f"Loaded {len(loaded)} patients from file.")
            else:
                print("No saved patient file found yet (save first).")
        elif choice == "11":
            print(utils.divider("Visit Log"))
            log = storage.read_visit_log()
            if not log:
                print("   (no visits logged yet)")
            for entry in log:
                print("   " + entry)
        else:
            print("Invalid choice, try again.")


# the standard program entry-point guard
if __name__ == "__main__":
    # read command-line arguments from sys.argv
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_demo()
        sys.exit(0)
    menu_loop()