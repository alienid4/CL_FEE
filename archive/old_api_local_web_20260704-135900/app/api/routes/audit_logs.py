from fastapi import APIRouter

from app.db.session import db_session
from app.repositories.sqlite_repository import list_audit_logs


router = APIRouter()


@router.get("")
def list_logs(limit: int = 100) -> dict:
    with db_session() as conn:
        logs = list_audit_logs(conn, limit=limit)
    return {"ok": True, "data": logs}
