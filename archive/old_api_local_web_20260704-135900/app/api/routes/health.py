from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.db.schema import init_db
from app.db.session import db_session


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    db_ok = False
    db_error = None
    try:
        with db_session() as conn:
            init_db(conn)
            conn.execute("SELECT 1").fetchone()
            db_ok = True
    except Exception as exc:  # pragma: no cover - defensive health output
        db_error = str(exc)

    data = {
        "ok": True,
        "service": settings.app_name,
        "runtime": "python-fastapi",
        "database": {
            "type": settings.db_type,
            "name": settings.mssql_database if settings.db_type == "mssql" else settings.sqlite_path,
            "ok": db_ok,
            "error": db_error,
        },
        "base_url": settings.app_base_url,
        "time": datetime.now(timezone.utc).isoformat(),
    }
    return data
