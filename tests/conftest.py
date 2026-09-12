"""Shared test fixtures.

Before importing the app we point the database and the ML artifact dir at
isolated temp paths so tests never touch real data or trained artifacts.
"""

import os
import tempfile

import pytest

_TMP = tempfile.mkdtemp(prefix="meditrack_test_")
os.environ["SQLITE_PATH"] = os.path.join(_TMP, "test.db")
os.environ["MODEL_ARTIFACT_DIR"] = os.path.join(_TMP, "no_artifacts")
os.environ["JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402


@pytest.fixture()
def client():
    """TestClient that triggers app startup (init_db + seed admin)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_token(client) -> str:
    res = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture()
def doctor_token(client) -> str:
    res = client.post("/auth/login", data={"username": "dr.sharma", "password": "doctor123"})
    assert res.status_code == 200
    return res.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}