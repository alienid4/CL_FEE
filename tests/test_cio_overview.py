"""CIO 決策總覽：大方向資金彙總 + 下月要出的款下探 + 模組極簡。"""
import os
from datetime import date

from fastapi.testclient import TestClient


def _next_month() -> str:
    today = date.today()
    if today.month == 12:
        return f"{today.year + 1}-01"
    return f"{today.year}-{today.month + 1:02d}"


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "cio.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _seed_case_with_next_month_payment(client, case_code, owner, amount):
    case = client.post("/api/cases", json={"case_code": case_code, "title": f"{case_code} 案", "owner": owner, "amount": amount}).json()["data"]
    contract = client.post("/api/contracts", json={"contract_code": f"K-{case_code}", "contract_name": "合約", "case_id": case["id"], "amount": amount}).json()["data"]
    client.post("/api/payments", json={"contract_id": contract["id"], "payment_month": _next_month(), "payment_amount": amount, "status": "pending"})
    return case["id"]


def test_overview_sums_next_month(tmp_path):
    with _client(tmp_path) as client:
        _seed_case_with_next_month_payment(client, "CT-1", "ap03", 15000000)
        data = client.get("/api/reports/cio-overview").json()["data"]
        assert data["next_month"] == _next_month()
        assert data["next_month_total"] == 15000000
        assert data["funds_to_prepare"] == 15000000  # pending 未結案
        codes = [row["case_code"] for row in data["upcoming_next_month"]]
        assert "CT-1" in codes
        # 下月要出的款帶得出承辦，供 CIO 追查
        assert any(row["owner"] == "ap03" for row in data["upcoming_next_month"])


def test_drilldown_360_from_overview(tmp_path):
    with _client(tmp_path) as client:
        case_id = _seed_case_with_next_month_payment(client, "CT-2", "ap03", 5000000)
        detail = client.get(f"/api/cases/{case_id}/360").json()["data"]
        assert detail["case"]["case_code"] == "CT-2"
        assert detail["case"]["owner"] == "ap03"
        assert detail["totals"]["payment_amount"] == 5000000
        assert len(detail["contracts"]) == 1


def test_cio_sees_only_overview_module(tmp_path):
    with _client(tmp_path, login="ap01") as client:
        me = client.get("/api/auth/me").json()["data"]
        assert me["allowed_modules"] == ["cio-overview"]
        assert me["default_module"] == "cio-overview"


def test_overview_scoped_for_handler(tmp_path):
    with _client(tmp_path, login=None) as client:
        # 主管先建：一筆自己的、一筆承辦的
        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        _seed_case_with_next_month_payment(client, "MINE-03", "ap03", 1000000)
        _seed_case_with_next_month_payment(client, "OTHER-02", "ap02", 9000000)
        # 換承辦 ap03：只看得到自己案件下的款
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        data = client.get("/api/reports/cio-overview").json()["data"]
        codes = [row["case_code"] for row in data["upcoming_next_month"]]
        assert "MINE-03" in codes and "OTHER-02" not in codes
        assert data["next_month_total"] == 1000000  # 只算自己的
