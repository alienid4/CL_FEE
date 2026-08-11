"""費用模組第二批（助理 0803 附件一 5.3＋第六節）：
最低承諾金額的排程與達成率，以及第三層實際費用明細與請款／核銷。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "commit.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _commitment_section(client, **over):
    m = client.post("/api/expenses", json={
        "expense_name": "雲端用量承諾", "total_amount": 3600000, "modes": "commitment",
        "signoff_ref": "SG-9", "vendor_name": "某雲端商", "vendor_tax_id": "12345678",
    }).json()["data"]
    body = {
        "mode": "commitment", "section_name": "三年最低承諾", "section_amount": 3600000,
        "periods": 3, "commit_span_months": 12, "frequency": "quarterly",
        "period_start": "2026-01-01", "first_amount": 1200000,
        "next_amount_rule": "same", "achievement_basis": "usage",
        "carry_over": 1, "shortfall_action": "差額補繳",
        **over,
    }
    sec = client.post(f"/api/expenses/{m['id']}/sections", json=body).json()["data"]
    return m, sec


def test_承諾期間依每期長度與頻率鋪出排程(tmp_path):
    with _client(tmp_path) as client:
        m, sec = _commitment_section(client)
        gen = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]
        rows = gen["schedules"]
        # 3 個承諾期 × 每期 12 個月 ÷ 每季 = 12 筆
        assert len(rows) == 12
        assert [r["commit_period"] for r in rows[:4]] == [1, 1, 1, 1]
        assert [r["commit_period"] for r in rows[4:8]] == [2, 2, 2, 2]
        assert rows[0]["expense_month"] == "2026-01" and rows[1]["expense_month"] == "2026-04"
        assert rows[4]["expense_month"] == "2027-01"          # 第二承諾期從隔年開始
        # 承諾金額攤到各期：120 萬 ÷ 4 季 = 30 萬
        assert rows[0]["planned_amount"] == 300000
        assert gen["can_confirm"] is True                      # 12 × 30 萬 = 360 萬，對得起來
        assert m["id"]


def test_期間長度除不盡頻率會擋下來(tmp_path):
    """每期 12 個月配「每半年」可以，配「每 5 個月」這種除不盡的會把一期切一半。"""
    with _client(tmp_path) as client:
        _m, sec = _commitment_section(client, commit_span_months=10, frequency="quarterly")
        r = client.post(f"/api/expense-sections/{sec['id']}/generate")
        assert r.status_code == 422 and "除不盡" in r.json()["detail"]


def test_後續承諾金額可依比例遞增(tmp_path):
    with _client(tmp_path) as client:
        _m, sec = _commitment_section(client, next_amount_rule="growth", growth_pct=10,
                                      section_amount=3972000)
        rows = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]["schedules"]
        assert rows[0]["planned_amount"] == 300000            # 第一承諾期 120 萬 ÷ 4
        assert rows[4]["planned_amount"] == 330000            # 第二期 +10%
        assert rows[8]["planned_amount"] == 363000            # 第三期再 +10%


def test_達成率要等實際費用登錄後才算得出來(tmp_path):
    with _client(tmp_path) as client:
        _m, sec = _commitment_section(client)
        rows = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]["schedules"]
        client.post(f"/api/expense-sections/{sec['id']}/confirm")

        before = client.get(f"/api/expense-sections/{sec['id']}/achievement").json()["data"]
        # 一筆都還沒登錄 → rate 是 null，不能拿 0% 混充「沒達成」
        assert before["periods"][0]["rate"] is None
        assert before["periods"][0]["committed"] == 1200000

        for r in rows[:4]:                                    # 第一承諾期四季都登錄
            client.post(f"/api/expense-schedules/{r['id']}/actuals", json={"usage_amount": 250000})
        after = client.get(f"/api/expense-sections/{sec['id']}/achievement").json()["data"]
        p1 = after["periods"][0]
        assert p1["recognized"] == 1000000 and p1["shortfall"] == 200000
        assert p1["rate"] == 83.3                             # 100 萬 ÷ 120 萬


def test_超額可轉入次期(tmp_path):
    with _client(tmp_path) as client:
        _m, sec = _commitment_section(client)
        rows = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]["schedules"]
        client.post(f"/api/expense-sections/{sec['id']}/confirm")
        for r in rows[:4]:
            client.post(f"/api/expense-schedules/{r['id']}/actuals", json={"usage_amount": 400000})
        res = client.get(f"/api/expense-sections/{sec['id']}/achievement").json()["data"]
        p1, p2 = res["periods"][0], res["periods"][1]
        assert p1["excess"] == 400000 and p1["carry_in_next"] == 400000
        assert p2["recognized"] == 400000                     # 前期超額算進下一期


def test_調整金額要寫原因且認列金額由系統算(tmp_path):
    with _client(tmp_path) as client:
        _m, sec = _commitment_section(client)
        rows = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]["schedules"]
        client.post(f"/api/expense-sections/{sec['id']}/confirm")

        bad = client.post(f"/api/expense-schedules/{rows[0]['id']}/actuals",
                          json={"usage_amount": 100000, "adjust_amount": -5000})
        assert bad.status_code == 422 and "調整原因" in bad.json()["detail"]

        good = client.post(f"/api/expense-schedules/{rows[0]['id']}/actuals", json={
            "usage_amount": 100000, "adjust_amount": -5000, "adjust_reason": "廠商折讓"}).json()["data"]
        assert good["recognized_amount"] == 95000            # 系統算，不讓人手填
        assert good["commit_period"] == 1                    # 承諾期別由排程帶


def test_排程沒確認不准登錄實際費用(tmp_path):
    with _client(tmp_path) as client:
        _m, sec = _commitment_section(client)
        rows = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]["schedules"]
        r = client.post(f"/api/expense-schedules/{rows[0]['id']}/actuals", json={"usage_amount": 1})
        assert r.status_code == 409


def _confirmed_periodic(client):
    m = client.post("/api/expenses", json={
        "expense_name": "維運服務費", "total_amount": 600, "modes": "periodic",
        "signoff_ref": "SG-1", "vendor_name": "廠商A", "vendor_tax_id": "87654321"}).json()["data"]
    sec = client.post(f"/api/expenses/{m['id']}/sections", json={
        "mode": "periodic", "section_amount": 600, "frequency": "monthly",
        "periods": 3, "first_amount": 200, "first_month": "2026-01",
        "first_due_date": "2026-01-10"}).json()["data"]
    rows = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]["schedules"]
    client.post(f"/api/expense-sections/{sec['id']}/confirm")
    return m, sec, rows


def test_請款核銷由系統帶入關聯與計算差異(tmp_path):
    with _client(tmp_path) as client:
        m, _sec, rows = _confirmed_periodic(client)
        s = client.post(f"/api/expense-schedules/{rows[0]['id']}/settlements", json={
            "invoice_no": "AB12345678", "invoice_date": "2026-02-01",
            "claim_amount": 200, "settler": "行政小陳"}).json()["data"]
        # 廠商、統編、計費期間、核銷月份都由系統帶，人只填發票與金額
        assert s["vendor_name"] == "廠商A" and s["vendor_tax_id"] == "87654321"
        assert s["settle_month"] == "2026-01"
        assert s["claim_diff"] == 0 and s["progress"] == "invoice_pending"
        assert s["progress_label"] == "發票尚未收到"

        tot = client.get(f"/api/expenses/{m['id']}/settlements").json()["data"]
        assert tot["scheduled_total"] == 600 and tot["claimed_total"] == 200
        assert tot["unclaimed_total"] == 400


def test_請款金額與排程不同要填差異原因(tmp_path):
    with _client(tmp_path) as client:
        _m, _sec, rows = _confirmed_periodic(client)
        bad = client.post(f"/api/expense-schedules/{rows[0]['id']}/settlements", json={
            "invoice_no": "X1", "claim_amount": 150})
        assert bad.status_code == 422 and "差異原因" in bad.json()["detail"]

        ok_ = client.post(f"/api/expense-schedules/{rows[0]['id']}/settlements", json={
            "invoice_no": "X1", "claim_amount": 150, "diff_reason": "本期部分服務未啟用"}).json()["data"]
        assert ok_["claim_diff"] == 50


def test_同一期同一張發票不得重複建(tmp_path):
    with _client(tmp_path) as client:
        _m, _sec, rows = _confirmed_periodic(client)
        client.post(f"/api/expense-schedules/{rows[0]['id']}/settlements",
                    json={"invoice_no": "SAME1", "claim_amount": 200})
        again = client.post(f"/api/expense-schedules/{rows[0]['id']}/settlements",
                            json={"invoice_no": "SAME1", "claim_amount": 200})
        assert again.status_code == 422 and "已經對這一期" in again.json()["detail"]


def test_處理進度五態與通知對象(tmp_path):
    with _client(tmp_path) as client:
        _m, _sec, rows = _confirmed_periodic(client)
        s = client.post(f"/api/expense-schedules/{rows[0]['id']}/settlements",
                        json={"invoice_no": "N1", "claim_amount": 200}).json()["data"]
        assert s["can_confirm"] is False          # 還沒到「可預備上簽」，不顯示確認完成

        # 行政備妥 → 通知承辦確認
        r1 = client.patch(f"/api/settlements/{s['id']}/progress",
                          json={"progress": "ready_to_sign"}).json()["data"]
        assert r1["notify"] == "owner" and r1["can_confirm"] is True

        # 承辦勾確認完成 → 通知核銷者
        r2 = client.patch(f"/api/settlements/{s['id']}/progress", json={"confirmed": True}).json()["data"]
        assert r2["notify"] == "settler" and r2["confirmed"] == 1

        for p, label in [("signing", "款項簽核中"), ("approved", "款項已核准"), ("submitted", "提交會計（結案）")]:
            got = client.patch(f"/api/settlements/{s['id']}/progress", json={"progress": p}).json()["data"]
            assert got["progress_label"] == label


def test_進度不對時不給勾確認完成(tmp_path):
    with _client(tmp_path) as client:
        _m, _sec, rows = _confirmed_periodic(client)
        s = client.post(f"/api/expense-schedules/{rows[0]['id']}/settlements",
                        json={"invoice_no": "N2", "claim_amount": 200}).json()["data"]
        r = client.patch(f"/api/settlements/{s['id']}/progress", json={"confirmed": True})
        assert r.status_code == 422 and "可預備上簽" in r.json()["detail"]
