"""End-to-end API tests using an isolated in-memory DB and no ML artifacts."""

from tests.conftest import auth


def test_login_and_me(client, admin_token):
    me = client.get("/auth/me", headers=auth(admin_token))
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert me.json()["role"] == "admin"


def test_login_wrong_password(client):
    res = client.post("/auth/login", data={"username": "admin", "password": "nope"})
    assert res.status_code == 401


def test_patients_require_auth(client):
    assert client.get("/patients").status_code == 401


def test_doctor_forbidden_on_admin_endpoints(client, doctor_token):
    res = client.get("/reports/departments", headers=auth(doctor_token))
    assert res.status_code == 403


def test_patient_crud_and_risk_flow(client, admin_token):
    h = auth(admin_token)

    # create
    r = client.post("/patients", headers=h, json={
        "name": "  priya   menon ", "dob": "1992-07-01", "gender": "F",
        "blood_group": "a+", "allergies": ["dust"],
        "height_cm": 165, "weight_kg": 80,
    })
    assert r.status_code == 201
    p = r.json()
    assert p["name"] == "Priya Menon"          # cleaned + title-cased
    assert p["blood_group"] == "A+"
    pid = p["patient_id"]

    # list
    names = [x["name"] for x in client.get("/patients", headers=h).json()]
    assert "Priya Menon" in names

    # add vitals -> high risk
    v = client.post(f"/patients/{pid}/vitals", headers=h, json={
        "systolic": 150, "diastolic": 95, "heart_rate": 105, "temperature_c": 38.4,
    })
    assert v.status_code == 201

    risk = client.get(f"/patients/{pid}/risk", headers=h).json()
    assert risk["risk_label"] == "HIGH"
    assert risk["risk_score"] >= 60
    assert risk["has_fever"] is True

    # trend
    trend = client.get(f"/patients/{pid}/risk/trend", headers=h).json()
    assert trend["series"], "expected at least one reading in the trend"

    # visit
    visit = client.post(f"/patients/{pid}/visits", headers=h, json={"reason": "Fever"})
    assert visit.status_code == 201
    booked = client.get(f"/patients/{pid}/visits", headers=h).json()
    assert booked[0]["reason"] == "Fever"

    # patch
    upd = client.patch(f"/patients/{pid}", headers=h, json={
        "name": "Priya Menon", "dob": "1992-07-01", "gender": "F",
        "blood_group": "a-", "allergies": [], "height_cm": 165, "weight_kg": 78,
    })
    assert upd.status_code == 200
    assert upd.json()["blood_group"] == "A-"


def test_summary_report(client, admin_token):
    res = client.get("/reports/summary", headers=auth(admin_token))
    assert res.status_code == 200
    body = res.json()
    assert body["total_patients"] >= 0
    assert body["total_departments"] == 8
    assert any("Pediatrics" in d for d in body["departments"])


def test_ml_status_reports_not_trained(client, admin_token):
    res = client.get("/ml/status", headers=auth(admin_token))
    assert res.status_code == 200
    assert res.json()["model_available"] is False


def test_invalid_blood_group_rejected(client, admin_token):
    r = client.post("/patients", headers=auth(admin_token), json={
        "name": "Bad Blood", "dob": "1990-01-01", "gender": "M",
        "blood_group": "Z+", "height_cm": 170, "weight_kg": 70,
    })
    assert r.status_code == 422


def test_delete_requires_admin(client, doctor_token, admin_token):
    h = auth(admin_token)
    p = client.post("/patients", headers=h, json={
        "name": "Gone Soon", "dob": "1980-01-01", "gender": "F",
        "blood_group": "O+", "height_cm": 160, "weight_kg": 55,
    }).json()
    pid = p["patient_id"]

    deny = client.delete(f"/patients/{pid}", headers=auth(doctor_token))
    assert deny.status_code == 403

    ok = client.delete(f"/patients/{pid}", headers=h)
    assert ok.status_code == 204
    assert client.get(f"/patients/{pid}", headers=h).status_code == 404