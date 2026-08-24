"""Idempotent startup: create tables, then seed doctors if the table is empty.

Used on Railway (see Procfile) where Uvicorn runs this once at boot before
serving, so the Postgres schema + seed data are guaranteed to exist.
"""
import models  # noqa: F401  (import registers models on Base.metadata)
from database import Base, SessionLocal, engine
from seed import seed, seed_patients


def main() -> None:
    print("Creating tables (if not present)...")
    Base.metadata.create_all(bind=engine)

    print("Seeding doctors (no-op if already seeded)...")
    seed()
    print("Seeding patients (no-op if already seeded)...")
    seed_patients()
    print("Startup complete.")


if __name__ == "__main__":
    main()