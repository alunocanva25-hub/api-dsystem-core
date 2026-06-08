import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app import models  # noqa: F401
from app.services.seed_service import seed_database


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    print("DSYSTEM SERVER CORE V1.0.1.1 - banco inicializado com sucesso.")


if __name__ == "__main__":
    main()
