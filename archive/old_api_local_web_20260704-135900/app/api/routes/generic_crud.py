from typing import Type

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.session import db_session
from app.repositories.sqlite_repository import create_record, get_record, list_records, update_record, void_record


def build_crud_router(
    *,
    table: str,
    entity_type: str,
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    search_columns: list[str],
) -> APIRouter:
    router = APIRouter()

    @router.get("")
    def list_endpoint(q: str | None = None, limit: int = 100) -> dict:
        with db_session() as conn:
            records = list_records(conn, table=table, search_columns=search_columns, q=q, limit=limit)
        return {"ok": True, "data": records}

    @router.post("", status_code=201)
    def create_endpoint(payload: create_schema) -> dict:  # type: ignore[valid-type]
        with db_session() as conn:
            record = create_record(
                conn,
                table=table,
                entity_type=entity_type,
                payload=payload.model_dump(exclude_unset=True),
            )
        return {"ok": True, "data": record}

    @router.get("/{record_id}")
    def get_endpoint(record_id: int) -> dict:
        with db_session() as conn:
            record = get_record(conn, table=table, record_id=record_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"{entity_type} not found")
        return {"ok": True, "data": record}

    @router.put("/{record_id}")
    def update_endpoint(record_id: int, payload: update_schema) -> dict:  # type: ignore[valid-type]
        with db_session() as conn:
            record = update_record(
                conn,
                table=table,
                entity_type=entity_type,
                record_id=record_id,
                payload=payload.model_dump(exclude_unset=True),
            )
        if record is None:
            raise HTTPException(status_code=404, detail=f"{entity_type} not found")
        return {"ok": True, "data": record}

    @router.post("/{record_id}/void")
    def void_endpoint(record_id: int) -> dict:
        with db_session() as conn:
            record = void_record(conn, table=table, entity_type=entity_type, record_id=record_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"{entity_type} not found")
        return {"ok": True, "data": record}

    return router
