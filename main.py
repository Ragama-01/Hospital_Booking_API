from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import appointments, doctors, patients

app = FastAPI(title="Clinic Booking System")

# Allow the web UI (served from this same app) and any dev frontend to call the
# API, including from a different origin during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "Clinic Booking System"}


app.include_router(doctors)
app.include_router(appointments)
app.include_router(patients)

# Serve the web UI. Mounted last so it never shadows the API routes; visiting
# the root (/) renders the interface at static/index.html.
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="ui")