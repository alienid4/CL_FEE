from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, timedelta
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator

from app.import_mapping import confirm_cases_dry_run_plan, confirm_preflight_report, mapping_preview
from app.settings import get_settings


_current_actor: ContextVar[str] = ContextVar("current_actor", default="system")


def set_current_actor(actor: str) -> None:
    """記錄目前請求的操作者，供 write_audit_log 使用（由 API 層每個請求綁定）。"""
    _current_actor.set(actor)


_owner_scope: ContextVar[str | None] = ContextVar("owner_scope", default=None)


def set_owner_scope(scope: str | None) -> None:
    """設定資料列可視範圍：非 None(承辦帳號)時，只看 owner 屬此帳號的案件及其關聯資料。"""
    _owner_scope.set(scope)


def _scope_where(table: str, scope: str) -> tuple[str, list[Any]]:
    """把 table 限縮到 scope 擁有案件範圍的 (WHERE 片段, 參數)。"""
    owned = "SELECT id FROM cases WHERE owner = ?"
    if table == "cases":
        return "owner = ?", [scope]
    if table == "contracts":
        return f"case_id IN ({owned})", [scope]
    if table == "payments":
        return f"contract_id IN (SELECT id FROM contracts WHERE case_id IN ({owned}))", [scope]
    if table == "documents":
        return (
            f"(case_id IN ({owned}) OR contract_id IN "
            f"(SELECT id FROM contracts WHERE case_id IN ({owned})))",
            [scope, scope],
        )
    return "", []


def _row_in_scope(conn: sqlite3.Connection, table: str, row_id: int, scope: str) -> bool:
    """該列是否在 scope(承辦) 的可視範圍內。用於寫入(改/停用/刪)前的越權防護。"""
    where, params = _scope_where(table, scope)
    if not where:
        return True
    return conn.execute(
        f"SELECT 1 FROM {table} WHERE id = ? AND ({where}) LIMIT 1", [row_id, *params]
    ).fetchone() is not None


SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    owner TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    amount REAL NOT NULL DEFAULT 0,
    risk_level TEXT NOT NULL DEFAULT 'normal',
    note TEXT NOT NULL DEFAULT '',
    next_step TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_code TEXT NOT NULL UNIQUE,
    contract_name TEXT NOT NULL,
    vendor_name TEXT NOT NULL DEFAULT '',
    amount REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    case_id INTEGER,
    end_date TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    payment_month TEXT NOT NULL,
    payment_amount REAL NOT NULL,
    invoice_status TEXT NOT NULL DEFAULT 'not_received',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    document_type TEXT NOT NULL DEFAULT 'other',
    source_note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    case_id INTEGER,
    contract_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    row_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    before_json TEXT,
    after_json TEXT,
    actor TEXT NOT NULL DEFAULT 'local-dev',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    row_number INTEGER NOT NULL,
    raw_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'staged',
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


STATUS_VALUES: dict[str, dict[str, set[str]]] = {
    "cases": {
        "status": {"draft", "reviewing", "approved", "disabled"},
    },
    "contracts": {
        "status": {"active", "reviewing", "closed", "disabled"},
    },
    "payments": {
        "invoice_status": {"not_received", "received", "verified"},
        "status": {"pending", "scheduled", "closed", "disabled"},
    },
    "documents": {
        "status": {"active", "reviewing", "archived", "disabled"},
    },
}


def dict_row(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict[str, Any]:
    return {column[0]: row[index] for index, column in enumerate(cursor.description)}


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize_database() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        ensure_column(conn, "documents", "status", "TEXT NOT NULL DEFAULT 'active'")
        ensure_column(conn, "audit_logs", "actor", "TEXT NOT NULL DEFAULT 'local-dev'")
        ensure_column(conn, "cases", "note", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "cases", "next_step", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "contracts", "end_date", "TEXT NOT NULL DEFAULT ''")


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def insert_row(table: str, payload: dict[str, Any]) -> dict[str, Any]:
    scope = _owner_scope.get()
    if table == "cases" and scope is not None:
        payload = {**payload, "owner": scope}  # 承辦建案自動歸自己
    allowed = allowed_fields()
    fields = {key: value for key, value in payload.items() if key in allowed[table]}
    if not fields:
        raise ValueError("No valid fields supplied.")
    validate_status_fields(table, fields)
    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    with connect() as conn:
        cursor = conn.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            list(fields.values()),
        )
        row_id = cursor.lastrowid
        row = get_row(conn, table, row_id)
        write_audit_log(conn, table, row_id, "create", None, row)
        return row


def allowed_fields() -> dict[str, set[str]]:
    return {
        "cases": {"case_code", "title", "owner", "status", "amount", "risk_level", "note", "next_step"},
        "contracts": {"contract_code", "contract_name", "vendor_name", "amount", "status", "case_id", "end_date"},
        "payments": {"contract_id", "payment_month", "payment_amount", "invoice_status", "status"},
        "documents": {"file_name", "document_type", "source_note", "status", "case_id", "contract_id"},
    }


def validate_status_fields(table: str, fields: dict[str, Any]) -> None:
    for field, valid_values in STATUS_VALUES.get(table, {}).items():
        if field not in fields or fields[field] is None:
            continue
        value = str(fields[field])
        if value not in valid_values:
            allowed = ", ".join(sorted(valid_values))
            raise ValueError(f"Invalid {table}.{field}: {value}. Allowed values: {allowed}.")


def get_row(conn: sqlite3.Connection, table: str, row_id: int) -> dict[str, Any]:
    row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
    if row is None:
        raise LookupError(f"{table} row {row_id} not found")
    return row


NULLABLE_FIELDS: dict[str, set[str]] = {
    "contracts": {"case_id"},
    "documents": {"case_id", "contract_id"},
}


def update_row(table: str, row_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    scope = _owner_scope.get()
    allowed = allowed_fields()
    nullable = NULLABLE_FIELDS.get(table, set())
    # 允許把可為空的外鍵顯式清成 NULL（解除關聯）；其餘欄位仍略過 None。
    fields = {
        key: value
        for key, value in payload.items()
        if key in allowed[table] and (value is not None or key in nullable)
    }
    if scope is not None:
        fields.pop("owner", None)  # 承辦不得竄改案件歸屬（避免竊佔/送人）
    if not fields:
        raise ValueError("No valid fields supplied.")
    validate_status_fields(table, fields)
    assignments = ", ".join(f"{key} = ?" for key in fields)
    with connect() as conn:
        before = get_row(conn, table, row_id)
        if scope is not None and not _row_in_scope(conn, table, row_id, scope):
            raise LookupError(f"{table} row {row_id} not found")  # 非本人範圍，視同不存在
        cursor = conn.execute(
            f"UPDATE {table} SET {assignments} WHERE id = ?",
            [*fields.values(), row_id],
        )
        if cursor.rowcount == 0:
            raise LookupError(f"{table} row {row_id} not found")
        after = get_row(conn, table, row_id)
        write_audit_log(conn, table, row_id, "update", before, after)
        return after


def disable_row(table: str, row_id: int) -> dict[str, Any]:
    scope = _owner_scope.get()
    if "status" not in allowed_fields()[table]:
        raise ValueError(f"{table} does not support disable.")
    validate_status_fields(table, {"status": "disabled"})
    with connect() as conn:
        before = get_row(conn, table, row_id)
        if scope is not None and not _row_in_scope(conn, table, row_id, scope):
            raise LookupError(f"{table} row {row_id} not found")  # 非本人範圍，視同不存在
        cursor = conn.execute(f"UPDATE {table} SET status = ? WHERE id = ?", ("disabled", row_id))
        if cursor.rowcount == 0:
            raise LookupError(f"{table} row {row_id} not found")
        after = get_row(conn, table, row_id)
        write_audit_log(conn, table, row_id, "disable", before, after)
        return after


CHILD_REFS: dict[str, list[tuple[str, str]]] = {
    "cases": [("contracts", "case_id"), ("documents", "case_id")],
    "contracts": [("payments", "contract_id"), ("documents", "contract_id")],
}


def delete_row(table: str, row_id: int) -> None:
    scope = _owner_scope.get()
    with connect() as conn:
        before = get_row(conn, table, row_id)
        if scope is not None and not _row_in_scope(conn, table, row_id, scope):
            raise LookupError(f"{table} row {row_id} not found")  # 非本人範圍，視同不存在
        # 有子列關聯時不得硬刪（避免靜默孤立子列、金額短少）；請先處理或改用作廢。
        for child_table, fk in CHILD_REFS.get(table, []):
            count = conn.execute(
                f"SELECT COUNT(*) AS c FROM {child_table} WHERE {fk} = ?", (row_id,)
            ).fetchone()["c"]
            if count:
                raise RuntimeError(
                    f"仍有 {count} 筆 {child_table} 關聯此 {table}（id={row_id}），"
                    "請先處理關聯資料或改用作廢。"
                )
        cursor = conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
        if cursor.rowcount == 0:
            raise LookupError(f"{table} row {row_id} not found")
        write_audit_log(conn, table, row_id, "delete", before, None)


def list_rows(table: str, limit: int = 100) -> list[dict[str, Any]]:
    scope = _owner_scope.get()
    where, params = _scope_where(table, scope) if scope is not None else ("", [])
    sql = f"SELECT * FROM {table}"
    if where:
        sql += f" WHERE {where}"
    sql += " ORDER BY id DESC LIMIT ?"
    with connect() as conn:
        return conn.execute(sql, [*params, max(1, min(limit, 500))]).fetchall()


def create_import_batch(source_name: str, status: str = "created") -> dict[str, Any]:
    source = source_name.strip()
    if not source:
        raise ValueError("source_name is required.")
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO import_batches (source_name, status) VALUES (?, ?)",
            (source, status),
        )
        batch_id = cursor.lastrowid
        batch = get_row(conn, "import_batches", batch_id)
        write_audit_log(conn, "import_batches", batch_id, "create", None, batch)
        return batch


def stage_import_rows(batch_id: int, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        raise ValueError("rows must contain at least one row.")
    with connect() as conn:
        batch = get_row(conn, "import_batches", batch_id)
        staged: list[dict[str, Any]] = []
        for index, raw in enumerate(rows, start=1):
            cursor = conn.execute(
                "INSERT INTO import_rows (batch_id, row_number, raw_json, status, error_message) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    batch_id,
                    index,
                    json.dumps(raw, ensure_ascii=False, sort_keys=True),
                    "staged",
                    None,
                ),
            )
            staged.append(get_row(conn, "import_rows", cursor.lastrowid))
        after = {"batch": batch, "staged_row_count": len(staged)}
        write_audit_log(conn, "import_batches", batch_id, "stage_rows", None, after)
        return staged


def list_import_batches(limit: int = 100) -> list[dict[str, Any]]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM import_batches ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 500)),),
        ).fetchall()


def get_import_batch(batch_id: int) -> dict[str, Any]:
    with connect() as conn:
        batch = get_row(conn, "import_batches", batch_id)
        rows = conn.execute(
            "SELECT * FROM import_rows WHERE batch_id = ? ORDER BY row_number ASC, id ASC",
            (batch_id,),
        ).fetchall()
        return {"batch": batch, "rows": rows}


def list_import_rows(batch_id: int, limit: int = 500) -> list[dict[str, Any]]:
    with connect() as conn:
        get_row(conn, "import_batches", batch_id)
        return conn.execute(
            "SELECT * FROM import_rows WHERE batch_id = ? ORDER BY row_number ASC, id ASC LIMIT ?",
            (batch_id, max(1, min(limit, 500))),
        ).fetchall()


def preview_import_mapping(batch_id: int) -> dict[str, Any]:
    with connect() as conn:
        batch = get_row(conn, "import_batches", batch_id)
        rows = conn.execute(
            "SELECT * FROM import_rows WHERE batch_id = ? ORDER BY row_number ASC, id ASC",
            (batch_id,),
        ).fetchall()
        return mapping_preview(batch, rows)


def confirm_import_batch_cases_dry_run(
    batch_id: int,
    confirmed_fields: list[dict[str, Any]],
) -> dict[str, Any]:
    with connect() as conn:
        batch = get_row(conn, "import_batches", batch_id)
        rows = conn.execute(
            "SELECT * FROM import_rows WHERE batch_id = ? ORDER BY row_number ASC, id ASC",
            (batch_id,),
        ).fetchall()
        preview = mapping_preview(batch, rows)
        existing_case_codes = {
            str(row["case_code"]).strip()
            for row in conn.execute("SELECT case_code FROM cases").fetchall()
        }
        return confirm_cases_dry_run_plan(preview, confirmed_fields, existing_case_codes)


def preflight_import_batch_confirm(
    batch_id: int,
    confirmed_fields: list[dict[str, Any]],
    accepted_warning_codes: list[str],
) -> dict[str, Any]:
    with connect() as conn:
        batch = get_row(conn, "import_batches", batch_id)
        rows = conn.execute(
            "SELECT * FROM import_rows WHERE batch_id = ? ORDER BY row_number ASC, id ASC",
            (batch_id,),
        ).fetchall()
        preview = mapping_preview(batch, rows)
        existing_case_codes = {
            str(row["case_code"]).strip()
            for row in conn.execute("SELECT case_code FROM cases").fetchall()
        }
        return confirm_preflight_report(
            preview,
            confirmed_fields,
            accepted_warning_codes,
            existing_case_codes,
        )


def write_audit_log(
    conn: sqlite3.Connection,
    table: str,
    row_id: int,
    action: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    actor: str | None = None,
) -> None:
    if actor is None:
        actor = _current_actor.get()
    conn.execute(
        "INSERT INTO audit_logs (table_name, row_id, action, before_json, after_json, actor) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            table,
            row_id,
            action,
            json.dumps(before, ensure_ascii=False, sort_keys=True) if before is not None else None,
            json.dumps(after, ensure_ascii=False, sort_keys=True) if after is not None else None,
            actor,
        ),
    )


def list_audit_logs(
    limit: int = 100,
    table_name: str | None = None,
    row_id: int | None = None,
    action: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if table_name:
        clauses.append("table_name = ?")
        params.append(table_name)
    if row_id is not None:
        clauses.append("row_id = ?")
        params.append(row_id)
    if action:
        clauses.append("action = ?")
        params.append(action)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 500)))
    with connect() as conn:
        return conn.execute(
            f"SELECT * FROM audit_logs {where} ORDER BY id DESC LIMIT ?",
            params,
        ).fetchall()


def dashboard_summary() -> dict[str, Any]:
    scope = _owner_scope.get()

    def _clause(table: str) -> tuple[str, list[Any]]:
        if scope is None:
            return "", []
        where, params = _scope_where(table, scope)
        return (f" WHERE {where}" if where else ""), params

    with connect() as conn:
        counts = {}
        for table in ("cases", "contracts", "payments", "documents"):
            clause, params = _clause(table)
            counts[table] = conn.execute(
                f"SELECT COUNT(*) AS count FROM {table}{clause}", params
            ).fetchone()["count"]
        c_clause, c_params = _clause("contracts")
        money = conn.execute(
            f"SELECT COALESCE(SUM(amount), 0) AS contract_amount FROM contracts{c_clause}", c_params
        ).fetchone()
        p_where, p_params = _scope_where("payments", scope) if scope is not None else ("", [])
        due_sql = (
            "SELECT COALESCE(SUM(payment_amount), 0) AS pending_payment_amount "
            "FROM payments WHERE status <> 'closed'"
        )
        if p_where:
            due_sql += f" AND {p_where}"
        due = conn.execute(due_sql, p_params).fetchone()
        return {
            "counts": counts,
            "contract_amount": money["contract_amount"],
            "pending_payment_amount": due["pending_payment_amount"],
        }


def monthly_spending_summary() -> list[dict[str, Any]]:
    """依月份彙總付款：每月總額、已付(closed)、待付(其餘)、筆數。依 owner 範圍過濾。"""
    scope = _owner_scope.get()
    where, params = _scope_where("payments", scope) if scope is not None else ("", [])
    sql = (
        "SELECT payment_month AS month, COUNT(*) AS count, "
        "COALESCE(SUM(payment_amount), 0) AS total, "
        "COALESCE(SUM(CASE WHEN status = 'closed' THEN payment_amount ELSE 0 END), 0) AS paid, "
        "COALESCE(SUM(CASE WHEN status <> 'closed' THEN payment_amount ELSE 0 END), 0) AS pending "
        "FROM payments"
    )
    if where:
        sql += f" WHERE {where}"
    sql += " GROUP BY payment_month ORDER BY payment_month DESC"
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


def cases_needing_attention() -> list[dict[str, Any]]:
    """需處理案件：未作廢，且(審核中 或 有填下一步)。承辦只看自己的。"""
    scope = _owner_scope.get()
    where = "status <> 'disabled' AND (status = 'reviewing' OR TRIM(next_step) <> '')"
    params: list[Any] = []
    if scope is not None:
        where = f"({where}) AND owner = ?"
        params.append(scope)
    with connect() as conn:
        return conn.execute(
            "SELECT id, case_code, title, status, note, next_step, owner, amount "
            f"FROM cases WHERE {where} ORDER BY id DESC LIMIT 100",
            params,
        ).fetchall()


def expiring_contracts(within_days: int = 90) -> list[dict[str, Any]]:
    """快到期或已過期的合約：有到期日且 <= 今天+within_days，未作廢。承辦只看自己案件下的。"""
    scope = _owner_scope.get()
    threshold = (date.today() + timedelta(days=within_days)).isoformat()
    where = "end_date <> '' AND end_date <= ? AND status <> 'disabled'"
    params: list[Any] = [threshold]
    if scope is not None:
        sw, sp = _scope_where("contracts", scope)
        if sw:
            where = f"({where}) AND {sw}"
            params += sp
    with connect() as conn:
        return conn.execute(
            f"SELECT * FROM contracts WHERE {where} ORDER BY end_date ASC LIMIT 100",
            params,
        ).fetchall()


def cio_overview() -> dict[str, Any]:
    """CIO 決策總覽：大方向資金（下月應付 / 要準備的資金）+ 下月要出的款（可下探至案件）。
    依 owner 範圍過濾（CIO/主管 scope=None 看全部；承辦只看自己案件下的付款）。"""
    scope = _owner_scope.get()
    today = date.today()
    this_month = today.strftime("%Y-%m")
    if today.month == 12:
        next_month = f"{today.year + 1}-01"
    else:
        next_month = f"{today.year}-{today.month + 1:02d}"

    pw, pp = _scope_where("payments", scope) if scope is not None else ("", [])
    tail = f" AND {pw}" if pw else ""

    with connect() as conn:
        def _sum(cond: str, params: list[Any]) -> float:
            return conn.execute(
                f"SELECT COALESCE(SUM(payment_amount), 0) AS s FROM payments WHERE {cond}",
                params,
            ).fetchone()["s"]

        next_month_total = _sum(f"payment_month = ?{tail}", [next_month, *pp])
        this_month_total = _sum(f"payment_month = ?{tail}", [this_month, *pp])
        funds_to_prepare = _sum(f"status <> 'closed'{tail}", [*pp])  # 尚未結案 = 要準備的資金

        # 下月要出的每一筆款，連到所屬案件（供 CIO 逐層下探）
        detail_sql = (
            "SELECT c.id AS case_id, c.case_code, c.title AS case_title, c.owner, "
            "k.contract_code, p.payment_month, p.payment_amount, p.status "
            "FROM payments p JOIN contracts k ON k.id = p.contract_id "
            "JOIN cases c ON c.id = k.case_id WHERE p.payment_month = ?"
        )
        detail_params: list[Any] = [next_month]
        if scope is not None:
            detail_sql += " AND c.owner = ?"
            detail_params.append(scope)
        detail_sql += " ORDER BY p.payment_amount DESC LIMIT 100"
        upcoming = conn.execute(detail_sql, detail_params).fetchall()

    return {
        "this_month": this_month,
        "next_month": next_month,
        "next_month_total": next_month_total,
        "this_month_total": this_month_total,
        "funds_to_prepare": funds_to_prepare,
        "upcoming_next_month": upcoming,
    }


def search_records(query: str) -> list[dict[str, Any]]:
    pattern = f"%{query}%"
    scope = _owner_scope.get()
    results: list[dict[str, Any]] = []
    with connect() as conn:
        for table, fields in {
            "case": ("cases", "case_code", "title", "owner"),
            "contract": ("contracts", "contract_code", "contract_name", "vendor_name"),
            "document": ("documents", "file_name", "document_type", "source_note"),
        }.items():
            source, code_field, title_field, extra_field = fields
            sql = (
                f"SELECT id, {code_field} AS code, {title_field} AS title, {extra_field} AS detail "
                f"FROM {source} WHERE ({code_field} LIKE ? OR {title_field} LIKE ? OR {extra_field} LIKE ?)"
            )
            params: list[Any] = [pattern, pattern, pattern]
            if scope is not None:
                sw, sp = _scope_where(source, scope)
                if sw:
                    sql += f" AND {sw}"
                    params += sp
            sql += " ORDER BY id DESC LIMIT 50"
            rows = conn.execute(sql, params).fetchall()
            results.extend({"type": table, **row} for row in rows)
    return results


def case_360(case_id: int) -> dict[str, Any]:
    scope = _owner_scope.get()
    with connect() as conn:
        case = get_row(conn, "cases", case_id)
        if scope is not None and case.get("owner") != scope:
            raise LookupError(f"cases row {case_id} not found")  # 非本人案件，視同不存在
        contracts = conn.execute("SELECT * FROM contracts WHERE case_id = ? ORDER BY id DESC", (case_id,)).fetchall()
        payments = conn.execute(
            "SELECT p.* FROM payments p JOIN contracts c ON c.id = p.contract_id "
            "WHERE c.case_id = ? ORDER BY p.payment_month DESC",
            (case_id,),
        ).fetchall()
        documents = conn.execute("SELECT * FROM documents WHERE case_id = ? ORDER BY id DESC", (case_id,)).fetchall()
        return {
            "case": case,
            "contracts": contracts,
            "payments": payments,
            "documents": documents,
            "totals": {
                "contract_amount": sum(row["amount"] for row in contracts),
                "payment_amount": sum(row["payment_amount"] for row in payments),
                "document_count": len(documents),
            },
        }
