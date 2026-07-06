from fastapi import APIRouter, HTTPException
from typing import Optional

from app.db.session import db_session
from app.repositories.sqlite_repository import insert_audit_log, now_iso, row_to_dict, rows_to_dicts
from app.schemas.signing_case import SigningCaseCreate, SigningCaseUpdate


router = APIRouter()


@router.get("")
def list_cases(q: Optional[str] = None, limit: int = 100) -> dict:
    sql = "SELECT * FROM signing_cases"
    params: list[object] = []
    if q:
        sql += " WHERE title LIKE ? OR case_code LIKE ? OR category LIKE ?"
        like = f"%{q}%"
        params.extend([like, like, like])
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return {"ok": True, "data": rows_to_dicts(rows)}


@router.post("", status_code=201)
def create_case(payload: SigningCaseCreate) -> dict:
    timestamp = now_iso()
    data = payload.model_dump(exclude_unset=True)
    columns = list(data.keys()) + ["created_at", "updated_at"]
    values = [data[column] for column in data] + [timestamp, timestamp]
    placeholders = ", ".join("?" for _ in columns)
    with db_session() as conn:
        cursor = conn.execute(
            f"INSERT INTO signing_cases ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )
        case = row_to_dict(conn.execute("SELECT * FROM signing_cases WHERE id = ?", (cursor.lastrowid,)).fetchone())
        insert_audit_log(conn, entity_type="signing_case", entity_id=cursor.lastrowid, action="create", detail=case)
    return {"ok": True, "data": case}


@router.get("/{case_id}")
def get_case(case_id: int) -> dict:
    with db_session() as conn:
        case = row_to_dict(conn.execute("SELECT * FROM signing_cases WHERE id = ?", (case_id,)).fetchone())
    if case is None:
        raise HTTPException(status_code=404, detail="signing case not found")
    return {"ok": True, "data": case}


@router.put("/{case_id}")
def update_case(case_id: int, payload: SigningCaseUpdate) -> dict:
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="no fields to update")
    allowed = [
        "case_code",
        "title",
        "category",
        "owner_department",
        "owner_user",
        "vendor_name",
        "role",
        "permission_scope",
        "amount",
        "budget_status",
        "project_status",
        "signing_status",
        "approval_status",
        "contract_status",
        "procurement_status",
        "payment_status",
        "invoice_status",
        "source_file_name",
        "source_sheet",
        "source_row",
        "source_column",
        "source_value",
        "cmdb_ci_id",
        "cmdb_ci_name",
        "cmdb_system_name",
        "cmdb_service_name",
        "cmdb_owner_department",
        "cmdb_environment",
        "cmdb_import_batch_id",
        "cmdb_last_synced_at",
        "cmdb_match_status",
        "cmdb_evidence_note",
        "status",
    ]
    assignments = [f"{field} = ?" for field in allowed if field in fields]
    values = [fields[field] for field in allowed if field in fields]
    values.extend([now_iso(), case_id])
    with db_session() as conn:
        result = conn.execute(
            f"UPDATE signing_cases SET {', '.join(assignments)}, updated_at = ? WHERE id = ?",
            values,
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="signing case not found")
        case = row_to_dict(conn.execute("SELECT * FROM signing_cases WHERE id = ?", (case_id,)).fetchone())
        insert_audit_log(conn, entity_type="signing_case", entity_id=case_id, action="update", detail=fields)
    return {"ok": True, "data": case}


@router.post("/{case_id}/status")
def update_case_status(case_id: int, status: str) -> dict:
    return update_case(case_id, SigningCaseUpdate(status=status))


@router.get("/{case_id}/logs")
def get_case_logs(case_id: int) -> dict:
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT * FROM audit_logs
            WHERE entity_type = 'signing_case' AND entity_id = ?
            ORDER BY id DESC
            """,
            (case_id,),
        ).fetchall()
    return {"ok": True, "data": rows_to_dicts(rows)}
