from datetime import datetime, timezone
import json
import sqlite3
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def insert_audit_log(
    conn: sqlite3.Connection,
    *,
    entity_type: str,
    entity_id: int | None,
    action: str,
    actor: str = "system",
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    created_at = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO audit_logs (entity_type, entity_id, action, actor, detail, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (entity_type, entity_id, action, actor, json.dumps(detail or {}, ensure_ascii=True), created_at),
    )
    return get_audit_log(conn, cursor.lastrowid)


def get_audit_log(conn: sqlite3.Connection, audit_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM audit_logs WHERE id = ?", (audit_id,)).fetchone()
    data = row_to_dict(row)
    if data is None:
        raise LookupError("audit log not found")
    return data


def list_audit_logs(conn: sqlite3.Connection, limit: int = 100) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return rows_to_dicts(rows)


def list_records(
    conn: sqlite3.Connection,
    *,
    table: str,
    search_columns: list[str] | None = None,
    q: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    sql = f"SELECT * FROM {table}"
    params: list[Any] = []
    if q and search_columns:
        where = " OR ".join(f"{column} LIKE ?" for column in search_columns)
        sql += f" WHERE {where}"
        params.extend([f"%{q}%"] * len(search_columns))
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    return rows_to_dicts(conn.execute(sql, params).fetchall())


def get_record(conn: sqlite3.Connection, *, table: str, record_id: int) -> dict[str, Any] | None:
    return row_to_dict(conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone())


def create_record(
    conn: sqlite3.Connection,
    *,
    table: str,
    entity_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    timestamp = now_iso()
    data = {**payload, "created_at": timestamp, "updated_at": timestamp}
    columns = list(data.keys())
    placeholders = ", ".join("?" for _ in columns)
    cursor = conn.execute(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
        [data[column] for column in columns],
    )
    record = get_record(conn, table=table, record_id=cursor.lastrowid)
    insert_audit_log(conn, entity_type=entity_type, entity_id=cursor.lastrowid, action="create", detail=record)
    return record or {}


def update_record(
    conn: sqlite3.Connection,
    *,
    table: str,
    entity_type: str,
    record_id: int,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    if not payload:
        return get_record(conn, table=table, record_id=record_id)
    data = {**payload, "updated_at": now_iso()}
    assignments = ", ".join(f"{column} = ?" for column in data)
    values = [data[column] for column in data]
    values.append(record_id)
    result = conn.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", values)
    if result.rowcount == 0:
        return None
    record = get_record(conn, table=table, record_id=record_id)
    insert_audit_log(conn, entity_type=entity_type, entity_id=record_id, action="update", detail=payload)
    return record


def void_record(
    conn: sqlite3.Connection,
    *,
    table: str,
    entity_type: str,
    record_id: int,
) -> dict[str, Any] | None:
    result = conn.execute(
        f"UPDATE {table} SET status = ?, updated_at = ? WHERE id = ?",
        ("void", now_iso(), record_id),
    )
    if result.rowcount == 0:
        return None
    record = get_record(conn, table=table, record_id=record_id)
    insert_audit_log(conn, entity_type=entity_type, entity_id=record_id, action="void", detail=record)
    return record
