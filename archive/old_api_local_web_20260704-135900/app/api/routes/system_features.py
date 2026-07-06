from fastapi import APIRouter, Query

from app.db.session import db_session
from app.repositories.sqlite_repository import rows_to_dicts


router = APIRouter()

DONE_STATUSES = {"done", "completed", "closed", "已完成", "完成"}
VOID_STATUSES = {"void", "作廢"}


def _is_done(status: str | None) -> bool:
    return (status or "").lower() in DONE_STATUSES or (status or "") in DONE_STATUSES


def _status_label(status: str | None) -> str:
    if not status:
        return "未開始"
    if _is_done(status):
        return "完成"
    if status in {"not_applicable", "n/a", "不適用"}:
        return "不適用"
    if status in {"exception", "overdue", "異常", "逾期"}:
        return "異常"
    if status in {"pending", "waiting", "待確認", "待補"}:
        return "待確認"
    return "進行中"


def _status_tone(label: str) -> str:
    return {
        "完成": "done",
        "不適用": "muted",
        "異常": "danger",
        "待確認": "warning",
        "進行中": "active",
        "未開始": "muted",
    }.get(label, "active")


def _timeline_for_case(case: dict, payments: list[dict], contracts: list[dict], documents: list[dict]) -> list[dict]:
    has_contract = bool(contracts)
    has_payment = bool(payments)
    has_document = bool(documents)
    invoice_done = any(row.get("invoice_status") in {"received", "paid", "已收", "已付款"} for row in payments)

    nodes = [
        ("預算", "完成" if case.get("amount", 0) else "待確認", "Case 金額或年度預算來源"),
        ("專案", _status_label(case.get("status")), "案件主檔狀態"),
        ("簽呈", "完成" if has_document else "待確認", "簽呈或附件是否已關聯"),
        ("核准", "完成" if _is_done(case.get("status")) else "進行中", "案件是否已核准或結案"),
        ("合約", "完成" if has_contract else "待確認", "是否有合約資料"),
        ("請購", "不適用" if not has_contract else "進行中", "請購資料待 Excel 範本確認"),
        ("付款", "完成" if has_payment and all(_is_done(row.get("status")) for row in payments) else ("進行中" if has_payment else "未開始"), "付款排程與付款狀態"),
        ("發票", "完成" if invoice_done else ("待確認" if has_payment else "未開始"), "發票狀態與付款排程關聯"),
    ]
    return [
        {"step": step, "status": status, "tone": _status_tone(status), "evidence": evidence}
        for step, status, evidence in nodes
    ]


def _case_evidence(case_id: int, documents: list[dict], import_rows: list[dict], audit_logs: list[dict]) -> list[dict]:
    evidence = []
    for doc in documents:
        evidence.append(
            {
                "type": "document",
                "title": doc.get("file_name"),
                "source": doc.get("document_type"),
                "detail": doc.get("source_note") or "文件已關聯案件",
            }
        )
    for row in import_rows:
        evidence.append(
            {
                "type": "excel_row",
                "title": f"{row.get('sheet_name') or '未命名 Sheet'} 第 {row.get('row_number') or '-'} 列",
                "source": f"import_rows#{row.get('id')}",
                "detail": row.get("validation_message") or row.get("raw_json"),
            }
        )
    for log in audit_logs:
        evidence.append(
            {
                "type": "audit",
                "title": f"{log.get('action')} by {log.get('actor')}",
                "source": log.get("created_at"),
                "detail": log.get("detail"),
            }
        )
    if not evidence:
        evidence.append(
            {
                "type": "system",
                "title": f"Case #{case_id} 尚未建立外部舉證",
                "source": "system",
                "detail": "匯入 Excel、附件或人工覆核後會在此形成舉證鏈。",
            }
        )
    return evidence


@router.get("/case-360/{case_id}")
def case_360(case_id: int) -> dict:
    with db_session() as conn:
        case = conn.execute("SELECT * FROM signing_cases WHERE id = ?", (case_id,)).fetchone()
        payments = rows_to_dicts(
            conn.execute("SELECT * FROM payment_schedules WHERE case_id = ? ORDER BY payment_month, id", (case_id,)).fetchall()
        )
        contracts = rows_to_dicts(
            conn.execute(
                """
                SELECT DISTINCT c.*
                FROM contracts c
                LEFT JOIN payment_schedules p ON p.contract_id = c.id
                WHERE p.case_id = ?
                ORDER BY c.id
                """,
                (case_id,),
            ).fetchall()
        )
        documents = rows_to_dicts(
            conn.execute("SELECT * FROM documents WHERE case_id = ? ORDER BY id DESC", (case_id,)).fetchall()
        )
        import_rows = rows_to_dicts(
            conn.execute(
                """
                SELECT *
                FROM import_rows
                WHERE raw_json LIKE ?
                ORDER BY id DESC
                LIMIT 20
                """,
                (f"%{case_id}%",),
            ).fetchall()
        )
        audit_logs = rows_to_dicts(
            conn.execute(
                """
                SELECT *
                FROM audit_logs
                WHERE entity_type IN ('signing_case', 'payment_schedule', 'contract', 'document')
                  AND (entity_id = ? OR detail LIKE ?)
                ORDER BY id DESC
                LIMIT 20
                """,
                (case_id, f"%{case_id}%"),
            ).fetchall()
        )

    case_data = dict(case) if case else None
    timeline = _timeline_for_case(case_data or {"status": "missing"}, payments, contracts, documents)
    return {
        "ok": True,
        "data": {
            "case": case_data,
            "contracts": contracts,
            "payments": payments,
            "documents": documents,
            "timeline": timeline,
            "evidence": _case_evidence(case_id, documents, import_rows, audit_logs),
            "totals": {
                "case_amount": (case_data or {}).get("amount", 0) or 0,
                "contract_amount": sum(row.get("amount") or 0 for row in contracts),
                "payment_amount": sum(row.get("payment_amount") or 0 for row in payments),
            },
        },
    }


@router.get("/drilldown")
def drilldown(
    metric: str = Query(...),
    q: str | None = None,
    owner: str | None = None,
    vendor: str | None = None,
    month: str | None = None,
    amount_min: float | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    filters: list[str] = []
    params: list[object] = []
    title = metric
    order_sql = " ORDER BY amount DESC, id DESC LIMIT ?"

    if metric in {"active_cases", "unfinished_cases", "cases"}:
        table_sql = "SELECT 'case' AS item_type, id, case_code AS code, title, category AS owner, NULL AS vendor, amount, status FROM signing_cases"
        if metric == "unfinished_cases":
            filters.append("LOWER(status) NOT IN ('done', 'completed', 'closed', 'void')")
            title = "未完成案件"
        elif metric == "active_cases":
            filters.append("LOWER(status) != 'void'")
            title = "有效案件"
        if q:
            filters.append("(title LIKE ? OR case_code LIKE ? OR category LIKE ?)")
            params.extend([f"%{q}%"] * 3)
        if owner:
            filters.append("category LIKE ?")
            params.append(f"%{owner}%")
        if amount_min is not None:
            filters.append("amount >= ?")
            params.append(amount_min)
    elif metric in {"payments", "invoice_month"}:
        table_sql = """
            SELECT 'payment' AS item_type, p.id, CAST(p.id AS TEXT) AS code,
                   COALESCE(c.contract_name, s.title, '付款排程') AS title,
                   s.category AS owner, c.vendor_name AS vendor,
                   p.payment_amount AS amount, p.status,
                   p.payment_month, p.invoice_status
            FROM payment_schedules p
            LEFT JOIN signing_cases s ON s.id = p.case_id
            LEFT JOIN contracts c ON c.id = p.contract_id
        """
        title = "付款與發票明細"
        order_sql = " ORDER BY p.payment_amount DESC, p.id DESC LIMIT ?"
        if month:
            filters.append("p.payment_month = ?")
            params.append(month)
        if q:
            filters.append("(c.contract_name LIKE ? OR s.title LIKE ? OR c.vendor_name LIKE ? OR p.invoice_status LIKE ?)")
            params.extend([f"%{q}%"] * 4)
        if vendor:
            filters.append("c.vendor_name LIKE ?")
            params.append(f"%{vendor}%")
        if amount_min is not None:
            filters.append("p.payment_amount >= ?")
            params.append(amount_min)
    elif metric in {"vendors", "vendor_amount"}:
        table_sql = """
            SELECT 'vendor' AS item_type, MIN(id) AS id, vendor_name AS code,
                   vendor_name AS title, NULL AS owner, vendor_name AS vendor,
                   SUM(amount) AS amount, COUNT(*) || ' 件合約' AS status
            FROM contracts
        """
        if vendor or q:
            filters.append("vendor_name LIKE ?")
            params.append(f"%{vendor or q}%")
        suffix = " WHERE " + " AND ".join(filters) if filters else ""
        sql = table_sql + suffix + " GROUP BY vendor_name ORDER BY amount DESC LIMIT ?"
        params.append(limit)
        with db_session() as conn:
            rows = rows_to_dicts(conn.execute(sql, params).fetchall())
        return {"ok": True, "data": {"title": "廠商金額下鑽", "metric": metric, "rows": rows}}
    else:
        table_sql = "SELECT 'case' AS item_type, id, case_code AS code, title, category AS owner, NULL AS vendor, amount, status FROM signing_cases"
        title = "案件明細"

    sql = table_sql
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += order_sql
    params.append(limit)
    with db_session() as conn:
        rows = rows_to_dicts(conn.execute(sql, params).fetchall())
    return {"ok": True, "data": {"title": title, "metric": metric, "rows": rows}}


@router.get("/timeline")
def timelines(limit: int = Query(default=30, ge=1, le=100)) -> dict:
    with db_session() as conn:
        cases = rows_to_dicts(conn.execute("SELECT * FROM signing_cases ORDER BY id DESC LIMIT ?", (limit,)).fetchall())
        payload = []
        for case in cases:
            case_id = case["id"]
            payments = rows_to_dicts(conn.execute("SELECT * FROM payment_schedules WHERE case_id = ?", (case_id,)).fetchall())
            contracts = rows_to_dicts(
                conn.execute(
                    """
                    SELECT DISTINCT c.*
                    FROM contracts c
                    LEFT JOIN payment_schedules p ON p.contract_id = c.id
                    WHERE p.case_id = ?
                    """,
                    (case_id,),
                ).fetchall()
            )
            documents = rows_to_dicts(conn.execute("SELECT * FROM documents WHERE case_id = ?", (case_id,)).fetchall())
            payload.append({"case": case, "timeline": _timeline_for_case(case, payments, contracts, documents)})
    return {"ok": True, "data": payload}


@router.get("/priority-matrix")
def priority_matrix(limit: int = Query(default=30, ge=1, le=100)) -> dict:
    with db_session() as conn:
        rows = rows_to_dicts(
            conn.execute(
                """
                SELECT s.id, s.case_code, s.title, s.category AS owner, s.amount, s.status,
                       COALESCE(SUM(p.payment_amount), 0) AS payment_amount,
                       COUNT(p.id) AS payment_count
                FROM signing_cases s
                LEFT JOIN payment_schedules p ON p.case_id = s.id
                GROUP BY s.id
                ORDER BY s.amount DESC, s.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        )
    bubbles = []
    for row in rows:
        amount = row.get("amount") or row.get("payment_amount") or 0
        status = _status_label(row.get("status"))
        urgency = 80 if status in {"異常", "待確認"} else 45 if status == "進行中" else 20
        impact = min(100, max(10, int(amount / 10000))) if amount else 10
        bubbles.append(
            {
                "case_id": row["id"],
                "label": row["title"],
                "owner": row.get("owner") or "未指派",
                "amount": amount,
                "urgency": urgency,
                "impact": impact,
                "status": status,
                "tone": _status_tone(status),
                "reason": "依狀態、金額與付款筆數排序",
            }
        )
    return {"ok": True, "data": {"bubbles": bubbles}}


@router.get("/owners")
def owners(q: str | None = None, limit: int = Query(default=100, ge=1, le=500)) -> dict:
    params: list[object] = []
    where = ""
    if q:
        where = "WHERE category LIKE ?"
        params.append(f"%{q}%")
    params.append(limit)
    with db_session() as conn:
        rows = rows_to_dicts(
            conn.execute(
                f"""
                SELECT COALESCE(category, '未指派') AS owner,
                       COUNT(*) AS case_count,
                       SUM(amount) AS total_amount,
                       SUM(CASE WHEN LOWER(status) IN ('done', 'completed', 'closed') THEN 1 ELSE 0 END) AS done_count,
                       SUM(CASE WHEN LOWER(status) NOT IN ('done', 'completed', 'closed', 'void') THEN 1 ELSE 0 END) AS open_count
                FROM signing_cases
                {where}
                GROUP BY COALESCE(category, '未指派')
                ORDER BY open_count DESC, total_amount DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        )
    return {"ok": True, "data": rows}


@router.get("/vendors")
def vendors(q: str | None = None, limit: int = Query(default=100, ge=1, le=500)) -> dict:
    params: list[object] = []
    where = ""
    if q:
        where = "WHERE vendor_name LIKE ?"
        params.append(f"%{q}%")
    params.append(limit)
    with db_session() as conn:
        rows = rows_to_dicts(
            conn.execute(
                f"""
                SELECT COALESCE(vendor_name, '未填廠商') AS vendor,
                       COUNT(*) AS contract_count,
                       SUM(amount) AS contract_amount,
                       MIN(start_date) AS first_start_date,
                       MAX(end_date) AS last_end_date
                FROM contracts
                {where}
                GROUP BY COALESCE(vendor_name, '未填廠商')
                ORDER BY contract_amount DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        )
    return {"ok": True, "data": rows}


@router.get("/rules")
def rules() -> dict:
    return {
        "ok": True,
        "data": [
            {"rule": "完成", "description": "狀態為 done、completed、closed、已完成或完成。"},
            {"rule": "未完成", "description": "有效案件中狀態尚未完成或結案。"},
            {"rule": "不適用", "description": "該流程節點無合約、請購或付款資料時標示，不納入完成率。"},
            {"rule": "異常", "description": "狀態為 exception、overdue、異常或逾期，需主管確認。"},
            {"rule": "舉證", "description": "所有金額、狀態與關聯需可追到 Excel、文件或異動紀錄。"},
        ],
    }


@router.get("/excel-operations")
def excel_operations() -> dict:
    return {
        "ok": True,
        "data": {
            "templates": ["年度預算", "專案清單", "簽呈 / 上簽", "合約", "請購", "付款排程", "發票", "資料檢核"],
            "import_modes": ["新增批次", "欄位對應", "資料檢核", "人工確認", "正式入庫"],
            "export_modes": ["匯出目前篩選", "匯出完整資料", "匯出含舉證資料", "匯出差異比較"],
            "note": "實際 Excel 欄位需依使用者範本建立 mapping，避免格式一變就改程式。",
        },
    }

@router.get("/cmdb-integration")
def cmdb_integration() -> dict:
    return {
        "ok": True,
        "data": {
            "phase": "reserved",
            "strategy": [
                {
                    "phase": 1,
                    "name": "費用合約控管本體",
                    "description": "先完成費用、合約、案件、付款、發票與舉證流程；資料模型預留 CMDB 關聯欄位。",
                    "status": "planned",
                },
                {
                    "phase": 2,
                    "name": "CMDB 查詢或匯入",
                    "description": "待 CMDB 欄位、API 或匯出檔格式確認後，支援查詢、同步、匯入與差異比對。",
                    "status": "reserved",
                },
            ],
            "reserved_fields": [
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
            ],
            "future_sources": ["CMDB API", "CMDB Excel 匯出", "CMDB CSV 匯出", "人工關聯"],
            "supported_targets": ["Case 360", "專案", "合約", "付款排程", "文件舉證", "搜尋", "處理優先矩陣"],
            "acceptance": [
                "第一階段資料不需要 CMDB 也能運作。",
                "Case、合約、專案可保留 CMDB CI 關聯欄位。",
                "第二階段接入後可從 Case 360 看到 CMDB 資產或服務資訊。",
                "CMDB 查詢或匯入結果需保留來源、同步時間與比對狀態。",
            ],
        },
    }
