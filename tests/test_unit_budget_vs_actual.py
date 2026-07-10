"""單位別 預算 vs 實付 彙總報表：預算依單位加總；付款經合約→案件→該案預算的單位歸戶；已付=closed。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "bva.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _pay(client, contract_id, month, amount, status):
    client.post("/api/payments", json={
        "contract_id": contract_id, "payment_month": month,
        "payment_amount": amount, "status": status,
    })


def _seed(client):
    # 資訊處：預算 1000，已付 300、待付 100（未超支）
    a = client.post("/api/cases", json={"case_code": "A", "title": "A 案"}).json()["data"]
    client.post("/api/budgets", json={"budget_code": "BA", "amount": 1000, "case_id": a["id"], "unit_name": "資訊處", "fiscal_year": "2026"})
    ka = client.post("/api/contracts", json={"contract_code": "KA", "contract_name": "合約A", "case_id": a["id"], "amount": 1000}).json()["data"]
    _pay(client, ka["id"], "2026-03", 300, "closed")
    _pay(client, ka["id"], "2026-04", 100, "pending")
    # 財務處：預算 500，已付 600（超支）
    b = client.post("/api/cases", json={"case_code": "B", "title": "B 案"}).json()["data"]
    client.post("/api/budgets", json={"budget_code": "BB", "amount": 500, "case_id": b["id"], "unit_name": "財務處", "fiscal_year": "2026"})
    kb = client.post("/api/contracts", json={"contract_code": "KB", "contract_name": "合約B", "case_id": b["id"], "amount": 500}).json()["data"]
    _pay(client, kb["id"], "2026-05", 600, "closed")
    # 無預算案件的付款 → 未歸單位
    c = client.post("/api/cases", json={"case_code": "C", "title": "C 案"}).json()["data"]
    kc = client.post("/api/contracts", json={"contract_code": "KC", "contract_name": "合約C", "case_id": c["id"], "amount": 50}).json()["data"]
    _pay(client, kc["id"], "2026-06", 50, "closed")


def test_unit_rollup_and_overspend(tmp_path):
    with _client(tmp_path) as client:
        _seed(client)
        data = client.get("/api/reports/unit-budget-vs-actual").json()["data"]
        rows = {r["unit"]: r for r in data["rows"]}
        # 依預算大→小排序：資訊處(1000) 在 財務處(500) 前
        assert [r["unit"] for r in data["rows"]] == ["資訊處", "財務處"]

        it = rows["資訊處"]
        assert it["budget"] == 1000 and it["paid"] == 300 and it["pending"] == 100
        assert it["remaining"] == 700 and it["usage_pct"] == 30.0 and it["over"] is False

        fin = rows["財務處"]
        assert fin["budget"] == 500 and fin["paid"] == 600
        assert fin["remaining"] == -100 and fin["usage_pct"] == 120.0 and fin["over"] is True

        # 無預算案件的付款進未歸單位、不進任何單位列
        assert data["unattributed"]["paid"] == 50
        assert data["totals"]["budget"] == 1500
        assert data["totals"]["paid"] == 950  # 300 + 600 + 50(未歸)


def test_year_filter_and_years_list(tmp_path):
    with _client(tmp_path) as client:
        _seed(client)
        # 2026 有資料
        d2026 = client.get("/api/reports/unit-budget-vs-actual?year=2026").json()["data"]
        assert d2026["totals"]["budget"] == 1500
        assert 2026 in d2026["years"]
        # 2027 無預算也無付款 → 空
        d2027 = client.get("/api/reports/unit-budget-vs-actual?year=2027").json()["data"]
        assert d2027["rows"] == []
        assert d2027["totals"]["budget"] == 0
        assert d2027["unattributed"]["paid"] == 0
