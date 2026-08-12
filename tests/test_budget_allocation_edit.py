"""預算分攤可人工微調（使用者 2026-08-12 回饋：分攤表只能整批重算，改不了個別單位）。

實務上談定的分攤常是「大致按比例、某一兩個單位另議」，沒有人工微調就只能改 Excel 重匯。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "alloc.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _budget_with_allocations(client, total=1000000):
    import app.store as store

    b = client.post("/api/budgets", json={
        "budget_code": "B-2026-001", "category": "基礎建設", "unit_name": "資訊管理處",
        "fiscal_year": "2026", "amount": total}).json()["data"]
    with store.connect() as conn:
        for seq, (code, name, pct) in enumerate(
                [("8101", "資訊管理處", 60.0), ("1010", "敦南分公司", 40.0)], start=1):
            conn.execute(
                "INSERT INTO budget_allocations (budget_id, seq, unit_code, unit_name, share_pct, amount) "
                "VALUES (?, ?, ?, ?, ?, ?)", (b["id"], seq, code, name, pct, total * pct / 100))
    return b


def test_改金額比例跟著算(tmp_path):
    with _client(tmp_path) as client:
        b = _budget_with_allocations(client)
        rows = client.get(f"/api/budgets/{b['id']}/allocations").json()["data"]
        target = next(r for r in rows if r["unit_code"] == "1010")

        res = client.patch(f"/api/budget-allocations/{target['id']}",
                           json={"amount": 300000}).json()["data"]
        changed = next(a for a in res["allocations"] if a["unit_code"] == "1010")
        assert changed["amount"] == 300000
        assert changed["share_pct"] == 30.0            # 30 萬 / 100 萬
        # 合計變成 90 萬，跟項目金額差 10 萬 → 要當場講出來
        assert res["balanced"] is False and res["diff"] == 100000


def test_改比例金額跟著算(tmp_path):
    with _client(tmp_path) as client:
        b = _budget_with_allocations(client)
        rows = client.get(f"/api/budgets/{b['id']}/allocations").json()["data"]
        target = next(r for r in rows if r["unit_code"] == "8101")

        res = client.patch(f"/api/budget-allocations/{target['id']}",
                           json={"share_pct": 55}).json()["data"]
        changed = next(a for a in res["allocations"] if a["unit_code"] == "8101")
        assert changed["share_pct"] == 55.0 and changed["amount"] == 550000


def test_改完會鎖回固定金額避免被重算洗掉(tmp_path):
    with _client(tmp_path) as client:
        b = _budget_with_allocations(client)
        client.patch(f"/api/budgets/{b['id']}", json={"alloc_method": "headcount"})
        rows = client.get(f"/api/budgets/{b['id']}/allocations").json()["data"]

        res = client.patch(f"/api/budget-allocations/{rows[0]['id']}",
                           json={"amount": 700000}).json()["data"]
        assert res["alloc_method"] == "fixed"          # 人工談好的結果不該被下次重算蓋掉


def test_分攤合計對得起來時不報差額(tmp_path):
    with _client(tmp_path) as client:
        b = _budget_with_allocations(client)
        chk = client.get(f"/api/budgets/{b['id']}/allocation-check").json()["data"]
        assert chk["balanced"] is True and chk["diff"] == 0 and chk["allocated"] == 1000000


def test_負數與空值擋掉(tmp_path):
    with _client(tmp_path) as client:
        b = _budget_with_allocations(client)
        rows = client.get(f"/api/budgets/{b['id']}/allocations").json()["data"]
        assert client.patch(f"/api/budget-allocations/{rows[0]['id']}",
                            json={"amount": -1}).status_code == 422
        assert client.patch(f"/api/budget-allocations/{rows[0]['id']}", json={}).status_code == 422
        assert client.patch("/api/budget-allocations/99999", json={"amount": 1}).status_code == 404


def test_改動留稽核紀錄(tmp_path):
    with _client(tmp_path) as client:
        b = _budget_with_allocations(client)
        rows = client.get(f"/api/budgets/{b['id']}/allocations").json()["data"]
        client.patch(f"/api/budget-allocations/{rows[0]['id']}", json={"amount": 123456})

        logs = client.get("/api/audit-logs", params={
            "table_name": "budget_allocations", "action": "manual-adjust"}).json()["data"]
        assert len(logs) == 1                          # 誰改的、改成多少查得到
