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
    if table in ("contracts", "projects", "signoffs", "purchases"):
        # 這些都靠 case_id 掛在案件上 → 依案件歸屬隔離（承辦只看自己案件下的）。
        # 預算(budgets) 不在此列：預算是全公司資料，不做 owner 隔離。
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

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_code TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT '',
    unit_name TEXT NOT NULL DEFAULT '',
    fiscal_year TEXT NOT NULL DEFAULT '',
    amount REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    case_id INTEGER,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code TEXT NOT NULL UNIQUE,
    project_name TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '',
    necessity TEXT NOT NULL DEFAULT '',
    progress REAL NOT NULL DEFAULT 0,
    owner TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    case_id INTEGER,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS signoffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signoff_code TEXT NOT NULL UNIQUE,
    subject TEXT NOT NULL,
    applicant TEXT NOT NULL DEFAULT '',
    amount REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    sign_date TEXT NOT NULL DEFAULT '',
    case_id INTEGER,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_code TEXT NOT NULL UNIQUE,
    item_name TEXT NOT NULL,
    vendor_name TEXT NOT NULL DEFAULT '',
    quantity REAL NOT NULL DEFAULT 0,
    amount REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    case_id INTEGER,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    role_code TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL DEFAULT '',
    disabled INTEGER NOT NULL DEFAULT 0,
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
        "status": {"draft", "pending_review", "reviewing", "approved", "disabled"},
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
    "budgets": {
        "status": {"active", "closed", "disabled"},
    },
    "projects": {
        "status": {"active", "completed", "paused", "disabled"},
    },
    "signoffs": {
        "status": {"draft", "submitted", "approved", "rejected", "disabled"},
    },
    "purchases": {
        "status": {"pending", "ordered", "arrived", "closed", "disabled"},
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
        ensure_column(conn, "cases", "due_date", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "cases", "created_by", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "cases", "approved_by", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "cases", "approved_at", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "contracts", "end_date", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "projects", "due_date", "TEXT NOT NULL DEFAULT ''")
        # 專案：對齊真實 Excel 欄位
        ensure_column(conn, "projects", "level", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "projects", "progress_planned", "REAL NOT NULL DEFAULT 0")
        ensure_column(conn, "projects", "rag_status", "TEXT NOT NULL DEFAULT ''")
        # 付款(核銷)：對齊真實費用整合表欄位
        for col in ("item", "settle_no", "ref_no", "period", "billing_period",
                    "settled_by", "vendor", "approval_level", "owner", "owner_email"):
            ensure_column(conn, "payments", col, "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "payments", "net_amount", "REAL NOT NULL DEFAULT 0")
        ensure_column(conn, "payments", "tax_amount", "REAL NOT NULL DEFAULT 0")


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


_FK_REFS = {"case_id": ("cases", "案件"), "contract_id": ("contracts", "合約")}


def _validate_fks(conn: sqlite3.Connection, fields: dict[str, Any]) -> None:
    """關聯 ID（case_id / contract_id）若有填，必須指向存在的資料，否則擋下。"""
    for fk, (ref_table, label) in _FK_REFS.items():
        val = fields.get(fk)
        if val is None:
            continue
        if conn.execute(f"SELECT 1 FROM {ref_table} WHERE id = ?", (val,)).fetchone() is None:
            raise ValueError(f"關聯的{label} ID {val} 不存在，請確認後再填。")


def insert_row(table: str, payload: dict[str, Any]) -> dict[str, Any]:
    scope = _owner_scope.get()
    if table == "cases":
        payload = {**payload, "created_by": _current_actor.get()}  # 記錄建立者，供雙人複核擋自己核自己
        if scope is not None:
            payload = {**payload, "owner": scope}  # 承辦建案自動歸自己
    allowed = allowed_fields()
    fields = {key: value for key, value in payload.items() if key in allowed[table]}
    if not fields:
        raise ValueError("No valid fields supplied.")
    validate_status_fields(table, fields)
    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    with connect() as conn:
        _validate_fks(conn, fields)
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
        "cases": {"case_code", "title", "owner", "status", "amount", "risk_level", "note", "next_step", "due_date", "created_by"},
        "contracts": {"contract_code", "contract_name", "vendor_name", "amount", "status", "case_id", "end_date"},
        "payments": {"contract_id", "payment_month", "payment_amount", "invoice_status", "status",
                     "item", "settle_no", "ref_no", "period", "billing_period", "settled_by",
                     "vendor", "approval_level", "owner", "owner_email", "net_amount", "tax_amount"},
        "documents": {"file_name", "document_type", "source_note", "status", "case_id", "contract_id"},
        "budgets": {"budget_code", "category", "unit_name", "fiscal_year", "amount", "status", "case_id", "note"},
        "projects": {"project_code", "project_name", "source", "necessity", "progress", "owner", "status", "case_id", "due_date", "note",
                     "level", "progress_planned", "rag_status"},
        "signoffs": {"signoff_code", "subject", "applicant", "amount", "status", "sign_date", "case_id", "note"},
        "purchases": {"purchase_code", "item_name", "vendor_name", "quantity", "amount", "status", "case_id", "note"},
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
    "budgets": {"case_id"},
    "projects": {"case_id"},
    "signoffs": {"case_id"},
    "purchases": {"case_id"},
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
        _validate_fks(conn, fields)
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


def submit_case(case_id: int) -> dict[str, Any]:
    """送出複核：draft/reviewing -> pending_review。承辦可送自己的（套 owner 範圍）。"""
    scope = _owner_scope.get()
    with connect() as conn:
        before = get_row(conn, "cases", case_id)
        if scope is not None and not _row_in_scope(conn, "cases", case_id, scope):
            raise LookupError(f"cases row {case_id} not found")  # 非本人範圍，視同不存在
        if before["status"] not in ("draft", "reviewing"):
            raise RuntimeError(f"案件目前狀態為 {before['status']}，無法送出複核。")
        conn.execute("UPDATE cases SET status = 'pending_review' WHERE id = ?", (case_id,))
        after = get_row(conn, "cases", case_id)
        write_audit_log(conn, "cases", case_id, "submit", before, after)
        return after


def approve_case(case_id: int, approver: str) -> dict[str, Any]:
    """核准：pending_review -> approved。雙人複核鐵則——建立者不得核准自己的案件。
    （角色限制「只有助理/主管可核」在 API 層擋；此處核准者看全部，不套 owner 範圍。）"""
    with connect() as conn:
        before = get_row(conn, "cases", case_id)
        if before["status"] != "pending_review":
            raise RuntimeError(f"案件目前狀態為 {before['status']}，只有『待複核』能核准。")
        if (before.get("created_by") or "") == approver:
            raise PermissionError("不能核准自己建立的案件，需由另一人複核。")
        conn.execute(
            "UPDATE cases SET status = 'approved', approved_by = ?, approved_at = datetime('now') WHERE id = ?",
            (approver, case_id),
        )
        after = get_row(conn, "cases", case_id)
        write_audit_log(conn, "cases", case_id, "approve", before, after)
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


def confirm_import_batch_cases_write(
    batch_id: int,
    confirmed_fields: list[dict[str, Any]],
) -> dict[str, Any]:
    """正式寫入案件。安全閘門：
    - 先跑與 dry-run 相同的驗證（零錯誤、確認齊、批內無重複）→ 任一不過即 raise，完全不寫。
    - 單一交易：全部成功才 commit，中途出錯整批回滾。
    - 冪等：案件編號已存在則跳過（不覆蓋），可安全重跑。
    - 來源舉證：逐列寫稽核，記 batch_id / row_number / source_row_id / actor。
    """
    actor = _current_actor.get()
    with connect() as conn:
        batch = get_row(conn, "import_batches", batch_id)
        rows = conn.execute(
            "SELECT * FROM import_rows WHERE batch_id = ? ORDER BY row_number ASC, id ASC",
            (batch_id,),
        ).fetchall()
        preview = mapping_preview(batch, rows)
        # 用空的 existing 驗證：批內錯誤/確認/重複要擋，但既有編號改為逐列冪等跳過而非整批拒絕。
        plan = confirm_cases_dry_run_plan(preview, confirmed_fields, set())
        existing = {
            str(r["case_code"]).strip() for r in conn.execute("SELECT case_code FROM cases").fetchall()
        }
        created: list[str] = []
        skipped: list[str] = []
        for item in plan["plan"]["cases"]:
            record = item["record"]
            code = str(record.get("case_code", "")).strip()
            if not code or code in existing:
                skipped.append(code)
                continue
            fields = {k: record[k] for k in ("case_code", "title", "owner", "amount") if k in record}
            fields["created_by"] = actor
            columns = ", ".join(fields)
            placeholders = ", ".join("?" for _ in fields)
            cursor = conn.execute(
                f"INSERT INTO cases ({columns}) VALUES ({placeholders})", list(fields.values())
            )
            row_id = cursor.lastrowid
            after = get_row(conn, "cases", row_id)
            write_audit_log(conn, "cases", row_id, "import", None, {
                **after,
                "import_batch_id": batch_id,
                "import_row_number": item["row_number"],
                "import_source_row_id": item["source_row_id"],
            })
            existing.add(code)
            created.append(code)
        conn.execute("UPDATE import_batches SET status = 'committed' WHERE id = ?", (batch_id,))
        return {
            "dry_run": False,
            "committed": True,
            "batch_id": batch_id,
            "created": created,
            "skipped": skipped,
            "created_count": len(created),
            "skipped_count": len(skipped),
        }


def parse_projects_xlsx(data: bytes) -> list[dict[str, Any]]:
    """解析『處級專案進度追蹤總表』格式的 .xlsx → 專案清單。
    規則：找含「專案名稱」的表頭列；其後每一列若『專案名稱』非空＝一個專案
    （空的是工作子項，先略過）。多工作表全部合併，每張表當一個『組別』。
    進度值 <=1 視為小數比例（0.294→29%）。標號僅每張表內序號，故 code 用 組別-標號。"""
    import io
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out: list[dict[str, Any]] = []
    try:
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            rows = list(ws.iter_rows(values_only=True))
            header_idx = None
            for i, r in enumerate(rows[:6]):
                if r and any(str(c).replace("\n", "") == "專案名稱" for c in r if c is not None):
                    header_idx = i
                    break
            if header_idx is None:
                continue
            seq = 0  # 每張表的流水序號，避免標號在同表重複造成 code 撞號
            for r in rows[header_idx + 1:]:
                if not r or len(r) < 2 or r[1] is None or not str(r[1]).strip():
                    continue

                def pct(v: Any) -> float:
                    if v is None or v == "":
                        return 0.0
                    try:
                        f = float(v)
                    except (TypeError, ValueError):
                        return 0.0
                    return round(f * 100, 1) if f <= 1 else round(f, 1)

                seq += 1
                out.append({
                    "project_code": f"{sheet}-{seq}",
                    "project_name": str(r[1]).strip(),
                    "source": sheet,
                    "necessity": str(r[2]).strip() if len(r) > 2 and r[2] else "",
                    "progress_planned": pct(r[3] if len(r) > 3 else None),
                    "progress": pct(r[4] if len(r) > 4 else None),
                    "rag_status": str(r[5]).strip() if len(r) > 5 and r[5] and str(r[5]).strip() else "",
                })
    finally:
        wb.close()
    return out


def commit_projects_import(records: list[dict[str, Any]]) -> dict[str, Any]:
    """把解析出的專案寫入 projects：單一交易、冪等（project_code 已存在則跳過）、逐列稽核。"""
    actor = _current_actor.get()
    fields_allowed = allowed_fields()["projects"]
    with connect() as conn:
        existing = {r["project_code"] for r in conn.execute("SELECT project_code FROM projects").fetchall()}
        created: list[str] = []
        skipped: list[str] = []
        for rec in records:
            code = rec.get("project_code", "").strip()
            if not code or code in existing:
                skipped.append(code)
                continue
            fields = {k: v for k, v in rec.items() if k in fields_allowed}
            columns = ", ".join(fields)
            placeholders = ", ".join("?" for _ in fields)
            cur = conn.execute(f"INSERT INTO projects ({columns}) VALUES ({placeholders})", list(fields.values()))
            after = get_row(conn, "projects", cur.lastrowid)
            write_audit_log(conn, "projects", cur.lastrowid, "import", None, {**after, "import_source": "xlsx"})
            existing.add(code)
            created.append(code)
        return {"created_count": len(created), "skipped_count": len(skipped), "created": created}


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


def overdue_reminders(within_days: int = 14) -> list[dict[str, Any]]:
    """催辦清單：逾期或即將到期、但尚未完成的『案件』與『合約』，供主動提醒。
    - 案件：有預計完成日(due_date) 且未核准/未作廢。
    - 合約：有到期日(end_date) 且未作廢。
    依 owner 範圍過濾（承辦只看自己的）。逾期(date<今天)標 overdue，其餘標 soon。"""
    scope = _owner_scope.get()
    today = date.today()
    today_s = today.isoformat()
    horizon = (today + timedelta(days=within_days)).isoformat()

    def _days(date_str: str) -> int:
        try:
            return (date.fromisoformat(date_str) - today).days
        except ValueError:
            return 0

    items: list[dict[str, Any]] = []
    with connect() as conn:
        # 案件：未完成且有預計完成日
        c_where = "due_date <> '' AND due_date <= ? AND status NOT IN ('approved', 'disabled')"
        c_params: list[Any] = [horizon]
        if scope is not None:
            c_where = f"({c_where}) AND owner = ?"
            c_params.append(scope)
        for r in conn.execute(
            f"SELECT id, case_code, title, owner, due_date, status FROM cases WHERE {c_where} ORDER BY due_date ASC LIMIT 100",
            c_params,
        ).fetchall():
            items.append({
                "type": "case", "id": r["id"], "code": r["case_code"], "title": r["title"],
                "owner": r["owner"], "date": r["due_date"], "status": r["status"],
                "days": _days(r["due_date"]), "severity": "overdue" if r["due_date"] < today_s else "soon",
            })

        # 專案：未完成且有預計完成日（比照案件納入催辦）
        pj_where = "due_date <> '' AND due_date <= ? AND status NOT IN ('completed', 'disabled')"
        pj_params: list[Any] = [horizon]
        if scope is not None:
            sw, sp = _scope_where("projects", scope)
            if sw:
                pj_where = f"({pj_where}) AND {sw}"
                pj_params += sp
        for r in conn.execute(
            f"SELECT id, project_code, project_name, owner, due_date, status FROM projects WHERE {pj_where} ORDER BY due_date ASC LIMIT 100",
            pj_params,
        ).fetchall():
            items.append({
                "type": "project", "id": r["id"], "code": r["project_code"], "title": r["project_name"],
                "owner": r["owner"], "date": r["due_date"], "status": r["status"],
                "days": _days(r["due_date"]), "severity": "overdue" if r["due_date"] < today_s else "soon",
            })

        # 合約：未作廢且有到期日
        k_where = "k.end_date <> '' AND k.end_date <= ? AND k.status <> 'disabled'"
        k_params: list[Any] = [horizon]
        if scope is not None:
            sw, sp = _scope_where("contracts", scope)
            if sw:
                k_where = f"({k_where}) AND {sw.replace('case_id', 'k.case_id')}"
                k_params += sp
        for r in conn.execute(
            "SELECT k.id, k.contract_code, k.contract_name, c.owner, k.end_date, k.status "
            f"FROM contracts k LEFT JOIN cases c ON c.id = k.case_id WHERE {k_where} ORDER BY k.end_date ASC LIMIT 100",
            k_params,
        ).fetchall():
            items.append({
                "type": "contract", "id": r["id"], "code": r["contract_code"], "title": r["contract_name"],
                "owner": r["owner"], "date": r["end_date"], "status": r["status"],
                "days": _days(r["end_date"]), "severity": "overdue" if r["end_date"] < today_s else "soon",
            })

    items.sort(key=lambda x: x["date"])
    return items


def orphan_payments() -> list[dict[str, Any]]:
    """未歸戶付款：所屬合約沒有掛案件（case_id 為空）→ 沒人追、CIO 也看不到。給主管檢視。"""
    with connect() as conn:
        return conn.execute(
            "SELECT p.id, p.payment_month, p.payment_amount, p.status, k.contract_code "
            "FROM payments p JOIN contracts k ON k.id = p.contract_id "
            "WHERE k.case_id IS NULL AND p.status <> 'disabled' ORDER BY p.id DESC LIMIT 100"
        ).fetchall()


def pending_approvals() -> list[dict[str, Any]]:
    """待我複核：狀態為 pending_review 且非我建立的案件（雙人複核，不能核自己的）。"""
    actor = _current_actor.get()
    with connect() as conn:
        return conn.execute(
            "SELECT id, case_code, title, owner, amount, created_by FROM cases "
            "WHERE status = 'pending_review' AND created_by <> ? ORDER BY id DESC LIMIT 100",
            (actor,),
        ).fetchall()


# 雙人複核規則 (b)：核准前不算數 —— CIO 畫面的金額只計「已核准」案件下的付款。
_APPROVED_PAYMENT_CLAUSE = (
    "contract_id IN (SELECT id FROM contracts WHERE case_id IN "
    "(SELECT id FROM cases WHERE status = 'approved'))"
)


def cio_overview() -> dict[str, Any]:
    """CIO 決策總覽：大方向資金（下月應付 / 要準備的資金）+ 下月要出的款（可下探至案件）。
    金額只算『已核准』案件（未複核的錢不讓 CIO 看到當真）；並依 owner 範圍過濾。"""
    scope = _owner_scope.get()
    today = date.today()
    this_month = today.strftime("%Y-%m")
    if today.month == 12:
        next_month = f"{today.year + 1}-01"
    else:
        next_month = f"{today.year}-{today.month + 1:02d}"

    pw, pp = _scope_where("payments", scope) if scope is not None else ("", [])
    tail = f" AND {pw}" if pw else ""
    approved = f" AND {_APPROVED_PAYMENT_CLAUSE}"  # 只算已核准案件的付款

    with connect() as conn:
        def _sum(cond: str, params: list[Any]) -> float:
            return conn.execute(
                f"SELECT COALESCE(SUM(payment_amount), 0) AS s FROM payments WHERE {cond}",
                params,
            ).fetchone()["s"]

        next_month_total = _sum(f"payment_month = ?{tail}{approved}", [next_month, *pp])
        this_month_total = _sum(f"payment_month = ?{tail}{approved}", [this_month, *pp])
        funds_to_prepare = _sum(f"status <> 'closed'{tail}{approved}", [*pp])  # 尚未結案 = 要準備的資金

        # D：未來 6 個月現金流預測（含本月），只算已核准案件的付款
        forecast = []
        y, m = today.year, today.month
        for _ in range(6):
            mon = f"{y}-{m:02d}"
            forecast.append({"month": mon, "total": _sum(f"payment_month = ?{tail}{approved}", [mon, *pp])})
            m = 1 if m == 12 else m + 1
            y = y + 1 if m == 1 else y

        # 下月要出的每一筆款，連到所屬案件（供 CIO 逐層下探）；只列已核准案件。
        # budget_links=0 代表案件沒關聯任何預算 → 視為「預算外/計畫外」支出。
        # E：case_budget_total>0 且 案件付款合計>預算合計 → 超支。
        detail_sql = (
            "SELECT c.id AS case_id, c.case_code, c.title AS case_title, c.owner, "
            "k.contract_code, p.payment_month, p.payment_amount, p.status, "
            "(SELECT COUNT(*) FROM budgets b WHERE b.case_id = c.id AND b.status <> 'disabled') AS budget_links, "
            "(SELECT COALESCE(SUM(b.amount),0) FROM budgets b WHERE b.case_id = c.id AND b.status <> 'disabled') AS case_budget_total, "
            "(SELECT COALESCE(SUM(pp.payment_amount),0) FROM payments pp JOIN contracts kk ON kk.id = pp.contract_id WHERE kk.case_id = c.id) AS case_payment_total "
            "FROM payments p JOIN contracts k ON k.id = p.contract_id "
            "JOIN cases c ON c.id = k.case_id WHERE p.payment_month = ? AND c.status = 'approved'"
        )
        detail_params: list[Any] = [next_month]
        if scope is not None:
            detail_sql += " AND c.owner = ?"
            detail_params.append(scope)
        detail_sql += " ORDER BY p.payment_amount DESC LIMIT 100"
        upcoming = []
        unplanned_total = 0.0
        overspent_count = 0
        for r in conn.execute(detail_sql, detail_params).fetchall():
            item = dict(r)
            item["unplanned"] = (r["budget_links"] or 0) == 0  # 無對應預算＝計畫外
            item["overspent"] = (r["case_budget_total"] or 0) > 0 and (r["case_payment_total"] or 0) > r["case_budget_total"]
            if item["unplanned"]:
                unplanned_total += r["payment_amount"]
            if item["overspent"]:
                overspent_count += 1
            upcoming.append(item)

    return {
        "this_month": this_month,
        "next_month": next_month,
        "next_month_total": next_month_total,
        "this_month_total": this_month_total,
        "funds_to_prepare": funds_to_prepare,
        "unplanned_next_month": unplanned_total,  # 下月「預算外/計畫外」金額
        "overspent_count": overspent_count,       # 下月清單中超支案件數
        "forecast": forecast,                     # 未來 6 個月現金流
        "upcoming_next_month": upcoming,
    }


def get_db_user(username: str) -> dict[str, Any] | None:
    with connect() as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def list_db_users() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT username, role_code, display_name, email, disabled FROM users ORDER BY username").fetchall()
    return rows


def create_db_user(username: str, role_code: str, display_name: str, email: str, password_hash: str) -> None:
    with connect() as conn:
        if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            raise ValueError(f"帳號 {username} 已存在。")
        conn.execute(
            "INSERT INTO users(username, role_code, display_name, email, password_hash) VALUES(?,?,?,?,?)",
            (username, role_code, display_name, email, password_hash),
        )


def update_db_user(username: str, fields: dict[str, Any]) -> None:
    allowed = {"role_code", "display_name", "email", "disabled", "password_hash"}
    sets = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not sets:
        return
    assignments = ", ".join(f"{k} = ?" for k in sets)
    with connect() as conn:
        cur = conn.execute(f"UPDATE users SET {assignments} WHERE username = ?", [*sets.values(), username])
        if cur.rowcount == 0:
            raise LookupError(f"帳號 {username} 不存在。")


def delete_db_user(username: str) -> None:
    with connect() as conn:
        cur = conn.execute("DELETE FROM users WHERE username = ?", (username,))
        if cur.rowcount == 0:
            raise LookupError(f"帳號 {username} 不存在。")


def backup_database(dest_path: str) -> None:
    """用 SQLite 線上備份 API 把整個資料庫複製到 dest_path（即使有連線也一致）。"""
    with connect() as src:
        dst = sqlite3.connect(dest_path)
        try:
            src.backup(dst)
        finally:
            dst.close()


def read_setting(key: str, default: str = "") -> str:
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def read_settings(keys: list[str]) -> dict[str, str]:
    with connect() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    have = {r["key"]: r["value"] for r in rows}
    return {k: have.get(k, "") for k in keys}


def write_settings(values: dict[str, str]) -> None:
    """upsert 一批設定。空字串代表清空該鍵；未出現的鍵不動。"""
    with connect() as conn:
        for key, value in values.items():
            conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
                (key, "" if value is None else str(value)),
            )


def search_records(query: str) -> list[dict[str, Any]]:
    pattern = f"%{query}%"
    scope = _owner_scope.get()
    results: list[dict[str, Any]] = []
    with connect() as conn:
        for table, fields in {
            "case": ("cases", "case_code", "title", "owner"),
            "contract": ("contracts", "contract_code", "contract_name", "vendor_name"),
            "document": ("documents", "file_name", "document_type", "source_note"),
            "budget": ("budgets", "budget_code", "category", "unit_name"),
            "project": ("projects", "project_code", "project_name", "source"),
            "signoff": ("signoffs", "signoff_code", "subject", "applicant"),
            "purchase": ("purchases", "purchase_code", "item_name", "vendor_name"),
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
        # 追查「這筆費用對應的預算/專案/簽呈/請購」——CIO 下探時要看得到整條控管鏈
        budgets = conn.execute("SELECT * FROM budgets WHERE case_id = ? ORDER BY id DESC", (case_id,)).fetchall()
        projects = conn.execute("SELECT * FROM projects WHERE case_id = ? ORDER BY id DESC", (case_id,)).fetchall()
        signoffs = conn.execute("SELECT * FROM signoffs WHERE case_id = ? ORDER BY id DESC", (case_id,)).fetchall()
        purchases = conn.execute("SELECT * FROM purchases WHERE case_id = ? ORDER BY id DESC", (case_id,)).fetchall()
        return {
            "case": case,
            "contracts": contracts,
            "payments": payments,
            "documents": documents,
            "budgets": budgets,
            "projects": projects,
            "signoffs": signoffs,
            "purchases": purchases,
            "totals": {
                "contract_amount": sum(row["amount"] for row in contracts),
                "payment_amount": sum(row["payment_amount"] for row in payments),
                "document_count": len(documents),
                "budget_amount": sum(row["amount"] for row in budgets),
                "signoff_amount": sum(row["amount"] for row in signoffs),
                "purchase_amount": sum(row["amount"] for row in purchases),
            },
        }
