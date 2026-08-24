from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from models import Appointment, AppointmentStatus, Doctor

SLOT_MINUTES = 30


def generate_slots_for_doctor(db: Session, doctor: Doctor, target_date: date) -> list[time]:
    """
    Returns every free 30-minute slot for `doctor` on `target_date`, i.e.
    every slot that is:
      - within the doctor's working hours
      - not inside the doctor's break
      - not already booked
    """
    day_start = datetime.combine(target_date, doctor.working_hours_start)
    day_end = datetime.combine(target_date, doctor.working_hours_end)
    break_start = datetime.combine(target_date, doctor.break_start)
    break_end = datetime.combine(target_date, doctor.break_end)

    day_floor = datetime.combine(target_date, time.min)
    day_ceiling = datetime.combine(target_date, time.max)
    booked_times = {
        appt.start_time
        for appt in db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor.id,
            Appointment.status == AppointmentStatus.booked,
            Appointment.start_time >= day_floor,
            Appointment.start_time <= day_ceiling,
        )
        .all()
    }

    slots: list[time] = []
    current = day_start
    while current + timedelta(minutes=SLOT_MINUTES) <= day_end:
        slot_end = current + timedelta(minutes=SLOT_MINUTES)
        overlaps_break = current < break_end and slot_end > break_start
        if not overlaps_break and current not in booked_times:
            slots.append(current.time())
        current += timedelta(minutes=SLOT_MINUTES)

    return slots