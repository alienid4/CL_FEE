"""測試種子資料（demo）：一鍵載入 / 一鍵清空。

安全設計（避免跟真資料混淆）：
- 每一筆都帶明顯標記：case_code / contract_code / file_name 以 "DEMO-" 開頭，
  標題以「［測試］」開頭。使用者一眼就能分辨這是測試資料。
- 清空只刪帶 DEMO- 標記的列（付款依附在 DEMO 合約上，用子查詢定位），
  依外鍵順序刪除；**絕不碰任何非 DEMO- 的真資料**。
- 載入採「先清空再插入」，重複點不會產生重複資料。
"""
from __future__ import annotations

from typing import Any

from datetime import date, timedelta

from app import store

DEMO_PREFIX = "DEMO-"


def _next_month() -> str:
    today = date.today()
    if today.month == 12:
        return f"{today.year + 1}-01"
    return f"{today.year}-{today.month + 1:02d}"


def _offset_date(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


# demo 案件的預計完成日（相對今天算，永遠能展示催辦）：index -> 天數偏移
_CASE_DUE_OFFSETS = {0: -6, 2: 7}  # DEMO-C01 逾期 6 天、DEMO-C03 還剩 7 天

# 說明：日期挑選讓 demo 能展示「到期提醒」與「月度支出」等真功能。
_CASES = [
    {"case_code": "DEMO-C01", "title": "［測試］機房網路擴充案", "status": "reviewing",
     "amount": 1200000, "owner": "ap02", "risk_level": "medium",
     "note": "示範資料，可一鍵清除", "next_step": "等主管簽核"},
    {"case_code": "DEMO-C02", "title": "［測試］資安設備採購", "status": "approved",
     "amount": 3500000, "owner": "ap03", "risk_level": "high",
     "note": "示範資料，可一鍵清除", "next_step": "安排付款排程"},
    {"case_code": "DEMO-C03", "title": "［測試］VPN 服務續約", "status": "draft",
     "amount": 480000, "owner": "ap03", "risk_level": "low",
     "note": "示範資料，可一鍵清除", "next_step": "補齊廠商報價"},
]

# (contract payload, 用哪個 case 的 index 當 case_id)
_CONTRACTS = [
    ({"contract_code": "DEMO-K01", "contract_name": "［測試］網路基礎架構服務契約",
      "vendor_name": "示範廠商甲", "amount": 1200000, "status": "active",
      "end_date": "2026-08-31"}, 0),  # 90 天內到期 → 觸發到期提醒
    ({"contract_code": "DEMO-K02", "contract_name": "［測試］資安設備維護合約",
      "vendor_name": "示範廠商乙", "amount": 3500000, "status": "active",
      "end_date": "2027-01-31"}, 1),
]

# (payment payload, 用哪個 contract 的 index 當 contract_id)
_PAYMENTS = [
    ({"payment_month": "2026-05", "payment_amount": 400000,
      "invoice_status": "verified", "status": "closed"}, 0),
    ({"payment_month": "2026-06", "payment_amount": 400000,
      "invoice_status": "received", "status": "scheduled"}, 0),
    ({"payment_month": "2026-06", "payment_amount": 1750000,
      "invoice_status": "not_received", "status": "pending"}, 1),
]

_DOCUMENTS = [
    ({"file_name": "DEMO-合約掃描.pdf", "document_type": "contract",
      "source_note": "［測試資料］", "status": "active"}, 0, 0),  # case_idx, contract_idx
]


def clear_demo_data() -> dict[str, int]:
    """只刪帶 DEMO- 標記的列，依外鍵順序，回傳各表刪除筆數。"""
    removed: dict[str, int] = {}
    with store.connect() as conn:
        cur = conn.execute("DELETE FROM documents WHERE file_name LIKE ?", (DEMO_PREFIX + "%",))
        removed["documents"] = cur.rowcount
        cur = conn.execute(
            "DELETE FROM payments WHERE contract_id IN "
            "(SELECT id FROM contracts WHERE contract_code LIKE ?)",
            (DEMO_PREFIX + "%",),
        )
        removed["payments"] = cur.rowcount
        cur = conn.execute("DELETE FROM contracts WHERE contract_code LIKE ?", (DEMO_PREFIX + "%",))
        removed["contracts"] = cur.rowcount
        cur = conn.execute(
            "DELETE FROM budget_periods WHERE budget_id IN "
            "(SELECT id FROM budgets WHERE budget_code LIKE ?)", (DEMO_PREFIX + "%",))
        removed["budget_periods"] = cur.rowcount
        cur = conn.execute(
            "DELETE FROM budget_allocations WHERE budget_id IN "
            "(SELECT id FROM budgets WHERE budget_code LIKE ?)", (DEMO_PREFIX + "%",))
        removed["budget_allocations"] = cur.rowcount
        cur = conn.execute("DELETE FROM budgets WHERE budget_code LIKE ?", (DEMO_PREFIX + "%",))
        removed["budgets"] = cur.rowcount
        cur = conn.execute("DELETE FROM cases WHERE case_code LIKE ?", (DEMO_PREFIX + "%",))
        removed["cases"] = cur.rowcount
    return removed


def load_demo_data() -> dict[str, int]:
    """先清空舊 demo 再插入一組完整示範資料，回傳各表載入筆數。"""
    clear_demo_data()
    case_ids = []
    for idx, payload in enumerate(_CASES):
        row = dict(payload)
        if idx in _CASE_DUE_OFFSETS:
            row["due_date"] = _offset_date(_CASE_DUE_OFFSETS[idx])  # 供催辦清單展示
        case_ids.append(store.insert_row("cases", row)["id"])

    contract_ids: list[int] = []
    for payload, case_idx in _CONTRACTS:
        row = store.insert_row("contracts", {**payload, "case_id": case_ids[case_idx]})
        contract_ids.append(row["id"])

    for payload, contract_idx in _PAYMENTS:
        store.insert_row("payments", {**payload, "contract_id": contract_ids[contract_idx]})

    # 額外一筆「下個月」的付款，讓 CIO 決策總覽的「下月應付」有東西可看（相對今天動態計算）。
    # 掛在 DEMO-K02（案 DEMO-C02 為 approved）——CIO 金額只算已核准案件，未核准的不會顯示。
    store.insert_row("payments", {
        "contract_id": contract_ids[1],
        "payment_month": _next_month(),
        "payment_amount": 800000,
        "invoice_status": "not_received",
        "status": "pending",
    })

    for payload, case_idx, contract_idx in _DOCUMENTS:
        store.insert_row("documents", {
            **payload,
            "case_id": case_ids[case_idx],
            "contract_id": contract_ids[contract_idx],
        })

    # L3 年度費用比較示範（比照真實 Excel：114 空、115 有值、116 續增）
    bud_id = store.insert_row("budgets", {
        "budget_code": DEMO_PREFIX + "BUD-ANNUAL",
        "category": "［測試］修繕維護費-資訊",
        "expense_detail": "開放系統平台主機APT防護系統",
        "unit_name": "資訊管理處",
        "fill_dept": "資訊管理處",
        "estimator": "林○○",
        "fiscal_year": "115",
        "amount": 878616,
        "case_id": case_ids[0],
    })["id"]
    _periods = [
        ("114", "1-9月", 0), ("114", "10-12月", 0),
        ("115", "1-9月", 658962), ("115", "10-12月", 219654),
        ("116", "1-9月", 700000), ("116", "10-12月", 250000),
    ]
    # 部門分攤示範（Stage 4 整合用）：合計≈全年度 878,616
    _allocs = [("8101", "資訊管理處", 527170), ("8009", "資訊安全部", 219654), ("8553", "數位開發部", 131792)]
    with store.connect() as conn:
        for fy, period, amt in _periods:
            conn.execute(
                "INSERT INTO budget_periods (budget_id, fiscal_year, period, amount) VALUES (?, ?, ?, ?)",
                (bud_id, fy, period, amt))
        for uc, un, amt in _allocs:
            conn.execute(
                "INSERT INTO budget_allocations (budget_id, unit_code, unit_name, amount, share_pct) VALUES (?, ?, ?, ?, ?)",
                (bud_id, uc, un, amt, round(amt / 878616 * 100, 2)))

    return {
        "cases": len(_CASES),
        "contracts": len(_CONTRACTS),
        "payments": len(_PAYMENTS) + 1,  # 含動態的下月付款
        "documents": len(_DOCUMENTS),
        "budgets": 1,
        "budget_periods": len(_periods),
    }


def demo_counts() -> dict[str, int]:
    """目前資料庫裡帶 DEMO- 標記的列數（給前端顯示狀態用）。"""
    with store.connect() as conn:
        def _count(sql: str) -> int:
            return conn.execute(sql, (DEMO_PREFIX + "%",)).fetchone()["n"]
        return {
            "cases": _count("SELECT COUNT(*) AS n FROM cases WHERE case_code LIKE ?"),
            "contracts": _count("SELECT COUNT(*) AS n FROM contracts WHERE contract_code LIKE ?"),
            "documents": _count("SELECT COUNT(*) AS n FROM documents WHERE file_name LIKE ?"),
        }


# ── AI 自測資料清除：跟「示範資料」是兩回事 ──
# 示範資料＝少量精選、給使用者展示功動用，維持不動。
# AI 測試資料＝AI 自測（cl-fee-selftest）過程中隨手建的，數量不定、跨全部模組，需要通用清除機制。
# 往後 AI 自測一律用 AITEST- 前綴（唯一標準）；以下舊前綴是這次上線前累積的歷史殘留，
# 一併收錄以便一次清乾淨——之後應該不會再長出新的舊前綴資料。
TEST_DATA_PREFIXES = ("AITEST-", "測-", "SELFTEST", "PROOF", "E2E", "test", "K-SELFTEST", "K-E2E", "K-CHAIN")


def _test_case_ids(conn) -> list[int]:
    clauses = " OR ".join("case_code LIKE ?" for _ in TEST_DATA_PREFIXES)
    params = [p + "%" for p in TEST_DATA_PREFIXES]
    return [r["id"] for r in conn.execute(f"SELECT id FROM cases WHERE {clauses}", params).fetchall()]


def _test_row_ids(conn, table: str, code_col: str, case_ids: list[int]) -> list[int]:
    """一筆資料算「AI 測試資料」：自己的代碼開頭符合已知前綴，或掛在測試案件的 case_id 底下。"""
    code_clauses = " OR ".join(f"{code_col} LIKE ?" for _ in TEST_DATA_PREFIXES)
    params: list[Any] = [p + "%" for p in TEST_DATA_PREFIXES]
    sql = f"SELECT id FROM {table} WHERE ({code_clauses})"
    if case_ids:
        placeholders = ",".join("?" * len(case_ids))
        sql += f" OR case_id IN ({placeholders})"
        params += case_ids
    return [r["id"] for r in conn.execute(sql, params).fetchall()]


def test_data_counts() -> dict[str, int]:
    """目前資料庫裡符合 AI 測試資料判定規則的列數（各表獨立計算，不含依賴表）。"""
    with store.connect() as conn:
        case_ids = _test_case_ids(conn)
        return {
            "cases": len(case_ids),
            "contracts": len(_test_row_ids(conn, "contracts", "contract_code", case_ids)),
            "purchases": len(_test_row_ids(conn, "purchases", "purchase_code", case_ids)),
            "signoffs": len(_test_row_ids(conn, "signoffs", "signoff_code", case_ids)),
            "budgets": len(_test_row_ids(conn, "budgets", "budget_code", case_ids)),
            "projects": len(_test_row_ids(conn, "projects", "project_code", case_ids)),
        }


def clear_test_data() -> dict[str, int]:
    """清掉所有 AI 測試資料（判定規則見 _test_row_ids），依外鍵順序刪除，回傳各表刪除筆數。
    絕不碰真實資料——已用現有 preview.db 驗證這條規則對目前資料無孤兒風險。"""
    removed: dict[str, int] = {}
    with store.connect() as conn:
        case_ids = _test_case_ids(conn)
        contract_ids = _test_row_ids(conn, "contracts", "contract_code", case_ids)
        purchase_ids = _test_row_ids(conn, "purchases", "purchase_code", case_ids)
        signoff_ids = _test_row_ids(conn, "signoffs", "signoff_code", case_ids)
        budget_ids = _test_row_ids(conn, "budgets", "budget_code", case_ids)
        project_ids = _test_row_ids(conn, "projects", "project_code", case_ids)

        def _delete_in(table: str, ids: list[int]) -> int:
            if not ids:
                return 0
            placeholders = ",".join("?" * len(ids))
            cur = conn.execute(f"DELETE FROM {table} WHERE id IN ({placeholders})", ids)
            return cur.rowcount

        def _delete_by_parent(table: str, parent_col: str, parent_ids: list[int]) -> int:
            if not parent_ids:
                return 0
            placeholders = ",".join("?" * len(parent_ids))
            cur = conn.execute(f"DELETE FROM {table} WHERE {parent_col} IN ({placeholders})", parent_ids)
            return cur.rowcount

        removed["payments"] = _delete_by_parent("payments", "contract_id", contract_ids)
        removed["project_items"] = _delete_by_parent("project_items", "project_id", project_ids)
        removed["budget_allocations"] = _delete_by_parent("budget_allocations", "budget_id", budget_ids)
        removed["budget_periods"] = _delete_by_parent("budget_periods", "budget_id", budget_ids)
        doc_ids = list({
            r["id"] for r in conn.execute(
                "SELECT id FROM documents WHERE case_id IN ({}) OR contract_id IN ({})".format(
                    ",".join("?" * len(case_ids)) or "NULL",
                    ",".join("?" * len(contract_ids)) or "NULL",
                ),
                (case_ids or []) + (contract_ids or []),
            ).fetchall()
        }) if (case_ids or contract_ids) else []
        removed["documents"] = _delete_in("documents", doc_ids)
        removed["contracts"] = _delete_in("contracts", contract_ids)
        removed["purchases"] = _delete_in("purchases", purchase_ids)
        removed["signoffs"] = _delete_in("signoffs", signoff_ids)
        removed["budgets"] = _delete_in("budgets", budget_ids)
        removed["projects"] = _delete_in("projects", project_ids)
        removed["cases"] = _delete_in("cases", case_ids)
    return removed
