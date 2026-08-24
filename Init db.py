"""
Creates all tables defined in models.py against DATABASE_URL.
Run once against your Railway Postgres instance:

    python init_db.py
"""
from database import engine, Base
import models  # noqa: F401  (import registers models on Base.metadata)


def init():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


if __name__ == "__main__":
    init()