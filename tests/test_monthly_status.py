"""每月支出狀態（使用者 2026-08-12：處長不要核決門檻，他要看每個月支出狀態）。

既有的月度支出只算實際核銷＝只看得到已經發生的錢。處長要掌握的是
「這個月還要付多少、下個月要準備多少」，所以預計與實際要一起給。
"""
import os
from datetime import date

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "monthly.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _month(offset: int) -> str:
    t = date.today()
    total = t.year * 12 + (t.month - 1) + offset
    return f"{total // 12:04d}:{total % 12 + 1:02d}".replace(":", "-")


def _confirmed_schedule(client, month: str, amount: float, periods: int = 1):
    """建一組已確認的費用排程（只有已確認的才會被算進預計）。"""
    m = client.post("/api/expenses", json={
        "expense_name": "維運", "total_amount": amount * periods,
        "modes": "periodic", "signoff_ref": "SG-1"}).json()["data"]
    sec = client.post(f"/api/expenses/{m['id']}/sections", json={
        "mode": "periodic", "section_amount": amount * periods, "frequency": "monthly",
        "periods": periods, "first_amount": amount, "first_month": month}).json()["data"]
    client.post(f"/api/expense-sections/{sec['id']}/generate")
    client.post(f"/api/expense-sections/{sec['id']}/confirm")
    return sec


def test_未來月份看得到要準備多少錢(tmp_path):
    with _client(tmp_path) as client:
        _confirmed_schedule(client, _month(1), 200000, periods=3)   # 下個月起連三期

        data = client.get("/api/reports/monthly-status").json()["data"]
        by_month = {m["month"]: m for m in data["months"]}
        assert by_month[_month(1)]["planned"] == 200000
        assert by_month[_month(2)]["planned"] == 200000
        assert data["ahead_total"] == 600000        # 未來要準備的總額
        assert data["current"]["month"] == date.today().strftime("%Y-%m")


def test_草稿排程不算進預計(tmp_path):
    """還在喬的排程不能拿來當資金預估——不然處長看到的數字是假的。"""
    with _client(tmp_path) as client:
        m = client.post("/api/expenses", json={
            "expense_name": "還沒確認", "total_amount": 500000,
            "modes": "periodic", "signoff_ref": "SG-2"}).json()["data"]
        sec = client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "periodic", "section_amount": 500000, "frequency": "monthly",
            "periods": 1, "first_amount": 500000, "first_month": _month(1)}).json()["data"]
        client.post(f"/api/expense-sections/{sec['id']}/generate")   # 產生但不確認

        data = client.get("/api/reports/monthly-status").json()["data"]
        by_month = {x["month"]: x for x in data["months"]}
        assert by_month[_month(1)]["planned"] == 0
        assert "草稿" in data["note"]


def test_實際已付與待付分開算(tmp_path):
    with _client(tmp_path) as client:
        k = client.post("/api/contracts", json={
            "contract_code": "K1", "contract_name": "約", "amount": 100}).json()["data"]
        client.post("/api/payments", json={
            "contract_id": k["id"], "payment_month": _month(0),
            "payment_amount": 80000, "status": "closed"})
        client.post("/api/payments", json={
            "contract_id": k["id"], "payment_month": _month(0),
            "payment_amount": 30000, "status": "pending"})

        cur = client.get("/api/reports/monthly-status").json()["data"]["current"]
        assert cur["paid"] == 80000 and cur["unpaid"] == 30000


def test_過去月份看得出預估準不準(tmp_path):
    with _client(tmp_path) as client:
        past = _month(-2)
        _confirmed_schedule(client, past, 100000)            # 當初預計 10 萬
        k = client.post("/api/contracts", json={
            "contract_code": "K2", "contract_name": "約", "amount": 100}).json()["data"]
        client.post("/api/payments", json={
            "contract_id": k["id"], "payment_month": past,
            "payment_amount": 130000, "status": "closed"})   # 實際付了 13 萬

        by_month = {m["month"]: m for m in
                    client.get("/api/reports/monthly-status").json()["data"]["months"]}
        row = by_month[past]
        assert row["planned"] == 100000 and row["paid"] == 130000
        assert row["diff"] == 30000 and row["is_past"] is True   # 超出預估 3 萬


def test_可以只看某一組(tmp_path):
    with _client(tmp_path) as client:
        c = client.post("/api/cases", json={"title": "網路案", "group_name": "網路組"}).json()["data"]
        k = client.post("/api/contracts", json={
            "contract_code": "K3", "contract_name": "約", "amount": 100,
            "case_id": c["id"]}).json()["data"]
        client.post("/api/payments", json={
            "contract_id": k["id"], "payment_month": _month(0),
            "payment_amount": 50000, "status": "closed"})

        net = client.get("/api/reports/monthly-status",
                         params={"group_name": "網路組"}).json()["data"]
        host = client.get("/api/reports/monthly-status",
                          params={"group_name": "主機組"}).json()["data"]
        assert net["current"]["paid"] == 50000
        assert host["current"]["paid"] == 0        # 別組看不到這筆


def test_沒資料時是零不是壞掉(tmp_path):
    with _client(tmp_path) as client:
        data = client.get("/api/reports/monthly-status").json()["data"]
        assert len(data["months"]) == 13          # 過去 6 ＋ 本月 ＋ 未來 6
        assert all(m["planned"] == 0 and m["paid"] == 0 for m in data["months"])
        assert data["ahead_total"] == 0
