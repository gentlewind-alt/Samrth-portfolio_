"""Database session dependency for FastAPI.

Uses SQLAlchemy with SQLite for the prototype. In production you can switch to PostgreSQL by updating the DATABASE_URL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import os

# Default to SQLite file in the backend folder
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resume.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """FastAPI dependency that provides a DB session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
