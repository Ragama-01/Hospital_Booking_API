"""Integration tests for the clinic booking logic.

Because the tests hit the FastAPI app through TestClient and seed real rows into
a SQLite database (see conftest.py), they exercise the routers plus the business
rules in services.py.
"""

from datetime import date, datetime, timedelta, time

import models
from database import SessionLocal


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _seed_doctor(db, **overrides):
    """Doctor with working hours 08:00-17:00 and a 13:00-14:00 break by default."""
    defaults = {
        "full_name": "Dr. Test",
        "speciality": "General Practice",
        "phone_number": "+254700000000",
        "email": f"doctor.{datetime.now().microsecond}@clinic.test",
        "working_hours_start": time(8, 0),
        "working_hours_end": time(17, 0),
        "break_start": time(13, 0),
        "break_end": time(14, 0),
    }
    defaults.update(overrides)
    doctor = models.Doctor(**defaults)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def _seed_patient(db):
    patient = models.Patient(
        patient_name="Test Patient",
        phone_number="+254799999999",
        email=f"patient.{datetime.now().microsecond}@clinic.test",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _seed_doctor_patient(db):
    """Returns a (doctor_id, patient_id) tuple of freshly seeded rows.

    Note: the session is left open on purpose so tests can seed further rows
    (e.g. an extra patient) through `db`. Local sessions don't hold locks once
    the seeding commit has ended the transaction.
    """
    doctor = _seed_doctor(db)
    patient = _seed_patient(db)
    return doctor.id, patient.id


def _slot(day_offset=3, hour=9, minute=0):
    """A valid-looking future 30-min-aligned slot in ISO form, inside working hours."""
    dt = datetime.combine(date.today() + timedelta(days=day_offset), time(hour, minute))
    return dt.isoformat()


def _hm(slot_str: str) -> str:
    """Normalise a serialized slot ('09:00:00' or '09:00') to 'HH:MM'."""
    return slot_str[:5]


# ---------------------------------------------------------------------------
# POST /appointments
# ---------------------------------------------------------------------------
def test_book_appointment_succeeds(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    resp = client.post(
        "/appointments",
        json={
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "start_time": _slot(),
            "notes": "Follow-up",
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "booked"
    assert body["doctor_id"] == doctor_id
    assert body["notes"] == "Follow-up"


def test_book_appointment_in_past_rejected(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    past = (datetime.now() - timedelta(days=1)).replace(minute=0, second=0, microsecond=0).isoformat()
    resp = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": past},
    )

    assert resp.status_code == 400
    assert "future" in resp.json()["detail"].lower()


def test_book_appointment_within_hour_of_now_rejected(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    soon = (datetime.now() + timedelta(minutes=5)).isoformat()
    resp = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": soon},
    )

    assert resp.status_code == 400


def test_book_appointment_outside_working_hours_rejected(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    # 19:00 is after working_hours_end (17:00).
    resp = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": _slot(hour=19)},
    )

    assert resp.status_code == 400
    assert "working hours" in resp.json()["detail"]


def test_book_appointment_during_break_rejected(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    # 13:00 falls inside the doctor's 13:00-14:00 break.
    resp = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": _slot(hour=13)},
    )

    assert resp.status_code == 400
    assert "break" in resp.json()["detail"]


def test_book_non_aligned_slot_rejected(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    # 09:15 is not on a 30-minute boundary.
    resp = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": _slot(minute=15)},
    )

    assert resp.status_code == 400
    assert "30-minute" in resp.json()["detail"]


def test_book_already_taken_slot_conflicts(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    payload = {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "start_time": _slot(hour=10),
    }
    assert client.post("/appointments", json=payload).status_code == 201

    # Second patient tries the same slot for the same doctor.
    other = _seed_patient(db)
    resp = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": other.id, "start_time": _slot(hour=10)},
    )

    assert resp.status_code == 409
    assert "already" in resp.json()["detail"]


def test_book_nonexistent_doctor_404(client):
    db = SessionLocal()
    _, patient_id = _seed_doctor_patient(db)

    resp = client.post(
        "/appointments",
        json={"doctor_id": 99999, "patient_id": patient_id, "start_time": _slot()},
    )

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------
def test_availability_excludes_break_and_booked_slots(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    # Book 09:00 for the target date.
    target = _slot(hour=9)
    resp = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": target},
    )
    assert resp.status_code == 201

    target_date = target[:10]
    resp = client.get(f"/doctors/{doctor_id}/availability", params={"date": target_date})
    assert resp.status_code == 200

    slots = [_hm(s) for s in resp.json()["available_slots"]]
    assert "09:00" not in slots  # booked
    assert "13:00" not in slots  # inside break
    assert "13:30" not in slots  # starts inside 13:00-14:00 break
    assert "09:30" in slots  # free


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------
def test_cancel_frees_slot_for_rebooking(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)
    slot = _slot(hour=10)

    book = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": slot},
    )
    appointment_id = book.json()["id"]

    cancel = client.patch(
        f"/appointments/{appointment_id}/cancel", json={"reason": "Patient unavailable"}
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"
    assert cancel.json()["cancellation_reason"] == "Patient unavailable"

    # The freed slot is bookable again.
    rebook = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": slot},
    )
    assert rebook.status_code == 201


def test_cancel_already_cancelled_fails(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    book = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": _slot(hour=9)},
    )
    appointment_id = book.json()["id"]

    assert (
        client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "First"}).status_code
        == 200
    )
    resp = client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "Again"})
    assert resp.status_code == 400
    assert "already cancelled" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Reschedule
# ---------------------------------------------------------------------------
def test_reschedule_moves_slot_and_frees_original(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)
    original, new = _slot(hour=9), _slot(hour=11)

    book = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": original},
    )
    appointment_id = book.json()["id"]

    resp = client.patch(
        f"/appointments/{appointment_id}/reschedule", json={"new_start_time": new}
    )
    assert resp.status_code == 200
    assert resp.json()["start_time"].startswith(new[:10] + "T11:00")

    # Original slot is free again, the new one is taken.
    target_date = original[:10]
    slots = [
        _hm(s)
        for s in client.get(
            f"/doctors/{doctor_id}/availability", params={"date": target_date}
        ).json()["available_slots"]
    ]
    assert "09:00" in slots
    assert "11:00" not in slots

    # And the original slot can now actually be booked.
    rebook = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": original},
    )
    assert rebook.status_code == 201


def test_reschedule_cancelled_appointment_fails(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    book = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": _slot(hour=9)},
    )
    appointment_id = book.json()["id"]
    client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "N/A"})

    resp = client.patch(
        f"/appointments/{appointment_id}/reschedule", json={"new_start_time": _slot(hour=11)}
    )
    assert resp.status_code == 400
    assert "cancelled" in resp.json()["detail"]


def test_reschedule_to_taken_slot_conflicts(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    first = client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": _slot(hour=9)},
    ).json()["id"]
    # Second patient holds 11:00.
    other = _seed_patient(db)
    client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": other.id, "start_time": _slot(hour=11)},
    )

    resp = client.patch(
        f"/appointments/{first}/reschedule", json={"new_start_time": _slot(hour=11)}
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Patient upcoming appointments (bonus)
# ---------------------------------------------------------------------------
def test_patient_upcoming_appointments_sorted(client):
    db = SessionLocal()
    doctor_id, patient_id = _seed_doctor_patient(db)

    # Book 10:00 first, then 09:00 — endpoint must sort by start time.
    client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": _slot(hour=10)},
    )
    client.post(
        "/appointments",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "start_time": _slot(hour=9)},
    )

    resp = client.get(f"/patients/{patient_id}/appointments")
    assert resp.status_code == 200
    body = resp.json()
    assert body["patient_id"] == patient_id
    starts = [a["start_time"] for a in body["appointments"]]
    assert starts == sorted(starts)
    assert len(starts) == 2