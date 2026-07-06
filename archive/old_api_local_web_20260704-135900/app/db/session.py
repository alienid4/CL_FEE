from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

from app.core.config import get_settings


def _sqlite_path() -> str:
    settings = get_settings()
    if settings.db_type != "sqlite":
        raise RuntimeError("Only sqlite is implemented in this development build.")
    if settings.sqlite_path == ":memory:":
        return settings.sqlite_path
    path = Path(settings.sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_sqlite_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
