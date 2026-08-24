import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker


def _build_database_url() -> str:
    """Determine the database connection string from the environment.

    Order of preference (so it works across Railway, Heroku, and local dev):

    1. A full URL from one of the common provider variable names. Railway
       usually exposes RAILWAY_DATABASE_URL and/or a plain DATABASE_URL; either
       is accepted. We strip stray whitespace/quotes in case a variable got
       wrapped when pasted into the dashboard.
    2. Individual Postgres parts (PGHOST, PGPORT, PGUSER, PGPASSWORD,
       PGDATABASE) — Railway's default variables when you attach Postgres.
    3. Fall back to a local SQLite file so dev runs and the test suite stay
       self-contained with no database configured.
    """
    url = None
    for name in ("RAILWAY_DATABASE_URL", "DATABASE_URL", "POSTGRES_URL"):
        raw = os.environ.get(name)
        if not raw:
            continue
        candidate = str(raw).strip().strip('"').strip("'")
        if candidate:
            url = candidate
            break

    if url:
        # Railway / managed providers commonly issue "postgres://" but
        # SQLAlchemy's psycopg drivers expect "postgresql://".
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # Build from individual Postgres variables if present.
    if os.environ.get("PGHOST") and os.environ.get("PGUSER"):
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=os.environ.get("PGUSER"),
            password=os.environ.get("PGPASSWORD"),
            host=os.environ.get("PGHOST"),
            port=os.environ.get("PGPORT"),
            database=os.environ.get("PGDATABASE"),
        )
        return url.render_as_string(hide_password=False)

    # Local development / tests: SQLite file.
    return "sqlite:///./clinic.db"


DATABASE_URL = _build_database_url()

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # FastAPI runs request handling across threads; SQLite needs to allow it.
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a session, always closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()