import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker


def _build_database_url() -> str:
   
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
    
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


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

    
    return "sqlite:///./clinic.db"


DATABASE_URL = _build_database_url()

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    
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