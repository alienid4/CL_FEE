"""照建議做的一批：D 多月預測、E 超支、B 未歸戶付款、F 待我複核、H 匯出、I 通知。"""
import os
from datetime import date

from fastapi.testclient import TestClient


def _nm():
    t = date.today()
    return f"{t.year + 1}-01" if t.month == 12 else f"{t.year}-{t.month + 1:02d}"


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "rev.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _approve(client, cid, approver="ap04", back="ap02"):
    client.post(f"/api/cases/{cid}/submit")
    client.post("/api/auth/login", json={"username": approver, "password": "T3st!Pass"})
    client.post(f"/api/cases/{cid}/approve")
    client.post("/api/auth/login", json={"username": back, "password": "T3st!Pass"})


def _case_pay(client, code, amount, month=None):
    case = client.post("/api/cases", json={"case_code": code, "title": code}).json()["data"]
    ct = client.post("/api/contracts", json={"contract_code": f"K-{code}", "contract_name": "c", "case_id": case["id"], "amount": amount}).json()["data"]
    client.post("/api/payments", json={"contract_id": ct["id"], "payment_month": month or _nm(), "payment_amount": amount, "status": "pending"})
    return case["id"], ct["id"]


def test_D_forecast_six_months(tmp_path):
    with _client(tmp_path) as client:
        d = client.get("/api/reports/cio-overview").json()["data"]
        assert len(d["forecast"]) == 6
        assert d["forecast"][0]["month"] == date.today().strftime("%Y-%m")


def test_E_overspent_flag(tmp_path):
    with _client(tmp_path) as client:
        cid, _ = _case_pay(client, "OVSP", 200)  # 付款 200
        client.post("/api/budgets", json={"budget_code": "B-OVSP", "amount": 100, "case_id": cid})  # 預算只有 100
        _approve(client, cid)
        d = client.get("/api/reports/cio-overview").json()["data"]
        row = next(r for r in d["upcoming_next_month"] if r["case_code"] == "OVSP")
        assert row["overspent"] is True
        assert d["overspent_count"] == 1


def test_B_orphan_payments(tmp_path):
    with _client(tmp_path) as client:
        ct = client.post("/api/contracts", json={"contract_code": "ORPH-K", "contract_name": "無案合約"}).json()["data"]
        client.post("/api/payments", json={"contract_id": ct["id"], "payment_month": _nm(), "payment_amount": 500, "status": "pending"})
        orphans = client.get("/api/reports/orphan-payments").json()["data"]
        assert any(o["contract_code"] == "ORPH-K" for o in orphans)


def test_F_pending_approvals_excludes_own(tmp_path):
    with _client(tmp_path) as client:  # ap02 建
        mine = client.post("/api/cases", json={"case_code": "F-MINE", "title": "我建的"}).json()["data"]
        client.post(f"/api/cases/{mine['id']}/submit")
        # 承辦 ap03 建、送出
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        theirs = client.post("/api/cases", json={"case_code": "F-THEIRS", "title": "承辦建的"}).json()["data"]
        client.post(f"/api/cases/{theirs['id']}/submit")
        # ap02 看待我複核：只該看到別人建的
        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        codes = [c["case_code"] for c in client.get("/api/reports/pending-approvals").json()["data"]]
        assert "F-THEIRS" in codes and "F-MINE" not in codes


def test_H_csv_export_modules(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/budgets", json={"budget_code": "EXP-B", "category": "類"})
        r = client.get("/api/budgets.csv")
        assert r.status_code == 200 and "text/csv" in r.headers["content-type"]
        assert r.text.startswith("﻿") and "預算編號" in r.text and "EXP-B" in r.text
        for m in ("projects", "signoffs", "purchases", "contracts", "payments"):
            assert client.get(f"/api/{m}.csv").status_code == 200


def test_I_notify_preview_without_smtp(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/cases", json={"case_code": "N-LATE", "title": "逾期", "owner": "ap03", "due_date": "2020-01-01"})
        res = client.post("/api/reports/reminders/notify").json()["data"]
        assert res["sent"] is False  # 未設 SMTP → 只預覽
        assert any("N-LATE" in d["body"] for d in res["digests"])
