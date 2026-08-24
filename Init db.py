
from database import engine, Base
import models  


def init():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


if __name__ == "__main__":
    init()