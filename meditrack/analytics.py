from . import vitals
from functools import reduce

def high_risk_patients(patients, threshold=60):
    """Keep only patients whose risk score >= threshold.

    `filter(func, iterable)` keeps items where func(item) is True.
    Here func is a lambda (an anonymous one-line function).
    """
    return list(filter(lambda p:vitals.risk_score(p) >= threshold, patients))

def summarise(patients):
    """Transform each patient dict into a short summary dict.

    `map(func, iterable)` applies func to every element.
    """
    return list (map(lambda p:{
        'id':p['id'],
        'name':p['name'],
        'risk':vitals.risk_score(p),
        'label':vitals.risk_label(vitals.risk_score(p))
    }, patients))

def average_age(patients, calculate_age):
    """Average patient age using reduce to sum the ages.
    """
    if not patients:
        return 0
    ages = list(map(lambda p:calculate_age(p['dob']), patients))
    total = reduce(lambda a, b : a + b, ages)
    return round(total/(len(ages)), 1)

def patient_stream(patients):
    """Yield patients one at a time instead of building a big list.
    """
    for patient in patients:
        yield patient

def risk_report_lines(patients):
    """Generator that yields a formatted line per patient"""
    for patient in patient_stream(patients):
        score = vitals.risk_score(patient)
        label = vitals.risk_label(score)
        yield f"{patient['id']} | {patient['name']} | Risk {score} ({label})"

def first_high_risk(patients):
    """Use the iterator protocol directly (iter + next) to grab the first
    high-risk patient without scanning the whole list."""
    it = iter(patients)
    while True:
        try:
            patient = next(it)
        except StopIteration:
            return None
        if vitals.risk_score(patient) >= 60:
            return patient


# ==========================================================================================================================================

# In `analytics.py`, write:
#   - `count_departments(node)` → recursively counts every department.
#   - `list_departments(node)` → recursively returns an **indented** list of names.

# Loop over the children and call the same function on each child.

def count_departments(node):
    """Recursively count every department in the hospital tree.

    We count each *child* department (not the hospital root itself).
    Base case  : a node with no children adds nothing further.
    Recursive  : each child is 1 + however many it contains.
    """
    children = node.get('sub', node.get('departments', []))
    total = 0
    for child in children:
        total += 1 + count_departments(child)     # function calls itself
    return total

def list_departments(node, depth=0, acc=None):
    """Recursively collect an indented department listing"""
    if acc is None:
        acc = []
    name = node.get("name", "")
    if name and depth > 0:
        acc.append(("  " * (depth - 1)) + "- " + name)
    for child in node.get("sub", node.get("departments", [])):
        list_departments(child, depth + 1, acc)
    return acc
