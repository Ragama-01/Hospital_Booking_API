"""Shared pytest fixtures for the clinic booking tests.

The test suite runs on a throwaway local SQLite database so it needs no
Postgres. We point DATABASE_URL at SQLite *before* importing the app modules.
"""
import os
import sys
from pathlib import Path

# Make sure the project root is importable regardless of how pytest is invoked.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///./test_clinic.db"

import pytest
from fastapi.testclient import TestClient

import models
from database import Base, SessionLocal, engine, get_db
from main import app


@pytest.fixture(autouse=True)
def _reset_db():
    """Drop/recreate schema per test.

    The production uniqueness rule is a *partial* PostgreSQL index
    (WHERE status = 'booked'). SQLite would ignore the partial clause and emit a
    plain unique index, which would wrongly block rebooking a cancelled slot.
    So for the SQLite run we drop that index and rely on the service-level checks
    that the tests exercise.
    """
    index = next(
        (i for i in models.Appointment.__table__.indexes if i.name == "uq_doctor_slot_when_booked"),
        None,
    )
    if index is not None:
        models.Appointment.__table__.indexes.remove(index)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c