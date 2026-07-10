"""廠商別 合約金額 vs 實付：合約直接帶 vendor_name，付款經合約歸戶到廠商；已付=closed；不分年度。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "vendor.db")
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


def test_vendor_rollup_and_overspend(tmp_path):
    with _client(tmp_path) as client:
        # 廠商甲：合約 1000，已付 300、待付 100（未超支）
        ka = client.post("/api/contracts", json={"contract_code": "KA", "contract_name": "合約A", "vendor_name": "廠商甲", "amount": 1000}).json()["data"]
        _pay(client, ka["id"], "2026-03", 300, "closed")
        _pay(client, ka["id"], "2026-04", 100, "pending")
        # 廠商乙：合約 500，已付 600（超支）
        kb = client.post("/api/contracts", json={"contract_code": "KB", "contract_name": "合約B", "vendor_name": "廠商乙", "amount": 500}).json()["data"]
        _pay(client, kb["id"], "2026-05", 600, "closed")
        # 未填廠商的合約
        kc = client.post("/api/contracts", json={"contract_code": "KC", "contract_name": "合約C", "amount": 200}).json()["data"]
        _pay(client, kc["id"], "2026-06", 50, "closed")

        data = client.get("/api/reports/vendor-amount-summary").json()["data"]
        rows = {r["vendor"]: r for r in data["rows"]}
        assert [r["vendor"] for r in data["rows"]] == ["廠商甲", "廠商乙", "（未填廠商）"]

        a = rows["廠商甲"]
        assert a["contract_amount"] == 1000 and a["paid"] == 300 and a["pending"] == 100
        assert a["remaining"] == 700 and a["usage_pct"] == 30.0 and a["over"] is False

        b = rows["廠商乙"]
        assert b["contract_amount"] == 500 and b["paid"] == 600
        assert b["remaining"] == -100 and b["usage_pct"] == 120.0 and b["over"] is True

        unfilled = rows["（未填廠商）"]
        assert unfilled["contract_amount"] == 200 and unfilled["paid"] == 50

        assert data["totals"]["contract_amount"] == 1700
        assert data["totals"]["paid"] == 950


def test_disabled_contract_excluded(tmp_path):
    with _client(tmp_path) as client:
        ct = client.post("/api/contracts", json={"contract_code": "KD", "contract_name": "停用合約", "vendor_name": "廠商丙", "amount": 999}).json()["data"]
        client.post(f"/api/contracts/{ct['id']}/disable")
        data = client.get("/api/reports/vendor-amount-summary").json()["data"]
        assert all(r["vendor"] != "廠商丙" for r in data["rows"])
