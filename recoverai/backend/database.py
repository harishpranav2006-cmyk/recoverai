"""RecoverAI — SQLAlchemy database engine, session, and base model."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Session:  # type: ignore[misc]
    """FastAPI dependency — yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db  # type: ignore[misc]
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables defined by ORM models."""
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """Drop all tables (use in tests / reset only)."""
    Base.metadata.drop_all(bind=engine)
