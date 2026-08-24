# Clinic Booking System

A REST API for a clinic appointment booking system, built with **FastAPI**,
**SQLAlchemy** and **PostgreSQL**.

## Features / Endpoints

| Method | Endpoint                              | Description |
| ------ | ------------------------------------- | ----------- |
| POST   | `/appointments`                       | Book a 30-min slot (validated against working hours, break, past time and double-booking). |
| GET    | `/doctors`                            | List all doctors. |
| GET    | `/doctors/{id}/availability?date=...` | All free 30-min slots for a doctor on a date. |
| GET    | `/patients`                           | List all patients. |
| POST   | `/patients`                           | Register a new patient. |
| PATCH  | `/appointments/{id}/cancel`           | Cancel with a reason; slot becomes bookable again. |
| PATCH  | `/appointments/{id}/reschedule`       | Move to a new slot; original slot is freed. |
| GET    | `/patients/{id}/appointments`         | (Bonus) Upcoming appointments sorted by start date. |

## Web UI

A self-contained web interface (no build step, plain HTML/CSS/JS) lives in
**`static/`** and is served by FastAPI itself:

1. **Book Appointment** – pick a doctor and date to see its free 30-min slots,
   then pick/create a patient and book.
2. **My Appointments** – pick a patient to list upcoming appointments, then
   **cancel** (with a reason) or **reschedule**.

Because the app mounts `static/` at `/`, visiting the server root shows the UI
(e.g. http://localhost:8000/), the API lives under `/docs`, the JSON health
check moved to `/health`, and CORS is enabled for local development.

## Business rules

- Slots are **30 minutes** and must start on a `:00`/`:30` boundary.
- A slot must be inside the doctor's working hours **and** end before they finish.
- Slots inside the doctor's break are never bookable.
- Appointments must be booked **at least 1 hour in the future** (bonus rule).
- Double-booking the same doctor/slot is prevented:
  - application-level check in `services.py`, plus
  - a **PostgreSQL partial unique index**
    `(doctor_id, start_time)` **WHERE status='booked'** as a concurrency backstop.
  Because the index only covers `booked` rows, a cancelled slot is immediately
  rebookable and rescheduling (which moves the single row) works naturally.

## Project layout

```
database.py         engine / session / get_db dependency
models.py           Doctor, Patient, Appointment
schemas.py          Pydantic request/response models
services.py         trading rules + booking operations (the core logic)
availability.py     30-min slot generation
routers/            FastAPI routers: doctors, appointments, patients
main.py             FastAPI app + router registration + static UI mount
static/             Web UI (index.html, styles.css, app.js; served at /)
seed.py             seeds 5 doctors
startup.py          idempotent boot: create tables + seed (used on Railway)
Init db.py          create tables only (python "Init db.py")
tests/              pytest suite for the booking logic
```

## Setup

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Run against your own Postgres (e.g. Railway):

```bash
export DATABASE_URL="postgresql://user:pass@host:port/dbname"
python "Init db.py"   # create tables
python seed.py        # seed 5 doctors
uvicorn main:app --reload
```

### Deploying on Railway

1. Push this repo to GitHub and import it in Railway (or use the Railway CLI).
2. Add a **Postgres** service from Railway's dashboard — it provisions a
   `DATABASE_URL` env var automatically, which the app already reads.
3. The included **`Procfile`** runs `python startup.py` (idempotent table
   creation + doctor seeding) then `uvicorn main:app --host 0.0.0.0 --port $PORT`,
   so schema and seed data are guaranteed to exist at boot.
4. Open the generated `https://<your-app>.up.railway.app/docs`.

Interactive docs at <http://localhost:8000/docs>.

## Tests

The suite is self-contained — it runs on a throwaway local SQLite file, so you
don't need Postgres to verify the booking logic:

```bash
pytest -q
```