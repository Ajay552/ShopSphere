"""Database engine and initialization for ShopSphere."""

from __future__ import annotations

import functools
import os
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from tools.models import Base, Product

DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_SQLITE_PATH = DATA_DIR / "shopsphere.db"


def get_database_url() -> str:
    """Return DATABASE_URL from env or default SQLite file under data/."""
    return os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")


@functools.lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create and cache the SQLAlchemy engine."""
    url = get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


def get_session() -> Session:
    """Return a new ORM session bound to the shared engine."""
    factory = sessionmaker(bind=get_engine())
    return factory()


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(get_engine())


def is_database_empty() -> bool:
    """Return True when the products table has no rows."""
    init_db()
    with get_session() as session:
        count = session.scalar(select(func.count()).select_from(Product))
        return not count


def ensure_db_seeded() -> None:
    """Seed the database from JSON when the DB file or products table is empty."""
    from tools.seed import seed_from_json

    url = get_database_url()
    if url.startswith("sqlite:///"):
        db_path = Path(url.replace("sqlite:///", "", 1))
        if not db_path.is_file():
            seed_from_json(force=False)
            return

    if is_database_empty():
        seed_from_json(force=False)
