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


def test_periodic_dates_cross_year(tmp_path):
    """週期月租(每季) 100萬分4期＝25萬/季，從 2026-06 起 → 第4期落在 2027，跨年度。"""
    with _setup(tmp_path) as client:
        import app.store as store

        ct = _contract(client, "PS-Q", 1_000_000)
        out = store.generate_payment_schedules(
            ct["id"], "periodic", 4, start_month="2026-06", frequency="quarterly")
        assert [round(s["planned_amount"]) for s in out] == [250000, 250000, 250000, 250000]
        assert [s["due_date"] for s in out] == ["2026-06", "2026-09", "2026-12", "2027-03"]
        # 跨年度：前 3 期屬 2026、第 4 期屬 2027（預算按 due_date 年度歸屬）
        years = [s["due_date"][:4] for s in out]
        assert years.count("2026") == 3 and years.count("2027") == 1


def test_remainder_first_vs_last(tmp_path):
    """除不盡零頭：可選放第一期或最後期，加總必等於合約總額。"""
    with _setup(tmp_path) as client:
        import app.store as store

        ct = _contract(client, "PS-R", 1_000_000)
        last = store.generate_payment_schedules(ct["id"], "installment", 3, remainder_on="last")
        assert round(sum(s["planned_amount"] for s in last), 2) == 1_000_000
        assert last[-1]["planned_amount"] > last[0]["planned_amount"]  # 零頭在最後
        store.clear_payment_schedules(ct["id"])
        first = store.generate_payment_schedules(ct["id"], "installment", 3, remainder_on="first")
        assert round(sum(s["planned_amount"] for s in first), 2) == 1_000_000
        assert first[0]["planned_amount"] > first[-1]["planned_amount"]  # 零頭在第一


def test_settle_marks_paid_and_blocks_regen(tmp_path):
    """標某期已付＝建 closed 付款回指排程、排程轉 paid、還欠下降；之後不准整個重產。"""
    with _setup(tmp_path) as client:
        import app.store as store

        ct = _contract(client, "PS-SET", 1_000_000)
        gen = client.post(f"/api/contracts/{ct['id']}/payment-schedules/generate",
                          json={"method": "installment", "count": 4, "start_month": "2026-08"})
        assert gen.status_code == 201, gen.text
        first_id = gen.json()["data"]["schedules"][0]["id"]

        r = client.post(f"/api/settle-schedule/{first_id}", json={})
        assert r.status_code == 201, r.text
        summary = r.json()["data"]["summary"]
        assert summary["paid"] == 250000
        assert summary["unpaid_planned"] == 750000  # 還欠 75 萬

        # 已有核銷回填 → 整個重產要被擋（400）
        blocked = client.post(f"/api/contracts/{ct['id']}/payment-schedules/generate",
                              json={"method": "installment", "count": 2, "clear": True})
        assert blocked.status_code == 400, blocked.text


def test_settle_forbidden_for_handler(tmp_path):
    """標已付僅主管/助理；承辦(handler=ap03) 被擋 403。"""
    with _setup(tmp_path) as client:
        import app.store as store

        ct = _contract(client, "PS-PERM", 500_000)
        gen = client.post(f"/api/contracts/{ct['id']}/payment-schedules/generate",
                          json={"method": "installment", "count": 2})
        sid = gen.json()["data"]["schedules"][0]["id"]
        # 換成承辦登入
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        r = client.post(f"/api/settle-schedule/{sid}", json={})
        assert r.status_code == 403, r.text


def test_cio_overview_cross_year_payable(tmp_path):
    """跨年度：季付合約 100萬從 2026-06 起 → 2026 收 3 期(75萬)、2027 收 1 期(25萬)。
    決策總覽的待付款按年度拆，各由該年度預算支付（需求書 §9＋使用者確認）。"""
    with _setup(tmp_path) as client:
        import app.store as store

        case = client.post("/api/cases", json={"case_code": "CY-1", "title": "跨年合約"}).json()["data"]
        # 雙人複核：ap02 送出 → ap04 核准 → 切回 ap02
        client.post(f"/api/cases/{case['id']}/submit")
        client.post("/api/auth/login", json={"username": "ap04", "password": "T3st!Pass"})
        client.post(f"/api/cases/{case['id']}/approve")
        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        ct = client.post("/api/contracts", json={
            "contract_code": "CY-CT", "contract_name": "季付合約",
            "amount": 1_000_000, "case_id": case["id"]}).json()["data"]
        store.generate_payment_schedules(ct["id"], "periodic", 4, start_month="2026-06", frequency="quarterly")

        data = client.get("/api/reports/cio-overview").json()["data"]
        assert data["payable_planned"] == 1_000_000       # 待付款＝預計未付總額
        assert data["payable_by_year"]["2026"] == 750_000  # 今年 3 期
        assert data["payable_by_year"]["2027"] == 250_000  # 明年 1 期
