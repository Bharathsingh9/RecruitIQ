"""
FastAPI route dependency injectors.
Resolves SQLAlchemy connection sessions.
"""

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    Creates and yields an isolated database connection session, closing it on teardown.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
