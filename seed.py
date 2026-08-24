"""
Seeds 5 doctors with working hours and a 1-hour break each, plus a handful
of dummy patients. Run after init_db.py:

    python seed.py
"""
from datetime import time

from database import SessionLocal
import models


def seed():
    db = SessionLocal()
    try:
        if db.query(models.Doctor).count() > 0:
            print("Doctors already seeded — skipping.")
            return

        doctors = [
            models.Doctor(
                full_name="Dr. Amina Yusuf",
                speciality="General Practice",
                phone_number="+254700000001",
                email="amina.yusuf@clinic.test",
                working_hours_start=time(8, 0),
                working_hours_end=time(17, 0),
                break_start=time(13, 0),
                break_end=time(14, 0),
            ),
            models.Doctor(
                full_name="Dr. Brian Otieno",
                speciality="Pediatrics",
                phone_number="+254700000002",
                email="brian.otieno@clinic.test",
                working_hours_start=time(9, 0),
                working_hours_end=time(18, 0),
                break_start=time(12, 0),
                break_end=time(13, 0),
            ),
            models.Doctor(
                full_name="Dr. Cynthia Wambui",
                speciality="Dermatology",
                phone_number="+254700000003",
                email="cynthia.wambui@clinic.test",
                working_hours_start=time(8, 30),
                working_hours_end=time(16, 30),
                break_start=time(12, 30),
                break_end=time(13, 30),
            ),
            models.Doctor(
                full_name="Dr. Daniel Kiptoo",
                speciality="Orthopedics",
                phone_number="+254700000004",
                email="daniel.kiptoo@clinic.test",
                working_hours_start=time(9, 0),
                working_hours_end=time(17, 0),
                break_start=time(13, 0),
                break_end=time(14, 0),
            ),
            models.Doctor(
                full_name="Dr. Esther Achieng",
                speciality="Gynaecology",
                phone_number="+254700000005",
                email="esther.achieng@clinic.test",
                working_hours_start=time(8, 0),
                working_hours_end=time(16, 0),
                break_start=time(11, 30),
                break_end=time(12, 30),
            ),
        ]
        db.add_all(doctors)
        db.commit()
        print(f"Seeded {len(doctors)} doctors.")
    finally:
        db.close()


def seed_patients():
    """Seed a few dummy patients (idempotent — skips if any already exist)."""
    db = SessionLocal()
    try:
        if db.query(models.Patient).count() > 0:
            print("Patients already seeded — skipping.")
            return

        patients = [
            models.Patient(
                patient_name="Jane Doe",
                phone_number="+254711111111",
                email="jane.doe@example.com",
            ),
            models.Patient(
                patient_name="John Mwangi",
                phone_number="+254722222222",
                email="john.mwangi@example.com",
            ),
            models.Patient(
                patient_name="Alice Njeri",
                phone_number="+254733333333",
                email="alice.njeri@example.com",
            ),
            models.Patient(
                patient_name="Peter Kamau",
                phone_number="+254744444444",
                email="peter.kamau@example.com",
            ),
            models.Patient(
                patient_name="Grace Atieno",
                phone_number="+254755555555",
                email="grace.atieno@example.com",
            ),
        ]
        db.add_all(patients)
        db.commit()
        print(f"Seeded {len(patients)} patients.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    seed_patients()