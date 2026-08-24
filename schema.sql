-- ============================================================================
-- Clinic Booking System - Postgres schema (Railway-ready)
-- Mirrors models.py exactly. Safe to run; uses IF NOT EXISTS so it is idempotent.
-- Run this against your Railway Postgres instance (Railway SQL editor or:
--   psql "$DATABASE_URL" -f schema.sql
-- )
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- Enum type used by the appointments.status column
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'appointment_status') THEN
    CREATE TYPE appointment_status AS ENUM ('booked', 'cancelled');
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- doctors
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    id                 SERIAL PRIMARY KEY,
    full_name          VARCHAR NOT NULL,
    speciality         VARCHAR NOT NULL,
    phone_number       VARCHAR NOT NULL,
    email              VARCHAR NOT NULL UNIQUE,
    working_hours_start TIME   NOT NULL,
    working_hours_end   TIME   NOT NULL,
    break_start         TIME   NOT NULL,
    break_end           TIME   NOT NULL
);

-- ---------------------------------------------------------------------------
-- patients
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id           SERIAL PRIMARY KEY,
    patient_name VARCHAR NOT NULL,
    phone_number VARCHAR NOT NULL,
    email        VARCHAR NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------------
-- appointments
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    id                 SERIAL PRIMARY KEY,
    doctor_id          INTEGER NOT NULL REFERENCES doctors(id),
    patient_id         INTEGER NOT NULL REFERENCES patients(id),
    start_time         TIMESTAMP NOT NULL,
    status             appointment_status NOT NULL DEFAULT 'booked',
    cancellation_reason VARCHAR,
    notes              VARCHAR
);

-- Partial unique index: prevents two BOOKED appointments for the same doctor
-- at the same start_time. Cancelled rows are excluded, so a freed slot can be
-- rebooked (and rescheduling works by moving the single row's start_time).
CREATE UNIQUE INDEX IF NOT EXISTS uq_doctor_slot_when_booked
    ON appointments (doctor_id, start_time)
    WHERE status = 'booked';

-- Convenience indexes for the queries the app runs most often.
CREATE INDEX IF NOT EXISTS ix_appointments_doctor_id
    ON appointments (doctor_id);
CREATE INDEX IF NOT EXISTS ix_appointments_patient_id
    ON appointments (patient_id);

COMMIT;

-- ============================================================================
-- Optional: seed 5 doctors (uncomment to run)
-- ============================================================================
-- INSERT INTO doctors
--   (full_name, speciality, phone_number, email,
--    working_hours_start, working_hours_end, break_start, break_end)
-- VALUES
--   ('Dr. Amina Yusuf', 'General Practice', '+254700000001', 'amina.yusuf@clinic.test', '08:00', '17:00', '13:00', '14:00'),
--   ('Dr. Brian Otieno', 'Pediatrics', '+254700000002', 'brian.otieno@clinic.test', '09:00', '18:00', '12:00', '13:00'),
--   ('Dr. Cynthia Wambui', 'Dermatology', '+254700000003', 'cynthia.wambui@clinic.test', '08:30', '16:30', '12:30', '13:30'),
--   ('Dr. Daniel Kiptoo', 'Orthopedics', '+254700000004', 'daniel.kiptoo@clinic.test', '09:00', '17:00', '13:00', '14:00'),
--   ('Dr. Esther Achieng', 'Gynaecology', '+254700000005', 'esther.achieng@clinic.test', '08:00', '16:00', '11:30', '12:30');
