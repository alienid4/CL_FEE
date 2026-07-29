"""費用類別分析：錢花在哪一類。

「類別」有兩種合理讀法，系統兩種都給、由使用者切換：
  預算類別（走案件底下的預算 category）／合約類型（直接看合約上的 contract_type）。
歸不出來的（沒預算、或一個案子跨多個類別）獨立成列並標記，不塞進「其他」——
塞進去數字看起來很完整，其實是把問題藏起來。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "cat.db")
    from app.main import create_app

    return TestClient(create_app())


def _seed(table, payload):
    from app import store

    return store.insert_row(table, payload)


def _rows(client, dimension):
    d = client.get("/api/reports/expense-categories", params={"dimension": dimension}).json()["data"]
    return {r["category"]: r for r in d["rows"]}, d


def test_by_budget_category(tmp_path):
    """付款→合約→案件→該案預算的類別。已付/待付分開算。"""
    with _client(tmp_path) as client:
        case = _seed("cases", {"case_code": "CAT-1", "title": "資安案", "owner": "ap02"})
        _seed("budgets", {"budget_code": "B1", "category": "資訊安全", "case_id": case["id"], "amount": 500_000})
        ct = _seed("contracts", {"contract_code": "K1", "contract_name": "防護系統",
                                 "amount": 400_000, "case_id": case["id"], "contract_type": "採購"})
        _seed("payments", {"contract_id": ct["id"], "payment_month": "2026-03", "payment_amount": 150_000, "status": "closed"})
        _seed("payments", {"contract_id": ct["id"], "payment_month": "2026-06", "payment_amount": 100_000, "status": "pending"})

        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        rows, d = _rows(client, "budget")
        assert rows["資訊安全"]["paid"] == 150_000
        assert rows["資訊安全"]["pending"] == 100_000
        assert rows["資訊安全"]["contract_amount"] == 400_000
        assert rows["資訊安全"]["payment_count"] == 2
        assert rows["資訊安全"]["needs_attention"] is False
        assert d["totals"]["paid"] == 150_000


def test_by_contract_type_is_a_different_cut(tmp_path):
    """換維度＝同一批錢用另一種切法：合約類型直接掛在合約上，不經案件。"""
    with _client(tmp_path) as client:
        case = _seed("cases", {"case_code": "CAT-2", "title": "機房案", "owner": "ap02"})
        _seed("budgets", {"budget_code": "B2", "category": "基礎建設", "case_id": case["id"], "amount": 300_000})
        ct = _seed("contracts", {"contract_code": "K2", "contract_name": "機櫃代管",
                                 "amount": 240_000, "case_id": case["id"], "contract_type": "租賃"})
        _seed("payments", {"contract_id": ct["id"], "payment_month": "2026-04", "payment_amount": 60_000, "status": "closed"})

        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        by_budget, _ = _rows(client, "budget")
        by_contract, _ = _rows(client, "contract")
        assert by_budget["基礎建設"]["paid"] == 60_000    # 預算類別看到的是「基礎建設」
        assert by_contract["租賃"]["paid"] == 60_000      # 合約類型看到的是「租賃」，同一筆錢


def test_case_with_mixed_budget_categories_is_flagged_not_guessed(tmp_path):
    """一個案子底下有多個不同類別的預算＝歸屬有歧義，標「多類別」讓人自己看，不硬猜。"""
    with _client(tmp_path) as client:
        case = _seed("cases", {"case_code": "CAT-3", "title": "混合案", "owner": "ap02"})
        _seed("budgets", {"budget_code": "B3a", "category": "工具", "case_id": case["id"], "amount": 100_000})
        _seed("budgets", {"budget_code": "B3b", "category": "資訊安全", "case_id": case["id"], "amount": 100_000})
        ct = _seed("contracts", {"contract_code": "K3", "contract_name": "混合約", "amount": 200_000, "case_id": case["id"]})
        _seed("payments", {"contract_id": ct["id"], "payment_month": "2026-05", "payment_amount": 50_000, "status": "closed"})

        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        rows, _ = _rows(client, "budget")
        mixed = rows["（多類別，需人工歸戶）"]
        assert mixed["paid"] == 50_000
        assert mixed["needs_attention"] is True
        assert "工具" not in rows and "資訊安全" not in rows  # 不會被硬塞到其中一類


def test_unclassified_is_visible_not_hidden(tmp_path):
    """沒預算可歸、也沒填合約類型的，獨立成「未分類」列並標記，不併進其他類別。"""
    with _client(tmp_path) as client:
        ct = _seed("contracts", {"contract_code": "K4", "contract_name": "沒歸戶的約", "amount": 80_000})
        _seed("payments", {"contract_id": ct["id"], "payment_month": "2026-07", "payment_amount": 20_000, "status": "closed"})

        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        for dim in ("budget", "contract"):
            rows, _ = _rows(client, dim)
            assert rows["（未分類）"]["paid"] == 20_000
            assert rows["（未分類）"]["needs_attention"] is True


def test_disabled_contract_excluded(tmp_path):
    with _client(tmp_path) as client:
        ct = _seed("contracts", {"contract_code": "K5", "contract_name": "停用約",
                                 "amount": 90_000, "contract_type": "服務", "status": "disabled"})
        _seed("payments", {"contract_id": ct["id"], "payment_month": "2026-07", "payment_amount": 30_000, "status": "closed"})

        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        rows, d = _rows(client, "contract")
        assert "服務" not in rows
        assert d["totals"]["paid"] == 0


def test_bad_dimension_rejected(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        assert client.get("/api/reports/expense-categories", params={"dimension": "亂填"}).status_code == 422
