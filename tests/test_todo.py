"""待辦事項 /api/todo。

使用者拍板（2026-07-29）：待辦不再靠人工填「下一步」，改由狀態與日期自動生成——
卡在審核流程的案件，加上快到日子的事（合約/保固/維護到期、預計付款日）。
"""
import os
from datetime import date, timedelta

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "todo.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _in(days):
    return (date.today() + timedelta(days=days)).isoformat()


def _todo(client):
    return client.get("/api/todo").json()["data"]


def test_只有卡在審核流程的案件才進待辦(tmp_path):
    with _client(tmp_path) as client:
        pend = client.post("/api/cases", json={"case_code": "T-PEND", "title": "待複核案"}).json()["data"]
        client.post(f"/api/cases/{pend['id']}/submit")
        ret = client.post("/api/cases", json={"case_code": "T-RET", "title": "被退件的"}).json()["data"]
        client.post(f"/api/cases/{ret['id']}/submit")
        client.post(f"/api/cases/{ret['id']}/return", json={"reason": "缺附件"})
        client.post("/api/cases", json={"case_code": "T-PLAIN", "title": "普通草稿"})

        rows = {r["case_code"]: r for r in _todo(client)}
        assert "T-PEND" in rows and rows["T-PEND"]["kind"] == "case"
        assert "T-RET" in rows
        assert rows["T-RET"]["detail"] == "缺附件"     # 退件原因直接顯示，不用點進去
        assert "T-PLAIN" not in rows                   # 草稿還沒送出，不算待辦


def test_快到期的合約保固維護都會進待辦(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/contracts", json={
            "contract_code": "T-K", "contract_name": "主機維護",
            "end_date": _in(10), "warranty_end_date": _in(-3), "maintenance_end_date": _in(20)})
        client.post("/api/contracts", json={
            "contract_code": "T-FAR", "contract_name": "還很久", "end_date": _in(200)})

        rows = _todo(client)
        kinds = {r["kind"] for r in rows if r["case_code"] == "T-K"}
        assert kinds == {"contract", "warranty", "maintenance"}   # 三種到期日各一筆
        assert "T-FAR" not in {r["case_code"] for r in rows}      # 200 天後的還不用煩


def test_快到預計付款日的排程會進待辦(tmp_path):
    with _client(tmp_path) as client:
        import app.store as store

        ct = client.post("/api/contracts", json={
            "contract_code": "T-PAY", "contract_name": "分期約", "amount": 120_000}).json()["data"]
        this_month = date.today().strftime("%Y-%m")
        store.generate_payment_schedules(ct["id"], "installment", 2, start_month=this_month)

        rows = [r for r in _todo(client) if r["kind"] == "payment_due"]
        assert rows and rows[0]["detail"] == "預計付款日"
        assert rows[0]["amount"] == 60_000


def test_已付款的排程不再出現在待辦(tmp_path):
    with _client(tmp_path) as client:
        import app.store as store

        ct = client.post("/api/contracts", json={
            "contract_code": "T-PAID", "contract_name": "已付", "amount": 50_000}).json()["data"]
        gen = store.generate_payment_schedules(ct["id"], "installment", 1,
                                               start_month=date.today().strftime("%Y-%m"))
        client.post(f"/api/settle-schedule/{gen[0]['id']}", json={})
        assert [r for r in _todo(client) if r["kind"] == "payment_due"] == []


def test_最急的排前面(tmp_path):
    """已過期的要排在快到期的前面，卡流程（沒有日期）的排最後。"""
    with _client(tmp_path) as client:
        client.post("/api/contracts", json={"contract_code": "T-SOON", "contract_name": "快到", "end_date": _in(20)})
        client.post("/api/contracts", json={"contract_code": "T-OVER", "contract_name": "過期", "end_date": _in(-5)})
        case = client.post("/api/cases", json={"case_code": "T-FLOW", "title": "卡流程"}).json()["data"]
        client.post(f"/api/cases/{case['id']}/submit")

        codes = [r["case_code"] for r in _todo(client)]
        assert codes.index("T-OVER") < codes.index("T-SOON") < codes.index("T-FLOW")


def test_todo_requires_login(tmp_path):
    with _client(tmp_path, login=None) as client:
        assert client.get("/api/todo").status_code == 401


def test_todo_scoped_for_handler(tmp_path):
    from app import store

    with _client(tmp_path, login=None) as client:
        mine = store.insert_row("cases", {"case_code": "MINE-R", "title": "m", "owner": "ap03"})
        theirs = store.insert_row("cases", {"case_code": "THEIRS-R", "title": "t", "owner": "ap02"})
        for c in (mine, theirs):
            store.update_row("cases", c["id"], {"status": "pending_review"})
        # 別人案件底下的合約到期，承辦也不該看到
        store.insert_row("contracts", {"contract_code": "THEIRS-K", "contract_name": "k",
                                       "case_id": theirs["id"], "end_date": _in(5)})
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        codes = {r["case_code"] for r in _todo(client)}
        assert codes == {"MINE-R"}
