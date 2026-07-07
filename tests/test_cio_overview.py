"""CIO 決策總覽：大方向資金彙總（只算已核准）+ 下月要出的款下探 + 模組極簡。"""
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


def _submit_and_approve(client, case_id, creator="ap02", approver="ap04"):
    """走完雙人複核：建立者送出 → 另一位助理核准 → 還原登入為建立者。"""
    client.post(f"/api/cases/{case_id}/submit")
    client.post("/api/auth/login", json={"username": approver, "password": "T3st!Pass"})
    r = client.post(f"/api/cases/{case_id}/approve")
    client.post("/api/auth/login", json={"username": creator, "password": "T3st!Pass"})
    return r


def test_overview_counts_only_approved(tmp_path):
    with _client(tmp_path) as client:
        cid = _seed_case_with_next_month_payment(client, "CT-1", "ap03", 15000000)
        # 尚未核准 → CIO 看不到這筆錢
        before = client.get("/api/reports/cio-overview").json()["data"]
        assert before["next_month_total"] == 0
        assert before["upcoming_next_month"] == []
        # 核准後 → CIO 才看得到
        _submit_and_approve(client, cid)
        data = client.get("/api/reports/cio-overview").json()["data"]
        assert data["next_month"] == _next_month()
        assert data["next_month_total"] == 15000000
        assert data["funds_to_prepare"] == 15000000
        codes = [row["case_code"] for row in data["upcoming_next_month"]]
        assert "CT-1" in codes
        assert any(row["owner"] == "ap03" for row in data["upcoming_next_month"])


def test_drilldown_360_from_overview(tmp_path):
    with _client(tmp_path) as client:
        case_id = _seed_case_with_next_month_payment(client, "CT-2", "ap03", 5000000)
        detail = client.get(f"/api/cases/{case_id}/360").json()["data"]
        assert detail["case"]["case_code"] == "CT-2"
        assert detail["case"]["owner"] == "ap03"
        assert detail["totals"]["payment_amount"] == 5000000
        assert len(detail["contracts"]) == 1


def test_drilldown_shows_full_control_chain(tmp_path):
    """CIO 下探案件要看得到整條控管鏈：對應預算/專案/簽呈/請購，不只合約付款。"""
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"case_code": "CHAIN-1", "title": "鏈"}).json()["data"]
        cid = case["id"]
        client.post("/api/budgets", json={"budget_code": "B-CH", "amount": 500, "case_id": cid})
        client.post("/api/projects", json={"project_code": "P-CH", "project_name": "專", "case_id": cid})
        client.post("/api/signoffs", json={"signoff_code": "S-CH", "subject": "簽", "amount": 500, "case_id": cid})
        client.post("/api/purchases", json={"purchase_code": "PO-CH", "item_name": "品", "amount": 500, "case_id": cid})
        d = client.get(f"/api/cases/{cid}/360").json()["data"]
        assert any(b["budget_code"] == "B-CH" for b in d["budgets"])
        assert any(p["project_code"] == "P-CH" for p in d["projects"])
        assert any(s["signoff_code"] == "S-CH" for s in d["signoffs"])
        assert any(p["purchase_code"] == "PO-CH" for p in d["purchases"])
        assert d["totals"]["budget_amount"] == 500


def test_unplanned_flag_when_no_budget(tmp_path):
    """下月要出的款，案件若無對應預算 → 標記預算外；有預算則否。"""
    with _client(tmp_path) as client:
        # 無預算的案件
        cid = _seed_case_with_next_month_payment(client, "NOBUD", "ap03", 300)
        _submit_and_approve(client, cid)
        data = client.get("/api/reports/cio-overview").json()["data"]
        row = next(r for r in data["upcoming_next_month"] if r["case_code"] == "NOBUD")
        assert row["unplanned"] is True
        assert data["unplanned_next_month"] == 300

        # 補上對應預算 → 不再算預算外
        client.post("/api/budgets", json={"budget_code": "BUD-NOBUD", "amount": 300, "case_id": cid})
        data2 = client.get("/api/reports/cio-overview").json()["data"]
        row2 = next(r for r in data2["upcoming_next_month"] if r["case_code"] == "NOBUD")
        assert row2["unplanned"] is False
        assert data2["unplanned_next_month"] == 0


def test_cio_sees_only_overview_module(tmp_path):
    with _client(tmp_path, login="ap01") as client:
        me = client.get("/api/auth/me").json()["data"]
        assert me["allowed_modules"] == ["cio-overview"]
        assert me["default_module"] == "cio-overview"


def test_overview_scoped_for_handler(tmp_path):
    with _client(tmp_path) as client:  # ap02
        mine = _seed_case_with_next_month_payment(client, "MINE-03", "ap03", 1000000)
        other = _seed_case_with_next_month_payment(client, "OTHER-02", "ap02", 9000000)
        _submit_and_approve(client, mine)
        _submit_and_approve(client, other)
        # 換承辦 ap03：只看得到自己案件下的款
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        data = client.get("/api/reports/cio-overview").json()["data"]
        codes = [row["case_code"] for row in data["upcoming_next_month"]]
        assert "MINE-03" in codes and "OTHER-02" not in codes
        assert data["next_month_total"] == 1000000  # 只算自己的
