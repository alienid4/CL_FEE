from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.db.session import db_session
from app.repositories.sqlite_repository import (
    create_record,
    get_record,
    rows_to_dicts,
    update_record,
    void_record,
)
from app.schemas.generic_records import PaymentScheduleCreate, PaymentScheduleUpdate


router = APIRouter()
TABLE = "payment_schedules"
ENTITY_TYPE = "payment_schedule"


@router.get("")
def list_payment_schedules(
    q: Optional[str] = None,
    case_id: Optional[int] = None,
    contract_id: Optional[int] = None,
    payment_month: Optional[str] = None,
    payment_month_from: Optional[str] = None,
    payment_month_to: Optional[str] = None,
    invoice_status: Optional[str] = None,
    status: Optional[str] = None,
    payment_amount_min: Optional[float] = None,
    payment_amount_max: Optional[float] = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    filters: list[str] = []
    params: list[object] = []

    if q:
        filters.append("(payment_month LIKE ? OR invoice_status LIKE ? OR status LIKE ?)")
        params.extend([f"%{q}%"] * 3)
    if case_id is not None:
        filters.append("case_id = ?")
        params.append(case_id)
    if contract_id is not None:
        filters.append("contract_id = ?")
        params.append(contract_id)
    if payment_month:
        filters.append("payment_month = ?")
        params.append(payment_month)
    if payment_month_from:
        filters.append("payment_month >= ?")
        params.append(payment_month_from)
    if payment_month_to:
        filters.append("payment_month <= ?")
        params.append(payment_month_to)
    if invoice_status:
        filters.append("invoice_status = ?")
        params.append(invoice_status)
    if status:
        filters.append("status = ?")
        params.append(status)
    if payment_amount_min is not None:
        filters.append("payment_amount >= ?")
        params.append(payment_amount_min)
    if payment_amount_max is not None:
        filters.append("payment_amount <= ?")
        params.append(payment_amount_max)

    sql = f"SELECT * FROM {TABLE}"
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY payment_month DESC, id DESC LIMIT ?"
    params.append(limit)

    with db_session() as conn:
        records = rows_to_dicts(conn.execute(sql, params).fetchall())
    return {"ok": True, "data": records}


@router.post("", status_code=201)
def create_payment_schedule(payload: PaymentScheduleCreate) -> dict:
    with db_session() as conn:
        record = create_record(
            conn,
            table=TABLE,
            entity_type=ENTITY_TYPE,
            payload=payload.model_dump(exclude_unset=True),
        )
    return {"ok": True, "data": record}


@router.get("/{record_id}")
def get_payment_schedule(record_id: int) -> dict:
    with db_session() as conn:
        record = get_record(conn, table=TABLE, record_id=record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"{ENTITY_TYPE} not found")
    return {"ok": True, "data": record}


@router.put("/{record_id}")
def update_payment_schedule(record_id: int, payload: PaymentScheduleUpdate) -> dict:
    with db_session() as conn:
        record = update_record(
            conn,
            table=TABLE,
            entity_type=ENTITY_TYPE,
            record_id=record_id,
            payload=payload.model_dump(exclude_unset=True),
        )
    if record is None:
        raise HTTPException(status_code=404, detail=f"{ENTITY_TYPE} not found")
    return {"ok": True, "data": record}


@router.post("/{record_id}/void")
def void_payment_schedule(record_id: int) -> dict:
    with db_session() as conn:
        record = void_record(conn, table=TABLE, entity_type=ENTITY_TYPE, record_id=record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"{ENTITY_TYPE} not found")
    return {"ok": True, "data": record}
