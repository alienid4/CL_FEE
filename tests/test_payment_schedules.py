"""§8 預計付款(Payment Schedule) 與 實際費用(Expense = payments 表) 分離。

需求書 §8 的核心：預計付款走 payment_schedules、實際費用走 payments，兩者分開並關聯，
避免同一筆金額在 Dashboard 重複計算。本測試涵蓋：
  - 依付款方式自動產生排程（固定期數 / 里程碑%）
  - 里程碑比例合計必須 = 100 才能送出
  - 預計 vs 實際彙總（planned / paid / 還欠 unpaid_planned）不重複計算
"""
import os

import pytest
from fastapi.testclient import TestClient


def _setup(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "psched.db")
    from app.main import create_app

    client = TestClient(create_app())
    client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
    return client


def _contract(client, code, amount):
    r = client.post("/api/contracts", json={"contract_code": code, "contract_name": "合約", "amount": amount})
    assert r.status_code == 201, r.text
    return r.json()["data"]


def test_generate_installment_schedules(tmp_path):
    with _setup(tmp_path) as client:
        import app.store as store

        ct = _contract(client, "PS-INST", 900)
        out = store.generate_payment_schedules(ct["id"], "installment", 3)
        assert len(out) == 3
        assert [round(s["planned_amount"]) for s in out] == [300, 300, 300]
        assert len(store.list_payment_schedules(ct["id"])) == 3


def test_milestone_percent_must_total_100(tmp_path):
    with _setup(tmp_path) as client:
        import app.store as store

        ct = _contract(client, "PS-MILE", 1000)
        with pytest.raises(ValueError):
            store.generate_payment_schedules(ct["id"], "milestone", [30, 60])  # 90% → 擋下
        out = store.generate_payment_schedules(ct["id"], "milestone", [30, 30, 40])
        assert [round(s["planned_amount"]) for s in out] == [300, 300, 400]
        store.validate_milestone_total(ct["id"])  # 合計 100% → 不拋


def test_summary_planned_vs_actual_no_double_count(tmp_path):
    with _setup(tmp_path) as client:
        import app.store as store

        ct = _contract(client, "PS-SUM", 1000)
        store.generate_payment_schedules(ct["id"], "installment", 2)  # 預計 500 + 500 = 1000
        # 實際付掉一期 500（狀態 closed = 已付）
        r = client.post("/api/payments", json={
            "contract_id": ct["id"], "payment_month": "2026-08",
            "payment_amount": 500, "status": "closed",
        })
        assert r.status_code == 201, r.text
        s = store.contract_payment_summary(ct["id"])
        assert s["planned"] == 1000    # 預計來自排程
        assert s["paid"] == 500        # 實際來自 payments，不重複算排程
        assert s["unpaid_planned"] == 500  # 還欠 500


def test_expense_can_link_back_to_schedule(tmp_path):
    with _setup(tmp_path) as client:
        import app.store as store

        ct = _contract(client, "PS-LINK", 800)
        sched = store.generate_payment_schedules(ct["id"], "installment", 2)
        # 實際費用回指它履行的預計排程
        r = client.post("/api/payments", json={
            "contract_id": ct["id"], "payment_month": "2026-09",
            "payment_amount": 400, "status": "closed",
            "payment_schedule_id": sched[0]["id"],
        })
        assert r.status_code == 201, r.text
        assert r.json()["data"]["payment_schedule_id"] == sched[0]["id"]
