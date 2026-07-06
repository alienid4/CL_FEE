import sqlite3


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cost_contract_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cost_item_code TEXT,
    cost_item_name TEXT NOT NULL,
    vendor_name TEXT,
    contract_amount REAL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signing_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_code TEXT,
    title TEXT NOT NULL,
    category TEXT,
    owner_department TEXT,
    owner_user TEXT,
    vendor_name TEXT,
    role TEXT DEFAULT 'manager',
    permission_scope TEXT DEFAULT 'department',
    amount REAL DEFAULT 0,
    budget_status TEXT DEFAULT 'pending',
    project_status TEXT DEFAULT 'pending',
    signing_status TEXT DEFAULT 'pending',
    approval_status TEXT DEFAULT 'pending',
    contract_status TEXT DEFAULT 'pending',
    procurement_status TEXT DEFAULT 'pending',
    payment_status TEXT DEFAULT 'pending',
    invoice_status TEXT DEFAULT 'pending',
    source_file_name TEXT,
    source_sheet TEXT,
    source_row INTEGER,
    source_column TEXT,
    source_value TEXT,
    cmdb_ci_id TEXT,
    cmdb_ci_name TEXT,
    cmdb_system_name TEXT,
    cmdb_service_name TEXT,
    cmdb_owner_department TEXT,
    cmdb_environment TEXT,
    cmdb_import_batch_id TEXT,
    cmdb_last_synced_at TEXT,
    cmdb_match_status TEXT DEFAULT 'reserved',
    cmdb_evidence_note TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    contract_code TEXT,
    contract_name TEXT NOT NULL,
    vendor_name TEXT,
    amount REAL DEFAULT 0,
    start_date TEXT,
    end_date TEXT,
    signing_case_id TEXT,
    procurement_no TEXT,
    owner_department TEXT,
    owner_user TEXT,
    permission_scope TEXT DEFAULT 'department',
    cmdb_ci_id TEXT,
    cmdb_ci_name TEXT,
    cmdb_system_name TEXT,
    cmdb_service_name TEXT,
    cmdb_owner_department TEXT,
    cmdb_environment TEXT,
    cmdb_import_batch_id TEXT,
    cmdb_last_synced_at TEXT,
    cmdb_match_status TEXT DEFAULT 'reserved',
    cmdb_evidence_note TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES signing_cases(id)
);

CREATE TABLE IF NOT EXISTS budget_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_year INTEGER NOT NULL,
    category TEXT,
    item_name TEXT NOT NULL,
    owner_group TEXT,
    budget_amount REAL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    contract_id INTEGER,
    payment_phase TEXT,
    planned_payment_date TEXT,
    actual_payment_date TEXT,
    payment_month TEXT,
    payment_amount REAL DEFAULT 0,
    payment_condition TEXT,
    invoice_status TEXT DEFAULT 'not_received',
    vendor_name TEXT,
    source_file_name TEXT,
    source_sheet TEXT,
    source_row INTEGER,
    source_column TEXT,
    source_value TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    contract_id INTEGER,
    payment_id INTEGER,
    invoice_no TEXT,
    vendor_name TEXT,
    invoice_date TEXT,
    invoice_month TEXT,
    invoice_amount REAL DEFAULT 0,
    tax_amount REAL DEFAULT 0,
    received_date TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    source_file_name TEXT,
    source_sheet TEXT,
    source_row INTEGER,
    source_column TEXT,
    source_value TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES signing_cases(id),
    FOREIGN KEY(contract_id) REFERENCES contracts(id),
    FOREIGN KEY(payment_id) REFERENCES payment_schedules(id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    contract_id INTEGER,
    payment_id INTEGER,
    invoice_id INTEGER,
    file_name TEXT NOT NULL,
    document_type TEXT NOT NULL DEFAULT 'other',
    parse_status TEXT NOT NULL DEFAULT 'not_parsed',
    page_no TEXT,
    evidence_text TEXT,
    source_note TEXT,
    uploaded_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file_name TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'excel',
    status TEXT NOT NULL DEFAULT 'uploaded',
    row_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS field_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    source_field TEXT NOT NULL,
    target_table TEXT NOT NULL,
    target_field TEXT NOT NULL,
    transform_note TEXT,
    version TEXT NOT NULL DEFAULT 'v1',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    sheet_name TEXT,
    row_number INTEGER,
    raw_json TEXT NOT NULL DEFAULT '{}',
    validation_status TEXT NOT NULL DEFAULT 'pending',
    validation_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(batch_id) REFERENCES import_batches(id)
);

CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    title TEXT NOT NULL,
    owner_user TEXT,
    owner_department TEXT,
    due_date TEXT,
    priority TEXT NOT NULL DEFAULT 'medium',
    task_type TEXT NOT NULL DEFAULT 'follow_up',
    result_note TEXT,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES signing_cases(id)
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    reminder_type TEXT NOT NULL,
    remind_at TEXT,
    target_user TEXT,
    target_role TEXT,
    frequency TEXT DEFAULT 'once',
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES signing_cases(id)
);

CREATE TABLE IF NOT EXISTS data_quality_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    severity TEXT NOT NULL DEFAULT 'warning',
    rule_code TEXT NOT NULL,
    message TEXT NOT NULL,
    source_file_name TEXT,
    source_sheet TEXT,
    source_row INTEGER,
    source_column TEXT,
    original_value TEXT,
    reviewed_by TEXT,
    reviewed_at TEXT,
    review_note TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES signing_cases(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    action TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'system',
    detail TEXT,
    created_at TEXT NOT NULL
);
"""


TABLE_COLUMNS: dict[str, dict[str, str]] = {
    "signing_cases": {
        "owner_department": "TEXT",
        "owner_user": "TEXT",
        "vendor_name": "TEXT",
        "role": "TEXT DEFAULT 'manager'",
        "permission_scope": "TEXT DEFAULT 'department'",
        "budget_status": "TEXT DEFAULT 'pending'",
        "project_status": "TEXT DEFAULT 'pending'",
        "signing_status": "TEXT DEFAULT 'pending'",
        "approval_status": "TEXT DEFAULT 'pending'",
        "contract_status": "TEXT DEFAULT 'pending'",
        "procurement_status": "TEXT DEFAULT 'pending'",
        "payment_status": "TEXT DEFAULT 'pending'",
        "invoice_status": "TEXT DEFAULT 'pending'",
        "source_file_name": "TEXT",
        "source_sheet": "TEXT",
        "source_row": "INTEGER",
        "source_column": "TEXT",
        "source_value": "TEXT",
        "cmdb_ci_id": "TEXT",
        "cmdb_ci_name": "TEXT",
        "cmdb_system_name": "TEXT",
        "cmdb_service_name": "TEXT",
        "cmdb_owner_department": "TEXT",
        "cmdb_environment": "TEXT",
        "cmdb_import_batch_id": "TEXT",
        "cmdb_last_synced_at": "TEXT",
        "cmdb_match_status": "TEXT DEFAULT 'reserved'",
        "cmdb_evidence_note": "TEXT",
    },
    "contracts": {
        "case_id": "INTEGER",
        "signing_case_id": "TEXT",
        "procurement_no": "TEXT",
        "owner_department": "TEXT",
        "owner_user": "TEXT",
        "permission_scope": "TEXT DEFAULT 'department'",
        "cmdb_ci_id": "TEXT",
        "cmdb_ci_name": "TEXT",
        "cmdb_system_name": "TEXT",
        "cmdb_service_name": "TEXT",
        "cmdb_owner_department": "TEXT",
        "cmdb_environment": "TEXT",
        "cmdb_import_batch_id": "TEXT",
        "cmdb_last_synced_at": "TEXT",
        "cmdb_match_status": "TEXT DEFAULT 'reserved'",
        "cmdb_evidence_note": "TEXT",
    },
    "payment_schedules": {
        "payment_phase": "TEXT",
        "planned_payment_date": "TEXT",
        "actual_payment_date": "TEXT",
        "payment_condition": "TEXT",
        "vendor_name": "TEXT",
        "source_file_name": "TEXT",
        "source_sheet": "TEXT",
        "source_row": "INTEGER",
        "source_column": "TEXT",
        "source_value": "TEXT",
    },
    "documents": {
        "payment_id": "INTEGER",
        "invoice_id": "INTEGER",
        "page_no": "TEXT",
        "evidence_text": "TEXT",
        "uploaded_by": "TEXT",
    },
}


def _ensure_columns(conn: sqlite3.Connection) -> None:
    for table, columns in TABLE_COLUMNS.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for column, definition in columns.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    _ensure_columns(conn)
