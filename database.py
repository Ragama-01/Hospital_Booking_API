import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Reads the connection string from DATABASE_URL (e.g. a Railway Postgres URL).
# Falls back to a local SQLite file so the app can run in dev without a DB,
# and so the test suite is self-contained.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./clinic.db")

# Railway (and most managed Postgres providers) issue URLs starting with
# "postgres://", but SQLAlchemy's psycopg driver expects "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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