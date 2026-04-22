from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base


def _build_engine() -> Engine:
    connect_args: dict[str, object] = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(settings.database_url, future=True, connect_args=connect_args)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    if settings.database_url.startswith("sqlite"):
        db_url = make_url(settings.database_url)
        database = db_url.database
        if database and database != ":memory:":
            engine.dispose()
            db_path = Path(database)
            if db_path.exists():
                db_path.unlink()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
