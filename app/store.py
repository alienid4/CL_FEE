from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime, timedelta
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
    if table in ("contracts", "signoffs", "purchases"):
        # 這些靠 case_id 掛在案件上 → 依案件歸屬隔離（承辦只看自己案件下的）。
        # 專案(projects)、預算(budgets) 不在此列：是全公司共享資料，不管誰負責、大家都看得到（含承辦，才能維護）。
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

CREATE TABLE IF NOT EXISTS project_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    seq INTEGER NOT NULL DEFAULT 0,
    item_name TEXT NOT NULL DEFAULT '',
    owner TEXT NOT NULL DEFAULT '',
    start_date TEXT NOT NULL DEFAULT '',
    end_date TEXT NOT NULL DEFAULT '',
    exec_status TEXT NOT NULL DEFAULT '',
    sub_total INTEGER NOT NULL DEFAULT 0,
    sub_done INTEGER NOT NULL DEFAULT 0,
    progress REAL NOT NULL DEFAULT 0,
    rag TEXT NOT NULL DEFAULT '',
    risk_note TEXT NOT NULL DEFAULT '',
    decision_needed TEXT NOT NULL DEFAULT '',
    support_needed TEXT NOT NULL DEFAULT '',
    duration_days TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS budget_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_id INTEGER NOT NULL,
    seq INTEGER NOT NULL DEFAULT 0,
    unit_code TEXT NOT NULL DEFAULT '',
    unit_name TEXT NOT NULL DEFAULT '',
    share_pct REAL NOT NULL DEFAULT 0,
    amount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS unit_headcounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_code TEXT NOT NULL DEFAULT '',
    unit_name TEXT NOT NULL DEFAULT '',
    headcount INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 單位主檔（Step 2）：每個真實單位一個永不變的內部編號；代號/名稱都是別名。
-- 非破壞式：原始資料(budget_allocations/unit_headcounts)不動，讀取時經別名認到同一主檔。
CREATE TABLE IF NOT EXISTS unit_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_code TEXT NOT NULL DEFAULT '',
    canonical_name TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS unit_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    master_id INTEGER NOT NULL,
    alias_code TEXT NOT NULL DEFAULT '',
    alias_name TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alias_code, alias_name)
);

-- 單位裁決紀錄（防呆＋後悔藥）：每次合併/分開都留誰、何時、為什麼，
-- 並記 undo_ops（每個別名的前一個歸屬）以便逐筆復原。原始資料本就不動，這裡是決策層的可逆帳。
CREATE TABLE IF NOT EXISTS unit_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL DEFAULT '',
    reason TEXT NOT NULL DEFAULT '',
    actor TEXT NOT NULL DEFAULT '',
    detail_json TEXT NOT NULL DEFAULT '',
    undo_ops_json TEXT NOT NULL DEFAULT '',
    undone INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 按類別分攤基準（Phase 2）：一個「類別」（台股功能/複委託功能/台複共用…）底下，
-- 各單位的百分比（來源＝資訊架構部費用分攤表『對照』表 NEW 欄，每類加總=100%）。
CREATE TABLE IF NOT EXISTS category_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL DEFAULT '',
    unit_code TEXT NOT NULL DEFAULT '',
    unit_name TEXT NOT NULL DEFAULT '',
    share_pct REAL NOT NULL DEFAULT 0,
    source_file TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, unit_code, unit_name)
);

-- 名稱歸納（比照單位主檔）：把「中華電信/中華電」這種同一實體的不同寫法歸成一個。
-- kind＝case(案件名)/project(專案名)/vendor(廠商名)。canonical＝以誰為準；別名皆對到它。
CREATE TABLE IF NOT EXISTS name_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL DEFAULT '',
    canonical_name TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kind, canonical_name)
);

CREATE TABLE IF NOT EXISTS name_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    master_id INTEGER NOT NULL,
    kind TEXT NOT NULL DEFAULT '',
    alias_name TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kind, alias_name)
);

CREATE TABLE IF NOT EXISTS name_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL DEFAULT '',
    action TEXT NOT NULL DEFAULT '',
    reason TEXT NOT NULL DEFAULT '',
    actor TEXT NOT NULL DEFAULT '',
    detail_json TEXT NOT NULL DEFAULT '',
    undo_ops_json TEXT NOT NULL DEFAULT '',
    undone INTEGER NOT NULL DEFAULT 0,
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
        # 專案進度總表：起訖日（供甘特／落後天數計算）
        ensure_column(conn, "projects", "start_date", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "projects", "end_date", "TEXT NOT NULL DEFAULT ''")
        # 預算共同費用分攤：尾數承擔單位（整數化後湊不齊的尾數歸給哪個單位；空＝自動抓填寫部門）
        ensure_column(conn, "budgets", "remainder_unit_code", "TEXT NOT NULL DEFAULT ''")
        # 預算分攤方法：fixed(固定金額) / headcount(按人數) / category(按類別，Phase 2)
        ensure_column(conn, "budgets", "alloc_method", "TEXT NOT NULL DEFAULT 'fixed'")
        ensure_column(conn, "budgets", "alloc_category_kind", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "budgets", "alloc_category", "TEXT NOT NULL DEFAULT ''")
        # 記匯入來源檔名，讓單位撞名清單能指回是哪個 Excel（人類追資料來源）
        ensure_column(conn, "budget_allocations", "source_file", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "unit_headcounts", "source_file", "TEXT NOT NULL DEFAULT ''")
        # 簽呈附件參照：貼簽呈系統連結或檔案位置（勾稽用，不存 PDF 本身）
        ensure_column(conn, "signoffs", "attachment_ref", "TEXT NOT NULL DEFAULT ''")
        # 系統編號：案件領「所屬年度＋四位流水號」，各階段共用此尾碼做跨階段勾稽
        ensure_column(conn, "cases", "fiscal_year", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "cases", "seq", "INTEGER NOT NULL DEFAULT 0")
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


def get_working_year() -> str:
    """目前作業年度：新案件『所屬年度』的預設值（例如今年 8 月就開始編明年預算）。
    設定沒填則退回今年。"""
    v = read_settings(["working_year"]).get("working_year", "")
    if str(v).strip():
        return str(v).strip()
    import datetime
    return str(datetime.date.today().year)


def insert_row(table: str, payload: dict[str, Any]) -> dict[str, Any]:
    scope = _owner_scope.get()
    if table == "cases":
        payload = {**payload, "created_by": _current_actor.get()}  # 記錄建立者，供雙人複核擋自己核自己
        if scope is not None:
            payload = {**payload, "owner": scope}  # 承辦建案自動歸自己
        # 所屬年度預設＝作業年度；流水號在交易內配發（同年遞增）
        payload = {**payload, "fiscal_year": str(payload.get("fiscal_year") or "").strip() or get_working_year()}
    allowed = allowed_fields()
    fields = {key: value for key, value in payload.items() if key in allowed[table]}
    if not fields:
        raise ValueError("No valid fields supplied.")
    validate_status_fields(table, fields)
    with connect() as conn:
        if table == "cases":
            nxt = conn.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 AS n FROM cases WHERE fiscal_year = ?",
                (fields.get("fiscal_year", ""),)).fetchone()["n"]
            fields = {**fields, "seq": nxt}  # 案件年度流水號（四位尾碼＝案件身分證）
        columns = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)
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
        "cases": {"case_code", "title", "owner", "status", "amount", "risk_level", "note", "next_step", "due_date", "created_by", "fiscal_year", "seq"},
        "contracts": {"contract_code", "contract_name", "vendor_name", "amount", "status", "case_id", "end_date"},
        "payments": {"contract_id", "payment_month", "payment_amount", "invoice_status", "status",
                     "item", "settle_no", "ref_no", "period", "billing_period", "settled_by",
                     "vendor", "approval_level", "owner", "owner_email", "net_amount", "tax_amount"},
        "documents": {"file_name", "document_type", "source_note", "status", "case_id", "contract_id"},
        "budgets": {"budget_code", "category", "unit_name", "fiscal_year", "amount", "status", "case_id", "note",
                    "remainder_unit_code", "alloc_method", "alloc_category_kind", "alloc_category"},
        "unit_headcounts": {"unit_code", "unit_name", "headcount", "source_file"},
        "category_shares": {"category", "unit_code", "unit_name", "share_pct", "source_file"},
        "projects": {"project_code", "project_name", "source", "necessity", "progress", "owner", "status", "case_id", "due_date", "note",
                     "level", "progress_planned", "rag_status", "start_date", "end_date"},
        "signoffs": {"signoff_code", "subject", "applicant", "amount", "status", "sign_date", "case_id", "note", "attachment_ref"},
        "purchases": {"purchase_code", "item_name", "vendor_name", "quantity", "amount", "status", "case_id", "note"},
        "project_items": {"project_id", "seq", "item_name", "owner", "start_date", "end_date", "exec_status",
                          "sub_total", "sub_done", "progress", "rag", "risk_note", "decision_needed",
                          "support_needed", "duration_days", "status"},
        "budget_allocations": {"budget_id", "seq", "unit_code", "unit_name", "share_pct", "amount", "source_file"},
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


def _norm_date(v: Any) -> str:
    """Excel 日期（datetime 或字串）→ 'YYYY-MM-DD'；空值回空字串。"""
    if v is None or v == "":
        return ""
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip().replace("/", "-")
    return s[:10]


def _clean_owner(v: Any) -> str:
    """負責人欄防呆：若被填成長句／備註（去識別化或誤填一整段），不當人名，回空字串。"""
    s = " ".join(str(v).split()) if v is not None else ""
    if len(s) > 16 or any(p in s for p in "。？！?!，,；;"):
        return ""
    return s


def _xls_pct(v: Any) -> float:
    """比例欄：<=1 視為小數（0.294→29.4），>1 視為已是百分比。"""
    if v is None or v == "":
        return 0.0
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return round(f * 100, 1) if f <= 1 else round(f, 1)


def parse_projects_xlsx(data: bytes) -> list[dict[str, Any]]:
    """解析『處級專案進度追蹤總表』.xlsx → 專案清單（依欄名對應，不靠欄位位置）。

    版面：每張工作表＝一個組別；表頭含「專案名稱」。專案為多列一組——
    第一列帶專案層級欄（名稱/必要性/總進度預計%/實際%/總進度燈號，AI 表多一欄「分類」）；
    其後每列是「工作主項目」，各自帶開始日期/結束日期。專案起訖＝各工作項的 min(開始)→max(結束)。
    因 AI 表欄位右移一格，一律用欄名比對，避免位置錯位（先前燈號抓成小數即此故）。"""
    import io
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out: list[dict[str, Any]] = []
    try:
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            rows = list(ws.iter_rows(values_only=True))
            header_idx = None
            for i, r in enumerate(rows[:8]):
                if r and any(str(c).replace("\n", "") == "專案名稱" for c in r if c is not None):
                    header_idx = i
                    break
            if header_idx is None:
                continue
            headers = [str(c).replace("\n", "").strip() if c is not None else "" for c in rows[header_idx]]

            def find(pred, lo=0, hi=None):
                hi = len(headers) if hi is None else hi
                for j in range(lo, hi):
                    if headers[j] and pred(headers[j]):
                        return j
                return None

            work_i = find(lambda h: h == "工作主項目")
            split = work_i if work_i is not None else len(headers)
            name_i = find(lambda h: h == "專案名稱", 0, split)
            if name_i is None:
                continue
            nec_i = find(lambda h: "必要性" in h, 0, split)
            plan_i = find(lambda h: "預計" in h, 0, split)
            act_i = find(lambda h: "實際" in h, 0, split)
            rag_i = find(lambda h: "燈號" in h, 0, split)          # 總進度燈號（專案層級那個）
            lvl_i = find(lambda h: h == "分類", 0, split)          # 只有 AI 表有
            start_i = find(lambda h: "開始" in h, split)
            end_i = find(lambda h: "結束" in h, split)
            owner_i = find(lambda h: "負責人" in h, split)
            # 工作項層級欄位（split＝工作主項目那欄之後）
            item_i = work_i  # 工作主項目
            exec_i = find(lambda h: "執行進度" in h, split)
            subtot_i = find(lambda h: "子項目總數" in h, split)
            subdone_i = find(lambda h: "子項目完成數" in h, split)
            prog_i = find(lambda h: "完成度" in h, split)
            wrag_i = find(lambda h: "燈號" in h, split)            # 工作項燈號（split 後第一個）
            risk_i = find(lambda h: ("風險" in h or "備註" in h), split)
            dec_i = find(lambda h: "需決策" in h, split)
            sup_i = find(lambda h: "需支援" in h, split)
            dur_i = find(lambda h: "持續天數" in h, split)

            def cell(r, i):
                return r[i] if (i is not None and i < len(r)) else None

            def txt(r, i):
                v = cell(r, i)
                return str(v).strip() if v is not None else ""

            def as_int(r, i):
                try:
                    return int(float(cell(r, i)))
                except (TypeError, ValueError):
                    return 0

            def build_item(r, seq_no):
                name = " ".join(txt(r, item_i).split())
                if not name:
                    return None
                return {
                    "seq": seq_no,
                    "item_name": name,
                    "owner": _clean_owner(cell(r, owner_i)),
                    "start_date": _norm_date(cell(r, start_i)),
                    "end_date": _norm_date(cell(r, end_i)),
                    "exec_status": txt(r, exec_i),
                    "sub_total": as_int(r, subtot_i),
                    "sub_done": as_int(r, subdone_i),
                    "progress": _xls_pct(cell(r, prog_i)),
                    "rag": txt(r, wrag_i),
                    "risk_note": txt(r, risk_i),
                    "decision_needed": txt(r, dec_i),
                    "support_needed": txt(r, sup_i),
                    "duration_days": txt(r, dur_i),
                }

            seq = 0
            cur: dict[str, Any] | None = None
            for r in rows[header_idx + 1:]:
                if not r:
                    continue
                nm = " ".join(txt(r, name_i).split())  # 收斂內部換行/多空白，避免分頁標籤爆版
                if nm:  # 新專案起始列
                    if cur is not None:
                        out.append(cur)
                    seq += 1
                    cur = {
                        "project_code": f"{sheet}-{seq}",
                        "project_name": nm,
                        "source": sheet,
                        "necessity": txt(r, nec_i),
                        "progress_planned": _xls_pct(cell(r, plan_i)),
                        "progress": _xls_pct(cell(r, act_i)),
                        "rag_status": txt(r, rag_i),
                        "level": txt(r, lvl_i),
                        "owner": _clean_owner(cell(r, owner_i)),
                        "start_date": _norm_date(cell(r, start_i)),
                        "end_date": _norm_date(cell(r, end_i)),
                        "items": [],
                    }
                    first = build_item(r, 1)
                    if first:
                        cur["items"].append(first)
                elif cur is not None:  # 工作項續列：擴張起訖、補負責人、加一筆工作項
                    sd, ed = _norm_date(cell(r, start_i)), _norm_date(cell(r, end_i))
                    if sd and (not cur["start_date"] or sd < cur["start_date"]):
                        cur["start_date"] = sd
                    if ed and (not cur["end_date"] or ed > cur["end_date"]):
                        cur["end_date"] = ed
                    if not cur["owner"]:
                        cur["owner"] = _clean_owner(cell(r, owner_i))
                    item = build_item(r, len(cur["items"]) + 1)
                    if item:
                        cur["items"].append(item)
            if cur is not None:
                out.append(cur)
    finally:
        wb.close()
    return out


def commit_projects_import(records: list[dict[str, Any]]) -> dict[str, Any]:
    """寫入 projects：單一交易、逐列稽核。以（組別＋專案名稱）為識別鍵——
    同名專案改『更新』（讓更新版總表的起訖日/進度灌進既有資料），沒見過的才『新增』。"""
    _identity = {"project_code", "source", "project_name"}
    fields_allowed = allowed_fields()["projects"]
    with connect() as conn:
        existing: dict[tuple[str, str], int] = {}
        for row in conn.execute("SELECT id, source, project_name FROM projects").fetchall():
            existing[(row["source"] or "", row["project_name"] or "")] = row["id"]
        item_fields = allowed_fields()["project_items"]
        created: list[str] = []
        updated: list[str] = []
        items_written = 0
        for rec in records:
            name = str(rec.get("project_name", "")).strip()
            if not name:
                continue
            key = (rec.get("source", "") or "", name)
            fields = {k: v for k, v in rec.items() if k in fields_allowed}
            if key in existing:
                rid = existing[key]
                before = get_row(conn, "projects", rid)
                upd = {k: v for k, v in fields.items() if k not in _identity}
                if upd:
                    sets = ", ".join(f"{k} = ?" for k in upd)
                    conn.execute(f"UPDATE projects SET {sets} WHERE id = ?", [*upd.values(), rid])
                after = get_row(conn, "projects", rid)
                write_audit_log(conn, "projects", rid, "import-update", before, after)
                updated.append(name)
            else:
                columns = ", ".join(fields)
                placeholders = ", ".join("?" for _ in fields)
                cur = conn.execute(f"INSERT INTO projects ({columns}) VALUES ({placeholders})", list(fields.values()))
                after = get_row(conn, "projects", cur.lastrowid)
                write_audit_log(conn, "projects", cur.lastrowid, "import", None, {**after, "import_source": "xlsx"})
                rid = cur.lastrowid
                existing[key] = rid
                created.append(name)
            # 工作項：以（project_id＋item_name）為鍵，同名更新、沒見過新增（不刪系統內新增的）
            seen = {r["item_name"]: r["id"] for r in conn.execute(
                "SELECT id, item_name FROM project_items WHERE project_id = ?", (rid,)).fetchall()}
            for it in rec.get("items", []):
                ifields = {k: v for k, v in it.items() if k in item_fields}
                ifields["project_id"] = rid
                iname = ifields.get("item_name", "")
                if iname in seen:
                    upd = {k: v for k, v in ifields.items() if k not in ("project_id", "item_name")}
                    if upd:
                        sets = ", ".join(f"{k} = ?" for k in upd)
                        conn.execute(f"UPDATE project_items SET {sets} WHERE id = ?", [*upd.values(), seen[iname]])
                else:
                    cols = ", ".join(ifields)
                    ph = ", ".join("?" for _ in ifields)
                    c2 = conn.execute(f"INSERT INTO project_items ({cols}) VALUES ({ph})", list(ifields.values()))
                    seen[iname] = c2.lastrowid
                items_written += 1
        return {"created_count": len(created), "updated_count": len(updated), "skipped_count": 0,
                "items_count": items_written, "created": created, "updated": updated}


def list_project_items(project_id: int) -> list[dict[str, Any]]:
    """某專案的工作項清單（排除已停用），依序號排序。"""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM project_items WHERE project_id = ? AND status != 'disabled' ORDER BY seq ASC, id ASC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def parse_budget_xlsx(data: bytes) -> list[dict[str, Any]]:
    """解析『預算』.xlsx → 預算清單。此檔為『表單型』：一張工作表＝一筆預算，
    內容是「標籤：值」（預算項目／費用內容／填寫部門／預估人員…）＋右側各年度費用表。
    故用『認標籤』抓值（不是認欄位位置），金額取『全年度費用』欄中最大的一年。"""
    import io
    import openpyxl

    def norm(v: Any) -> str:
        return " ".join(str(v).split()) if v is not None else ""

    label_map = {"預算項目": "category", "填寫部門": "unit_name"}
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out: list[dict[str, Any]] = []
    try:
        for sheet in wb.sheetnames:
            rows = [list(r) if r else [] for r in wb[sheet].iter_rows(values_only=True)]

            def value_right(r: list, i: int) -> str:
                for j in range(i + 1, len(r)):
                    if r[j] is not None and str(r[j]).strip():
                        return norm(r[j])
                return ""

            fields: dict[str, str] = {}
            content = person = ""
            amount_col: int | None = None
            for r in rows:
                for i, cell in enumerate(r):
                    key = norm(cell).rstrip("：:")
                    if key in label_map and label_map[key] not in fields:
                        fields[label_map[key]] = value_right(r, i)
                    elif key == "費用內容" and not content:
                        content = value_right(r, i)
                    elif key == "預估人員" and not person:
                        person = value_right(r, i)
                    if norm(cell) == "全年度費用":
                        amount_col = i

            amount = 0.0
            fiscal_year = ""
            if amount_col is not None:
                for r in rows:
                    if amount_col < len(r):
                        try:
                            fv = float(r[amount_col])
                        except (TypeError, ValueError):
                            fv = None
                        if fv and fv > amount:
                            yr = next((norm(c) for c in r if norm(c).endswith("年度")
                                       and any(ch.isdigit() for ch in norm(c))), "")
                            amount, fiscal_year = round(fv, 2), yr

            if not (fields.get("category") or amount):
                continue  # 空白/非預算表跳過

            # 62 單位共同費用分攤表：找「部門代號」表頭列，往下讀到「合計」；col「合計」＝各單位年度分攤額
            allocations: list[dict[str, Any]] = []
            code_col = name_col = total_col = None
            alloc_hdr = None
            for i, r in enumerate(rows):
                if any(norm(c) == "部門代號" for c in r):
                    alloc_hdr = i
                    for j, c in enumerate(r):
                        k = norm(c)
                        if k == "部門代號":
                            code_col = j
                        elif k == "部門別":
                            name_col = j
                        elif k == "合計":
                            total_col = j
                    break
            if alloc_hdr is not None and name_col is not None and total_col is not None:
                seq = 0
                for r in rows[alloc_hdr + 1:]:
                    nm = norm(r[name_col]) if name_col < len(r) else ""
                    if nm in ("合計", "EOF"):
                        if nm == "合計":
                            break  # 遇到合計列就停
                        continue
                    if not nm:
                        continue
                    try:
                        amt = round(float(r[total_col]), 2) if total_col < len(r) else 0.0
                    except (TypeError, ValueError):
                        amt = 0.0
                    cd = norm(r[code_col]) if (code_col is not None and code_col < len(r)) else ""
                    seq += 1
                    allocations.append({
                        "seq": seq,
                        "unit_code": cd,
                        "unit_name": nm,
                        "amount": amt,
                        "share_pct": round(amt / amount * 100, 2) if amount else 0.0,
                    })

            note = "；".join(x for x in [content, (f"預估人員：{person}" if person else "")] if x)
            out.append({
                "budget_code": norm(sheet)[:60] or f"預算-{len(out) + 1}",
                "category": fields.get("category", ""),
                "unit_name": fields.get("unit_name", ""),
                "fiscal_year": fiscal_year,
                "amount": amount,
                "note": note,
                "allocations": allocations,
            })
    finally:
        wb.close()
    return out


def commit_budgets_import(records: list[dict[str, Any]], source_file: str = "") -> dict[str, Any]:
    """寫入 budgets：單一交易、逐列稽核。以 budget_code（工作表名）為鍵——同名更新、沒見過新增。
    每筆預算的 62 單位分攤明細一併寫入 budget_allocations（以 budget_id+unit_code 為鍵、同碼更新）。
    source_file：這批資料的來源 Excel 檔名，寫進每筆分攤，供單位撞名清單指回來源。"""
    source_file = (source_file or "").strip()
    fields_allowed = allowed_fields()["budgets"]
    alloc_fields = allowed_fields()["budget_allocations"]
    with connect() as conn:
        existing = {r["budget_code"]: r["id"] for r in conn.execute("SELECT id, budget_code FROM budgets").fetchall()}
        created: list[str] = []
        updated: list[str] = []
        alloc_written = 0
        for rec in records:
            code = str(rec.get("budget_code", "")).strip()
            if not code:
                continue
            fields = {k: v for k, v in rec.items() if k in fields_allowed}
            if code in existing:
                rid = existing[code]
                before = get_row(conn, "budgets", rid)
                upd = {k: v for k, v in fields.items() if k != "budget_code"}
                if upd:
                    sets = ", ".join(f"{k} = ?" for k in upd)
                    conn.execute(f"UPDATE budgets SET {sets} WHERE id = ?", [*upd.values(), rid])
                write_audit_log(conn, "budgets", rid, "import-update", before, get_row(conn, "budgets", rid))
                updated.append(code)
            else:
                columns = ", ".join(fields)
                placeholders = ", ".join("?" for _ in fields)
                cur = conn.execute(f"INSERT INTO budgets ({columns}) VALUES ({placeholders})", list(fields.values()))
                after = get_row(conn, "budgets", cur.lastrowid)
                write_audit_log(conn, "budgets", cur.lastrowid, "import", None, {**after, "import_source": "xlsx"})
                rid = cur.lastrowid
                existing[code] = rid
                created.append(code)
            # 分攤明細：以（budget_id, unit_code）為鍵 upsert
            seen = {r["unit_code"]: r["id"] for r in conn.execute(
                "SELECT id, unit_code FROM budget_allocations WHERE budget_id = ?", (rid,)).fetchall()}
            for al in rec.get("allocations", []):
                afields = {k: v for k, v in al.items() if k in alloc_fields}
                afields["budget_id"] = rid
                if source_file:
                    afields["source_file"] = source_file
                ucode = afields.get("unit_code", "")
                if ucode and ucode in seen:
                    upd = {k: v for k, v in afields.items() if k not in ("budget_id", "unit_code")}
                    if upd:
                        sets = ", ".join(f"{k} = ?" for k in upd)
                        conn.execute(f"UPDATE budget_allocations SET {sets} WHERE id = ?", [*upd.values(), seen[ucode]])
                else:
                    cols = ", ".join(afields)
                    ph = ", ".join("?" for _ in afields)
                    c2 = conn.execute(f"INSERT INTO budget_allocations ({cols}) VALUES ({ph})", list(afields.values()))
                    if ucode:
                        seen[ucode] = c2.lastrowid
                alloc_written += 1
        return {"created_count": len(created), "updated_count": len(updated), "skipped_count": 0,
                "allocations_count": alloc_written, "created": created, "updated": updated}


def list_budget_allocations(budget_id: int) -> list[dict[str, Any]]:
    """某費用項目的單位分攤明細（依分攤額大到小），並算出『整數分攤』：
    各單位四捨五入到元，湊不齊的尾數歸給『尾數承擔單位』（預設＝填寫部門，可用 remainder_unit_code 覆寫），
    使整數欄合計＝項目總額。回傳每列含 amount(精確)、amount_int(整數)、is_remainder_unit、remainder。"""
    with connect() as conn:
        budget = get_row(conn, "budgets", budget_id)
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM budget_allocations WHERE budget_id = ? ORDER BY amount DESC, seq ASC",
            (budget_id,)).fetchall()]
    if not rows:
        return rows
    total = int(round(float(budget.get("amount") or 0)))
    for r in rows:
        r["amount_int"] = int(round(float(r.get("amount") or 0)))
        r["is_remainder_unit"] = False
        r["remainder"] = 0
    remainder = total - sum(r["amount_int"] for r in rows)
    # 決定承擔單位：明指 remainder_unit_code > 對到填寫部門(unit_name) > 分攤額最大者
    rem_code = str(budget.get("remainder_unit_code") or "").strip()
    bunit = str(budget.get("unit_name") or "").strip()
    absorber = None
    if rem_code:
        absorber = next((r for r in rows if r["unit_code"] == rem_code), None)
    if absorber is None and bunit:
        absorber = next((r for r in rows if r["unit_name"] == bunit), None)
    if absorber is None:
        absorber = rows[0]  # 分攤額最大者
    absorber["amount_int"] += remainder
    absorber["is_remainder_unit"] = True
    absorber["remainder"] = remainder
    return rows


def budget_unit_rollup(unit_code: str | None = None) -> dict[str, Any]:
    """以單位為主的彙總：每個單位在所有費用項目的分攤合計（部門負擔表）。
    經單位主檔別名解析：合併過的撞名（如同碼異名）會認到同一單位、合併加總；
    未裁決的維持原 (代號,名稱)。帶 unit_code 則另回該單位被攤的每一筆明細。"""
    with connect() as conn:
        alias_map, _masters = _load_alias_map(conn)
        rows = [dict(r) for r in conn.execute(
            "SELECT a.unit_code, a.unit_name, a.amount, a.share_pct, b.budget_code, b.category, b.fiscal_year "
            "FROM budget_allocations a JOIN budgets b ON b.id = a.budget_id").fetchall()]

    def resolve(code: str, name: str) -> tuple[str, str, str]:
        m = alias_map.get((code, name))
        if m:
            return (f"m{m['master_id']}", m["canonical_code"], m["canonical_name"])
        return (f"r::{code}::{name}", code, name)

    groups: dict[str, dict[str, Any]] = {}
    detail: list[dict[str, Any]] = []
    for r in rows:
        code = str(r.get("unit_code") or "").strip()
        name = str(r.get("unit_name") or "").strip()
        key, disp_code, disp_name = resolve(code, name)
        g = groups.setdefault(key, {"unit_code": disp_code, "unit_name": disp_name,
                                    "item_count": 0, "total_amount": 0.0})
        g["item_count"] += 1
        g["total_amount"] += float(r.get("amount") or 0)
        if unit_code is not None and disp_code == str(unit_code):
            detail.append({"amount": r.get("amount"), "share_pct": r.get("share_pct"),
                           "budget_code": r.get("budget_code"), "category": r.get("category"),
                           "fiscal_year": r.get("fiscal_year")})

    units = sorted(groups.values(), key=lambda g: -g["total_amount"])
    for u in units:
        u["total_amount"] = round(u["total_amount"])
    result: dict[str, Any] = {"units": units}
    if unit_code is not None:
        detail.sort(key=lambda d: -float(d.get("amount") or 0))
        result["detail"] = detail
    return result


def _load_alias_map(conn) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[int, dict[str, Any]]]:
    """讀單位主檔＋別名，回傳：
    - alias_map：{(代號, 名稱) → {master_id, canonical_code, canonical_name}}
    - masters：{master_id → {id, canonical_code, canonical_name, ...}}"""
    masters = {m["id"]: dict(m) for m in conn.execute(
        "SELECT id, canonical_code, canonical_name, status, note FROM unit_master").fetchall()}
    alias_map: dict[tuple[str, str], dict[str, Any]] = {}
    for a in conn.execute("SELECT master_id, alias_code, alias_name FROM unit_aliases").fetchall():
        m = masters.get(a["master_id"])
        if not m:
            continue
        alias_map[(str(a["alias_code"] or "").strip(), str(a["alias_name"] or "").strip())] = {
            "master_id": m["id"], "canonical_code": m["canonical_code"], "canonical_name": m["canonical_name"]}
    return alias_map, masters


def unit_conflicts() -> dict[str, Any]:
    """單位主檔：偵測跨資料的『撞名』——同一代號對到多個名稱、或同一名稱對到多個代號。
    掃描 budget_allocations、unit_headcounts；已在單位主檔裁決過（每個變體都有別名）的組別視為『已處理』，
    不再列入待確認。每個變體附上它目前對到的主檔（canonical），供前端顯示與合併操作。"""
    # 每個資料表的中文分類（沒記到來源檔名時的退路標籤）
    sources = [
        ("budget_allocations", "預算分攤"),
        ("unit_headcounts", "人數基準"),
    ]
    # 收集所有 (代號, 名稱) 出現次數，並記「來源」＝實際 Excel 檔名（記不到才退回分類標籤）
    pairs: dict[tuple[str, str], dict[str, Any]] = {}
    with connect() as conn:
        alias_map, _masters = _load_alias_map(conn)
        for table, label in sources:
            rows = conn.execute(
                f"SELECT COALESCE(unit_code,'') AS c, COALESCE(unit_name,'') AS n, "
                f"COALESCE(source_file,'') AS f, COUNT(*) AS cnt "
                f"FROM {table} GROUP BY c, n, f"
            ).fetchall()
            for r in rows:
                code = str(r["c"]).strip()
                name = str(r["n"]).strip()
                if not name and not code:
                    continue
                fname = str(r["f"]).strip()
                # 有檔名就顯示檔名；舊資料沒記檔名，退回「分類（未記檔名）」
                src = fname if fname else f"{label}（舊資料·未記檔名）"
                key = (code, name)
                slot = pairs.setdefault(key, {"unit_code": code, "unit_name": name, "count": 0, "sources": set()})
                slot["count"] += int(r["cnt"])
                slot["sources"].add(src)

    def _entry(code: str, name: str, slot: dict[str, Any]) -> dict[str, Any]:
        m = alias_map.get((code, name))
        return {"unit_code": code, "unit_name": name, "count": slot["count"],
                "sources": sorted(slot["sources"]),
                "master": m,  # None＝尚未裁決；否則為它目前對到的主檔
                "resolved": bool(m)}

    by_code: dict[str, list[dict[str, Any]]] = {}
    by_name: dict[str, list[dict[str, Any]]] = {}
    for (code, name), slot in pairs.items():
        entry = _entry(code, name, slot)
        if code:
            by_code.setdefault(code, []).append(entry)
        if name:
            by_name.setdefault(name, []).append(entry)

    # 一碼多名；已全部裁決（每個變體都有別名）者視為已處理，不再列入待確認
    code_conflicts = []
    resolved_codes = 0
    for code, entries in by_code.items():
        names = {e["unit_name"] for e in entries if e["unit_name"]}
        if len(names) <= 1:
            continue
        if all(e["resolved"] for e in entries):
            resolved_codes += 1
            continue
        code_conflicts.append({"unit_code": code, "variants": sorted(entries, key=lambda e: -e["count"])})
    # 一名多碼（含「有代號 vs 空代號」）
    name_conflicts = []
    resolved_names = 0
    for name, entries in by_name.items():
        codes = {e["unit_code"] for e in entries}
        if len(codes) <= 1:
            continue
        if all(e["resolved"] for e in entries):
            resolved_names += 1
            continue
        name_conflicts.append({"unit_name": name, "variants": sorted(entries, key=lambda e: -e["count"])})

    code_conflicts.sort(key=lambda x: x["unit_code"])
    name_conflicts.sort(key=lambda x: x["unit_name"])
    return {
        "code_conflicts": code_conflicts,
        "name_conflicts": name_conflicts,
        "summary": {
            "code_conflicts": len(code_conflicts),
            "name_conflicts": len(name_conflicts),
            "resolved_groups": resolved_codes + resolved_names,
            "distinct_pairs": len(pairs),
        },
    }


def list_unit_master() -> dict[str, Any]:
    """單位主檔清單：每個主檔 + 它底下的別名（代號/名稱），供檢視與解除合併。"""
    with connect() as conn:
        masters = [dict(m) for m in conn.execute(
            "SELECT id, canonical_code, canonical_name, status, note FROM unit_master ORDER BY canonical_code, id").fetchall()]
        aliases = [dict(a) for a in conn.execute(
            "SELECT id, master_id, alias_code, alias_name FROM unit_aliases ORDER BY id").fetchall()]
    by_master: dict[int, list[dict[str, Any]]] = {}
    for a in aliases:
        by_master.setdefault(a["master_id"], []).append(a)
    for m in masters:
        m["aliases"] = by_master.get(m["id"], [])
    return {"masters": masters, "count": len(masters)}


def _find_or_create_master(conn, canonical_code: str, canonical_name: str, note: str = "") -> int:
    """以 (canonical_code, canonical_name) 找主檔，沒有就建。回傳 master_id。"""
    code = (canonical_code or "").strip()
    name = (canonical_name or "").strip()
    row = conn.execute(
        "SELECT id FROM unit_master WHERE canonical_code = ? AND canonical_name = ?", (code, name)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO unit_master (canonical_code, canonical_name, note) VALUES (?, ?, ?)", (code, name, note))
    return cur.lastrowid


def _attach_alias(conn, master_id: int, alias_code: str, alias_name: str) -> int | None:
    """把 (代號, 名稱) 掛到某主檔；若別名已存在則改指到此主檔（重新裁決可覆蓋）。
    回傳『前一個 master_id』（原本沒別名則 None），供決策紀錄記 undo。"""
    code = (alias_code or "").strip()
    name = (alias_name or "").strip()
    existing = conn.execute(
        "SELECT id, master_id FROM unit_aliases WHERE alias_code = ? AND alias_name = ?", (code, name)).fetchone()
    if existing:
        prev = existing["master_id"]
        conn.execute("UPDATE unit_aliases SET master_id = ? WHERE id = ?", (master_id, existing["id"]))
        return prev
    conn.execute(
        "INSERT INTO unit_aliases (master_id, alias_code, alias_name) VALUES (?, ?, ?)", (master_id, code, name))
    return None


def _record_decision(conn, action: str, reason: str, detail: dict[str, Any], undo_ops: list[dict[str, Any]]) -> int:
    cur = conn.execute(
        "INSERT INTO unit_decisions (action, reason, actor, detail_json, undo_ops_json) VALUES (?, ?, ?, ?, ?)",
        (action, (reason or "").strip(), _current_actor.get(),
         json.dumps(detail, ensure_ascii=False), json.dumps(undo_ops, ensure_ascii=False)))
    return cur.lastrowid


def _cleanup_empty_masters(conn) -> int:
    rows = conn.execute(
        "SELECT id FROM unit_master WHERE id NOT IN (SELECT DISTINCT master_id FROM unit_aliases)").fetchall()
    for r in rows:
        conn.execute("DELETE FROM unit_master WHERE id = ?", (r["id"],))
    return len(rows)


def unit_merge_impact(variants: list[dict[str, Any]]) -> dict[str, Any]:
    """影響預覽：這些變體目前在『預算分攤』佔幾筆、金額多少（讓使用者按下前看清後果）。"""
    rows = 0
    amount = 0.0
    per: list[dict[str, Any]] = []
    with connect() as conn:
        for v in variants:
            code = str(v.get("unit_code", "")).strip()
            name = str(v.get("unit_name", "")).strip()
            r = conn.execute(
                "SELECT COUNT(*) AS n, COALESCE(SUM(amount),0) AS amt FROM budget_allocations "
                "WHERE COALESCE(unit_code,'')=? AND COALESCE(unit_name,'')=?", (code, name)).fetchone()
            rows += int(r["n"])
            amount += float(r["amt"])
            per.append({"unit_code": code, "unit_name": name, "rows": int(r["n"]), "amount": round(float(r["amt"]))})
    return {"rows": rows, "amount": round(amount), "per_variant": per}


def merge_units(variants: list[dict[str, Any]], canonical_code: str, canonical_name: str, reason: str = "") -> dict[str, Any]:
    """合併：這些變體是同一單位，以 (canonical_code, canonical_name) 為準。
    建/取主檔，把每個變體掛成別名。非破壞式：原始資料不動，讀取時經別名認到同一主檔。
    reason 必填（防呆＋留依據）；記入 unit_decisions，可逐筆復原。"""
    if not variants:
        raise ValueError("沒有要合併的單位變體。")
    if not (reason or "").strip():
        raise ValueError("請填『為什麼這樣判斷』的理由，才能裁決。")
    cname = (canonical_name or "").strip()
    if not cname and not (canonical_code or "").strip():
        raise ValueError("請指定要以哪個為準（代號或名稱至少一個）。")
    with connect() as conn:
        master_id = _find_or_create_master(conn, canonical_code, canonical_name)
        undo_ops = []
        for v in variants:
            code = str(v.get("unit_code", ""))
            name = str(v.get("unit_name", ""))
            prev = _attach_alias(conn, master_id, code, name)
            undo_ops.append({"alias_code": code.strip(), "alias_name": name.strip(), "prev_master_id": prev})
        _cleanup_empty_masters(conn)
        detail = {"canonical_code": (canonical_code or "").strip(), "canonical_name": cname, "variants": variants}
        did = _record_decision(conn, "merge", reason, detail, undo_ops)
    return {"master_id": master_id, "merged": len(variants), "decision_id": did,
            "canonical_code": (canonical_code or "").strip(), "canonical_name": cname}


def reassign_unit(variant: dict[str, Any], canonical_code: str, canonical_name: str, reason: str = "") -> dict[str, Any]:
    """逐筆改派：某一筆撞名變體其實屬於別的單位（常見於代號打錯），
    把它單獨掛到指定的主單位（現有的、或用正確代號/名稱新建），不影響同組其他筆。非破壞式、可復原。"""
    if not variant or (not str(variant.get("unit_code", "")).strip() and not str(variant.get("unit_name", "")).strip()):
        raise ValueError("沒有要改派的單位。")
    if not (reason or "").strip():
        raise ValueError("請填『為什麼這樣判斷』的理由，才能改派。")
    cname = (canonical_name or "").strip()
    if not cname and not (canonical_code or "").strip():
        raise ValueError("請指定要改派到哪個單位（代號或名稱至少一個）。")
    code = str(variant.get("unit_code", ""))
    name = str(variant.get("unit_name", ""))
    with connect() as conn:
        master_id = _find_or_create_master(conn, canonical_code, canonical_name)
        prev = _attach_alias(conn, master_id, code, name)
        _cleanup_empty_masters(conn)
        undo_ops = [{"alias_code": code.strip(), "alias_name": name.strip(), "prev_master_id": prev}]
        detail = {"canonical_code": (canonical_code or "").strip(), "canonical_name": cname, "variants": [variant]}
        did = _record_decision(conn, "reassign", reason, detail, undo_ops)
    return {"master_id": master_id, "decision_id": did,
            "canonical_code": (canonical_code or "").strip(), "canonical_name": cname}


def split_units(variants: list[dict[str, Any]], reason: str = "") -> dict[str, Any]:
    """分開保留：這些變體是不同單位，各自成為一個主檔（別名＝自己）。裁決後不再列為待確認。"""
    if not variants:
        raise ValueError("沒有要分開的單位變體。")
    if not (reason or "").strip():
        raise ValueError("請填『為什麼這樣判斷』的理由，才能裁決。")
    made = 0
    with connect() as conn:
        undo_ops = []
        for v in variants:
            code = str(v.get("unit_code", ""))
            name = str(v.get("unit_name", ""))
            mid = _find_or_create_master(conn, code, name)
            prev = _attach_alias(conn, mid, code, name)
            undo_ops.append({"alias_code": code.strip(), "alias_name": name.strip(), "prev_master_id": prev})
            made += 1
        _cleanup_empty_masters(conn)
        did = _record_decision(conn, "split", reason, {"variants": variants}, undo_ops)
    return {"split": made, "decision_id": did}


def list_unit_decisions(limit: int = 100) -> dict[str, Any]:
    """決策紀錄：誰、何時、把什麼合併/分開、為什麼，供檢視與逐筆復原。"""
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT id, action, reason, actor, detail_json, undone, created_at "
            "FROM unit_decisions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
    out = []
    for r in rows:
        try:
            detail = json.loads(r.get("detail_json") or "{}")
        except (ValueError, TypeError):
            detail = {}
        variants = detail.get("variants", [])
        out.append({
            "id": r["id"], "action": r["action"], "reason": r["reason"], "actor": r["actor"],
            "undone": bool(r["undone"]), "created_at": r["created_at"],
            "canonical_code": detail.get("canonical_code", ""), "canonical_name": detail.get("canonical_name", ""),
            "variants": [{"unit_code": v.get("unit_code", ""), "unit_name": v.get("unit_name", "")} for v in variants],
        })
    return {"decisions": out, "count": len(out)}


def undo_decision(decision_id: int) -> dict[str, Any]:
    """復原某次裁決：依 undo_ops 把每個別名還原到前一個歸屬（原本沒有就刪掉），並清掉空主檔。"""
    with connect() as conn:
        row = conn.execute(
            "SELECT undo_ops_json, undone FROM unit_decisions WHERE id = ?", (decision_id,)).fetchone()
        if not row:
            raise ValueError("找不到該筆裁決紀錄。")
        if row["undone"]:
            raise ValueError("這筆裁決已經復原過了。")
        try:
            ops = json.loads(row["undo_ops_json"] or "[]")
        except (ValueError, TypeError):
            ops = []
        for op in ops:
            code = str(op.get("alias_code", "")).strip()
            name = str(op.get("alias_name", "")).strip()
            prev = op.get("prev_master_id")
            if prev is None:
                conn.execute("DELETE FROM unit_aliases WHERE alias_code = ? AND alias_name = ?", (code, name))
            else:
                conn.execute("UPDATE unit_aliases SET master_id = ? WHERE alias_code = ? AND alias_name = ?",
                             (prev, code, name))
        removed = _cleanup_empty_masters(conn)
        conn.execute("UPDATE unit_decisions SET undone = 1 WHERE id = ?", (decision_id,))
    return {"undone": decision_id, "removed_masters": removed}


def reset_unit_decisions() -> dict[str, Any]:
    """一鍵還原：清掉所有單位裁決（別名＋主檔），回到剛匯入的原始狀態。
    原始 budget_allocations / unit_headcounts 本就沒被動過，所以這是保證級的後悔藥。"""
    with connect() as conn:
        n_alias = conn.execute("SELECT COUNT(*) AS n FROM unit_aliases").fetchone()["n"]
        n_master = conn.execute("SELECT COUNT(*) AS n FROM unit_master").fetchone()["n"]
        conn.execute("DELETE FROM unit_aliases")
        conn.execute("DELETE FROM unit_master")
        conn.execute("UPDATE unit_decisions SET undone = 1 WHERE undone = 0")
        write_audit_log(conn, "unit_master", 0, "reset-all",
                        {"aliases": n_alias, "masters": n_master}, {"aliases": 0, "masters": 0})
    return {"removed_aliases": n_alias, "removed_masters": n_master}


def unlink_alias(alias_id: int) -> dict[str, Any]:
    """解除某別名（還原裁決）；若主檔已無任何別名，一併刪除該空主檔。"""
    with connect() as conn:
        row = conn.execute("SELECT master_id FROM unit_aliases WHERE id = ?", (alias_id,)).fetchone()
        if not row:
            raise ValueError("找不到該別名。")
        master_id = row["master_id"]
        conn.execute("DELETE FROM unit_aliases WHERE id = ?", (alias_id,))
        left = conn.execute("SELECT COUNT(*) AS n FROM unit_aliases WHERE master_id = ?", (master_id,)).fetchone()["n"]
        removed_master = False
        if left == 0:
            conn.execute("DELETE FROM unit_master WHERE id = ?", (master_id,))
            removed_master = True
        write_audit_log(conn, "unit_master", master_id, "unlink-alias", None,
                        {"alias_id": alias_id, "removed_master": removed_master})
    return {"unlinked": alias_id, "removed_master": removed_master}


# ==== 名稱歸納（案件名/專案名/廠商名）：比照單位主檔，把同一實體的不同寫法歸成一個 ====
NAME_SOURCES: dict[str, list[tuple[str, str]]] = {
    "case": [("cases", "title")],
    "project": [("projects", "project_name")],
    "vendor": [("contracts", "vendor_name"), ("payments", "vendor"), ("purchases", "vendor_name")],
}
NAME_KIND_LABEL = {"case": "案件名稱", "project": "專案名稱", "vendor": "廠商名稱"}


def _name_alias_map(conn, kind: str) -> dict[str, str]:
    """{別名 → 主名(canonical)}（限某 kind）。"""
    rows = conn.execute(
        "SELECT a.alias_name, m.canonical_name FROM name_aliases a JOIN name_master m ON m.id = a.master_id "
        "WHERE a.kind = ?", (kind,)).fetchall()
    return {str(r["alias_name"]): str(r["canonical_name"]) for r in rows}


def list_name_values(kind: str) -> dict[str, Any]:
    """回某 kind 目前所有不同名稱（跨來源表去重、計數），並附它目前歸到的主名（若已裁決）。
    供前端做相似度分群、裁決合併。"""
    if kind not in NAME_SOURCES:
        raise ValueError(f"未知的名稱種類：{kind}")
    counts: dict[str, int] = {}
    with connect() as conn:
        for table, col in NAME_SOURCES[kind]:
            for r in conn.execute(
                f"SELECT COALESCE({col},'') AS v, COUNT(*) AS n FROM {table} GROUP BY v").fetchall():
                name = str(r["v"]).strip()
                if name:
                    counts[name] = counts.get(name, 0) + int(r["n"])
        amap = _name_alias_map(conn, kind)
    values = [{"name": n, "count": c, "canonical": amap.get(n)} for n, c in counts.items()]
    values.sort(key=lambda x: (-x["count"], x["name"]))
    return {"kind": kind, "values": values, "resolved": sum(1 for v in values if v["canonical"])}


def _record_name_decision(conn, kind: str, action: str, reason: str, detail: dict, undo_ops: list) -> int:
    cur = conn.execute(
        "INSERT INTO name_decisions (kind, action, reason, actor, detail_json, undo_ops_json) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (kind, action, (reason or "").strip(), _current_actor.get(),
         json.dumps(detail, ensure_ascii=False), json.dumps(undo_ops, ensure_ascii=False)))
    return cur.lastrowid


def _attach_name_alias(conn, master_id: int, kind: str, alias_name: str) -> int | None:
    name = (alias_name or "").strip()
    existing = conn.execute(
        "SELECT id, master_id FROM name_aliases WHERE kind = ? AND alias_name = ?", (kind, name)).fetchone()
    if existing:
        prev = existing["master_id"]
        conn.execute("UPDATE name_aliases SET master_id = ? WHERE id = ?", (master_id, existing["id"]))
        return prev
    conn.execute("INSERT INTO name_aliases (master_id, kind, alias_name) VALUES (?, ?, ?)", (master_id, kind, name))
    return None


def _find_or_create_name_master(conn, kind: str, canonical_name: str) -> int:
    name = (canonical_name or "").strip()
    row = conn.execute(
        "SELECT id FROM name_master WHERE kind = ? AND canonical_name = ?", (kind, name)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO name_master (kind, canonical_name) VALUES (?, ?)", (kind, name))
    return cur.lastrowid


def _cleanup_empty_name_masters(conn) -> int:
    rows = conn.execute(
        "SELECT id FROM name_master WHERE id NOT IN (SELECT DISTINCT master_id FROM name_aliases)").fetchall()
    for r in rows:
        conn.execute("DELETE FROM name_master WHERE id = ?", (r["id"],))
    return len(rows)


def merge_names(kind: str, names: list[str], canonical_name: str, reason: str = "") -> dict[str, Any]:
    """把這些名稱視為同一實體，以 canonical_name 為準（其餘掛成別名）。非破壞式、可復原。"""
    if kind not in NAME_SOURCES:
        raise ValueError(f"未知的名稱種類：{kind}")
    names = [str(n).strip() for n in (names or []) if str(n).strip()]
    if not names:
        raise ValueError("沒有要合併的名稱。")
    if not (reason or "").strip():
        raise ValueError("請填『為什麼這樣判斷』的理由，才能裁決。")
    cname = (canonical_name or "").strip()
    if not cname:
        raise ValueError("請指定要以哪個名稱為準。")
    with connect() as conn:
        master_id = _find_or_create_name_master(conn, kind, cname)
        undo_ops = []
        for n in names:
            prev = _attach_name_alias(conn, master_id, kind, n)
            undo_ops.append({"alias_name": n, "prev_master_id": prev})
        _cleanup_empty_name_masters(conn)
        did = _record_name_decision(conn, kind, "merge", reason,
                                    {"canonical_name": cname, "names": names}, undo_ops)
    return {"master_id": master_id, "merged": len(names), "decision_id": did, "canonical_name": cname}


def split_names(kind: str, names: list[str], reason: str = "") -> dict[str, Any]:
    """這些名稱各自是不同實體（各自成主名）。裁決後不再列為待確認。"""
    if kind not in NAME_SOURCES:
        raise ValueError(f"未知的名稱種類：{kind}")
    names = [str(n).strip() for n in (names or []) if str(n).strip()]
    if not names:
        raise ValueError("沒有要分開的名稱。")
    if not (reason or "").strip():
        raise ValueError("請填『為什麼這樣判斷』的理由，才能裁決。")
    with connect() as conn:
        undo_ops = []
        for n in names:
            mid = _find_or_create_name_master(conn, kind, n)
            prev = _attach_name_alias(conn, mid, kind, n)
            undo_ops.append({"alias_name": n, "prev_master_id": prev})
        _cleanup_empty_name_masters(conn)
        did = _record_name_decision(conn, kind, "split", reason, {"names": names}, undo_ops)
    return {"split": len(names), "decision_id": did}


def list_name_decisions(kind: str | None = None, limit: int = 100) -> dict[str, Any]:
    where = "WHERE kind = ?" if kind else ""
    params = ([kind] if kind else []) + [limit]
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT id, kind, action, reason, actor, detail_json, undone, created_at "
            f"FROM name_decisions {where} ORDER BY id DESC LIMIT ?", params).fetchall()]
    out = []
    for r in rows:
        try:
            detail = json.loads(r.get("detail_json") or "{}")
        except (ValueError, TypeError):
            detail = {}
        out.append({"id": r["id"], "kind": r["kind"], "action": r["action"], "reason": r["reason"],
                    "actor": r["actor"], "undone": bool(r["undone"]), "created_at": r["created_at"],
                    "canonical_name": detail.get("canonical_name", ""), "names": detail.get("names", [])})
    return {"decisions": out, "count": len(out)}


def undo_name_decision(decision_id: int) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT undo_ops_json, undone FROM name_decisions WHERE id = ?", (decision_id,)).fetchone()
        if not row:
            raise ValueError("找不到該筆裁決紀錄。")
        if row["undone"]:
            raise ValueError("這筆裁決已經復原過了。")
        try:
            ops = json.loads(row["undo_ops_json"] or "[]")
        except (ValueError, TypeError):
            ops = []
        d = conn.execute("SELECT kind FROM name_decisions WHERE id = ?", (decision_id,)).fetchone()
        kind = d["kind"] if d else ""
        for op in ops:
            name = str(op.get("alias_name", "")).strip()
            prev = op.get("prev_master_id")
            if prev is None:
                conn.execute("DELETE FROM name_aliases WHERE kind = ? AND alias_name = ?", (kind, name))
            else:
                conn.execute("UPDATE name_aliases SET master_id = ? WHERE kind = ? AND alias_name = ?",
                             (prev, kind, name))
        removed = _cleanup_empty_name_masters(conn)
        conn.execute("UPDATE name_decisions SET undone = 1 WHERE id = ?", (decision_id,))
    return {"undone": decision_id, "removed_masters": removed}


def reset_name_decisions(kind: str | None = None) -> dict[str, Any]:
    """一鍵還原某 kind（或全部）的名稱裁決。原始資料本就沒被動過。"""
    with connect() as conn:
        if kind:
            mids = [r["id"] for r in conn.execute("SELECT id FROM name_master WHERE kind = ?", (kind,)).fetchall()]
            n_alias = conn.execute("SELECT COUNT(*) AS n FROM name_aliases WHERE kind = ?", (kind,)).fetchone()["n"]
            conn.execute("DELETE FROM name_aliases WHERE kind = ?", (kind,))
            for mid in mids:
                conn.execute("DELETE FROM name_master WHERE id = ?", (mid,))
            conn.execute("UPDATE name_decisions SET undone = 1 WHERE kind = ? AND undone = 0", (kind,))
            return {"kind": kind, "removed_aliases": n_alias, "removed_masters": len(mids)}
        n_alias = conn.execute("SELECT COUNT(*) AS n FROM name_aliases").fetchone()["n"]
        n_master = conn.execute("SELECT COUNT(*) AS n FROM name_master").fetchone()["n"]
        conn.execute("DELETE FROM name_aliases")
        conn.execute("DELETE FROM name_master")
        conn.execute("UPDATE name_decisions SET undone = 1 WHERE undone = 0")
        return {"removed_aliases": n_alias, "removed_masters": n_master}


def resolve_name(kind: str, name: str) -> str:
    """把一個名稱解析成它的主名（未裁決則原樣回傳）。供之後報表/彙總用。"""
    with connect() as conn:
        amap = _name_alias_map(conn, kind)
    return amap.get(str(name).strip(), name)


def parse_headcount_xlsx(data: bytes) -> list[dict[str, Any]]:
    """解析『費用分攤表（人數）』.xlsx → 人數基準。認表頭『人數』欄那一列，讀 代號/部門/人數。"""
    import io
    import openpyxl

    def norm(v: Any) -> str:
        return " ".join(str(v).split()) if v is not None else ""

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out: list[dict[str, Any]] = []
    try:
        for sheet in wb.sheetnames:
            rows = [list(r) if r else [] for r in wb[sheet].iter_rows(values_only=True)]
            hdr = code_c = name_c = hc_c = None
            for i, r in enumerate(rows[:8]):
                if any(norm(c) == "人數" for c in r):
                    hdr = i
                    for j, c in enumerate(r):
                        k = norm(c)
                        if k in ("代號", "部門代號", "單位代碼"):
                            code_c = j
                        elif k in ("部門", "部門別", "單位", "單位名稱"):
                            name_c = j
                        elif k == "人數":
                            hc_c = j
                    break
            if hdr is None or hc_c is None:
                continue
            for r in rows[hdr + 1:]:
                name = norm(r[name_c]) if (name_c is not None and name_c < len(r)) else ""
                if name in ("合計", "小計"):
                    break
                if not name:
                    continue
                code = norm(r[code_c]) if (code_c is not None and code_c < len(r)) else ""
                try:
                    hc = int(float(r[hc_c])) if (hc_c < len(r) and r[hc_c] not in (None, "")) else 0
                except (TypeError, ValueError):
                    hc = 0
                out.append({"unit_code": code, "unit_name": name, "headcount": hc})
    finally:
        wb.close()
    return out


def commit_headcounts_import(records: list[dict[str, Any]], source_file: str = "") -> dict[str, Any]:
    """寫入人數基準：以 unit_code 為鍵 upsert（無代號者以 unit_name 為鍵）。
    source_file：來源 Excel 檔名，寫進每筆，供單位撞名清單指回來源。"""
    allowed = allowed_fields()["unit_headcounts"]
    source_file = (source_file or "").strip()
    with connect() as conn:
        existing: dict[str, int] = {}
        for r in conn.execute("SELECT id, unit_code, unit_name FROM unit_headcounts").fetchall():
            existing[(r["unit_code"] or "").strip() or ("＃" + (r["unit_name"] or ""))] = r["id"]
        created = updated = 0
        for rec in records:
            fields = {k: v for k, v in rec.items() if k in allowed}
            if source_file:
                fields["source_file"] = source_file
            key = str(rec.get("unit_code", "")).strip() or ("＃" + str(rec.get("unit_name", "")))
            if key in existing:
                rid = existing[key]
                upd = {k: v for k, v in fields.items() if k != "unit_code"}
                if upd:
                    conn.execute(f"UPDATE unit_headcounts SET {', '.join(f'{k} = ?' for k in upd)} WHERE id = ?",
                                 [*upd.values(), rid])
                updated += 1
            else:
                cols = ", ".join(fields)
                ph = ", ".join("?" for _ in fields)
                cur = conn.execute(f"INSERT INTO unit_headcounts ({cols}) VALUES ({ph})", list(fields.values()))
                existing[key] = cur.lastrowid
                created += 1
        return {"created_count": created, "updated_count": updated}


def list_headcounts() -> list[dict[str, Any]]:
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM unit_headcounts ORDER BY headcount DESC, id ASC").fetchall()]


def parse_category_shares_xlsx(data: bytes) -> list[dict[str, Any]]:
    """解析『資訊架構部費用分攤表』的『對照』表 → 類別基準。
    表頭第一列是類別（台股功能/複委託功能/台、複共用功能…），第二列標(現行)/(NEW)；
    只取 NEW 欄。每個有百分比的儲存格 → (類別, 代號, 名稱, 百分比)。"""
    import io
    import openpyxl

    def norm(v: Any) -> str:
        return " ".join(str(v).split()) if v is not None else ""

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out: list[dict[str, Any]] = []
    try:
        # 找「對照」表；找不到就退回最後一張
        sheet = next((s for s in wb.sheetnames if "對照" in s), wb.sheetnames[-1])
        rows = [list(r) if r else [] for r in wb[sheet].iter_rows(values_only=True)]
        if len(rows) < 3:
            return out
        hdr_cat, hdr_ver = rows[0], rows[1]
        width = max(len(hdr_cat), len(hdr_ver))
        # 類別名稱往右填滿（合併儲存格只有左上有值）
        cats, last = [], ""
        for j in range(width):
            v = norm(hdr_cat[j]) if j < len(hdr_cat) else ""
            if v:
                last = v
            cats.append(last)
        # 取 NEW 欄
        new_cols = [j for j in range(2, width)
                    if j < len(hdr_ver) and "NEW" in norm(hdr_ver[j]).upper()]
        for r in rows[2:]:
            code = norm(r[0]) if len(r) > 0 else ""
            name = norm(r[1]) if len(r) > 1 else ""
            if not code and not name:
                continue
            if code in ("合計", "小計") or name in ("合計", "小計"):
                break
            for j in new_cols:
                if j >= len(r) or r[j] in (None, ""):
                    continue
                try:
                    pct = float(r[j])
                except (TypeError, ValueError):
                    continue
                if pct <= 0:
                    continue
                out.append({"category": cats[j], "unit_code": code, "unit_name": name,
                            "share_pct": round(pct * 100, 4)})
    finally:
        wb.close()
    return out


def commit_category_shares_import(records: list[dict[str, Any]], source_file: str = "") -> dict[str, Any]:
    """寫入類別基準：以 (類別, 代號, 名稱) 為鍵 upsert。整批重匯前先清掉同來源舊資料避免殘留。"""
    allowed = allowed_fields()["category_shares"]
    source_file = (source_file or "").strip()
    with connect() as conn:
        existing = {(r["category"], r["unit_code"], r["unit_name"]): r["id"] for r in conn.execute(
            "SELECT id, category, unit_code, unit_name FROM category_shares").fetchall()}
        written = 0
        cats: set[str] = set()
        for rec in records:
            fields = {k: v for k, v in rec.items() if k in allowed}
            if source_file:
                fields["source_file"] = source_file
            key = (rec.get("category", ""), rec.get("unit_code", ""), rec.get("unit_name", ""))
            cats.add(rec.get("category", ""))
            if key in existing:
                upd = {k: v for k, v in fields.items() if k not in ("category", "unit_code", "unit_name")}
                if upd:
                    conn.execute(f"UPDATE category_shares SET {', '.join(f'{k} = ?' for k in upd)} WHERE id = ?",
                                 [*upd.values(), existing[key]])
            else:
                cols = ", ".join(fields)
                ph = ", ".join("?" for _ in fields)
                conn.execute(f"INSERT INTO category_shares ({cols}) VALUES ({ph})", list(fields.values()))
            written += 1
        return {"written": written, "categories": sorted(c for c in cats if c)}


def list_category_shares(category: str | None = None) -> dict[str, Any]:
    """類別基準：回各類別清單（含單位數、百分比合計），帶 category 則回該類別各單位明細。"""
    with connect() as conn:
        cats = [dict(r) for r in conn.execute(
            "SELECT category, COUNT(*) AS units, ROUND(SUM(share_pct), 2) AS pct_sum "
            "FROM category_shares GROUP BY category ORDER BY category").fetchall()]
        result: dict[str, Any] = {"categories": cats}
        if category is not None:
            result["shares"] = [dict(r) for r in conn.execute(
                "SELECT unit_code, unit_name, share_pct FROM category_shares "
                "WHERE category = ? ORDER BY share_pct DESC", (category,)).fetchall()]
        return result


def compute_budget_allocations(budget_id: int) -> dict[str, Any]:
    """依預算的 alloc_method 重算分攤並寫入 budget_allocations。
    headcount：amount = 費用 × 該單位人數 ÷ 總人數。
    category：amount = 費用 × 該類別下該單位%（整數化＋尾數承擔在 list_budget_allocations 處理）。"""
    with connect() as conn:
        budget = get_row(conn, "budgets", budget_id)
        method = str(budget.get("alloc_method") or "fixed")
        total = float(budget.get("amount") or 0)
        if method == "fixed":
            return {"method": "fixed", "written": 0, "note": "固定金額：沿用現有分攤，未重算"}
        if method == "category":
            cat = str(budget.get("alloc_category") or "").strip()
            if not cat:
                raise ValueError("請先選一個分攤類別（台股功能／複委託功能／台、複共用功能…）。")
            shares = conn.execute(
                "SELECT unit_code, unit_name, share_pct FROM category_shares "
                "WHERE category = ? AND share_pct > 0 ORDER BY share_pct DESC", (cat,)).fetchall()
            if not shares:
                raise ValueError(f"類別「{cat}」在基準表裡查不到資料，請先匯入類別基準（對照表）。")
            conn.execute("DELETE FROM budget_allocations WHERE budget_id = ?", (budget_id,))
            written = 0
            for seq, s in enumerate(shares, start=1):
                pct = float(s["share_pct"])
                conn.execute(
                    "INSERT INTO budget_allocations (budget_id, seq, unit_code, unit_name, share_pct, amount) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (budget_id, seq, s["unit_code"], s["unit_name"], round(pct, 2), round(total * pct / 100, 2)))
                written += 1
            write_audit_log(conn, "budgets", budget_id, "recompute-category", None,
                            {"category": cat, "units": written, "total": total})
            return {"method": "category", "written": written, "category": cat}
        if method != "headcount":
            raise ValueError(f"未知分攤方法：{method}")
        hcs = conn.execute(
            "SELECT unit_code, unit_name, headcount FROM unit_headcounts WHERE headcount > 0 "
            "ORDER BY headcount DESC, id ASC").fetchall()
        total_hc = sum(int(h["headcount"]) for h in hcs)
        if total_hc <= 0:
            raise ValueError("人數基準表是空的或總人數為 0，請先匯入人數表。")
        conn.execute("DELETE FROM budget_allocations WHERE budget_id = ?", (budget_id,))
        written = 0
        for seq, h in enumerate(hcs, start=1):
            hc = int(h["headcount"])
            conn.execute(
                "INSERT INTO budget_allocations (budget_id, seq, unit_code, unit_name, share_pct, amount) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (budget_id, seq, h["unit_code"], h["unit_name"],
                 round(hc / total_hc * 100, 2), round(total * hc / total_hc, 2)))
            written += 1
        write_audit_log(conn, "budgets", budget_id, "recompute-headcount", None,
                        {"units": written, "total": total, "total_headcount": total_hc})
        return {"method": "headcount", "written": written, "total_headcount": total_hc}


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
        # 每列：(表, 顯示代號欄, 顯示標題欄, 顯示明細欄, [額外可搜欄位…])
        # 額外欄位讓「負責人/廠商/備註」也搜得到（先前專案漏了 owner，搜負責人找不到即此故）。
        for table, fields in {
            "case": ("cases", "case_code", "title", "owner", ["note", "next_step"]),
            "contract": ("contracts", "contract_code", "contract_name", "vendor_name", []),
            "document": ("documents", "file_name", "document_type", "source_note", []),
            "budget": ("budgets", "budget_code", "category", "unit_name", ["note"]),
            "project": ("projects", "project_code", "project_name", "source", ["owner", "necessity", "note"]),
            "signoff": ("signoffs", "signoff_code", "subject", "applicant", ["note"]),
            "purchase": ("purchases", "purchase_code", "item_name", "vendor_name", ["note"]),
        }.items():
            source, code_field, title_field, extra_field, more_fields = fields
            search_fields = [code_field, title_field, extra_field, *more_fields]
            where_or = " OR ".join(f"{f} LIKE ?" for f in search_fields)
            sql = (
                f"SELECT id, {code_field} AS code, {title_field} AS title, {extra_field} AS detail "
                f"FROM {source} WHERE ({where_or})"
            )
            params: list[Any] = [pattern] * len(search_fields)
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
