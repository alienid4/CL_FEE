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

    return {
        "cases": len(_CASES),
        "contracts": len(_CONTRACTS),
        "payments": len(_PAYMENTS) + 1,  # 含動態的下月付款
        "documents": len(_DOCUMENTS),
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
