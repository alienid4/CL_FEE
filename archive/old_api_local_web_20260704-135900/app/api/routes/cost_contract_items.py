from fastapi import APIRouter, HTTPException
from typing import Optional

from app.db.session import db_session
from app.repositories.sqlite_repository import insert_audit_log, now_iso, row_to_dict, rows_to_dicts
from app.schemas.cost_contract_item import CostContractItemCreate, CostContractItemUpdate


router = APIRouter()


@router.get("")
def list_items(q: Optional[str] = None, limit: int = 100) -> dict:
    sql = "SELECT * FROM cost_contract_items"
    params: list[object] = []
    if q:
        sql += " WHERE cost_item_name LIKE ? OR vendor_name LIKE ? OR cost_item_code LIKE ?"
        like = f"%{q}%"
        params.extend([like, like, like])
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return {"ok": True, "data": rows_to_dicts(rows)}


@router.post("", status_code=201)
def create_item(payload: CostContractItemCreate) -> dict:
    timestamp = now_iso()
    with db_session() as conn:
        cursor = conn.execute(
            """
            INSERT INTO cost_contract_items
                (cost_item_code, cost_item_name, vendor_name, contract_amount, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.cost_item_code,
                payload.cost_item_name,
                payload.vendor_name,
                payload.contract_amount,
                payload.status,
                timestamp,
                timestamp,
            ),
        )
        item = row_to_dict(
            conn.execute("SELECT * FROM cost_contract_items WHERE id = ?", (cursor.lastrowid,)).fetchone()
        )
        insert_audit_log(conn, entity_type="cost_contract_item", entity_id=cursor.lastrowid, action="create", detail=item)
    return {"ok": True, "data": item}


@router.get("/{item_id}")
def get_item(item_id: int) -> dict:
    with db_session() as conn:
        item = row_to_dict(conn.execute("SELECT * FROM cost_contract_items WHERE id = ?", (item_id,)).fetchone())
    if item is None:
        raise HTTPException(status_code=404, detail="cost contract item not found")
    return {"ok": True, "data": item}


@router.put("/{item_id}")
def update_item(item_id: int, payload: CostContractItemUpdate) -> dict:
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="no fields to update")
    allowed = ["cost_item_code", "cost_item_name", "vendor_name", "contract_amount", "status"]
    assignments = [f"{field} = ?" for field in allowed if field in fields]
    values = [fields[field] for field in allowed if field in fields]
    values.extend([now_iso(), item_id])
    with db_session() as conn:
        result = conn.execute(
            f"UPDATE cost_contract_items SET {', '.join(assignments)}, updated_at = ? WHERE id = ?",
            values,
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="cost contract item not found")
        item = row_to_dict(conn.execute("SELECT * FROM cost_contract_items WHERE id = ?", (item_id,)).fetchone())
        insert_audit_log(conn, entity_type="cost_contract_item", entity_id=item_id, action="update", detail=fields)
    return {"ok": True, "data": item}


@router.post("/{item_id}/void")
def void_item(item_id: int) -> dict:
    with db_session() as conn:
        result = conn.execute(
            "UPDATE cost_contract_items SET status = ?, updated_at = ? WHERE id = ?",
            ("void", now_iso(), item_id),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="cost contract item not found")
        item = row_to_dict(conn.execute("SELECT * FROM cost_contract_items WHERE id = ?", (item_id,)).fetchone())
        insert_audit_log(conn, entity_type="cost_contract_item", entity_id=item_id, action="void", detail=item)
    return {"ok": True, "data": item}
