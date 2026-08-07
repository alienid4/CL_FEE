"""待辦事項四張卡（助理 2026-08-03 回饋）：待審核／合約到期／WBS 到期／費用核銷。
期限口徑是助理指定的：合約三個月內、WBS 兩週內、核銷看當月。
資料範圍靠 owner scope 收斂——承辦只看自己負責案件底下的東西。"""
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


def _d(days):
    return (date.today() + timedelta(days=days)).isoformat()


def _cards(client):
    return client.get("/api/reports/todo-cards").json()["data"]


def test_期限口徑_合約三個月_wbs兩週(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"title": "測試案"}).json()["data"]
        client.post("/api/contracts", json={"contract_code": "C1", "contract_name": "快到期", "case_id": case["id"], "end_date": _d(30)})
        client.post("/api/contracts", json={"contract_code": "C2", "contract_name": "很久以後", "case_id": case["id"], "end_date": _d(200)})
        proj = client.post("/api/projects", json={"project_code": "P1", "project_name": "專案", "case_id": case["id"]}).json()["data"]
        client.post(f"/api/projects/{proj['id']}/items", json={"item_name": "快到期工作", "end_date": _d(7), "sub_total": 2, "sub_done": 0, "risk_note": "測試用"})
        client.post(f"/api/projects/{proj['id']}/items", json={"item_name": "還很久", "end_date": _d(60), "sub_total": 2, "sub_done": 0, "risk_note": "測試用"})

        d = _cards(client)
        assert [c["contract_code"] for c in d["contracts_expiring"]["items"]] == ["C1"]   # 200 天後的不列
        assert [w["item_name"] for w in d["wbs_due"]["items"]] == ["快到期工作"]           # 60 天後的不列
        assert d["contracts_expiring"]["window"] == "三個月內" and d["wbs_due"]["window"] == "兩週內"


def test_已完成的工作項不列入(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"title": "測試案"}).json()["data"]
        proj = client.post("/api/projects", json={"project_code": "P1", "project_name": "專案", "case_id": case["id"]}).json()["data"]
        client.post(f"/api/projects/{proj['id']}/items", json={"item_name": "做完了", "end_date": _d(3), "sub_total": 2, "sub_done": 2, "risk_note": "測試用"})
        client.post(f"/api/projects/{proj['id']}/items", json={"item_name": "還沒做完", "end_date": _d(3), "sub_total": 2, "sub_done": 1, "risk_note": "測試用"})

        d = _cards(client)
        assert [w["item_name"] for w in d["wbs_due"]["items"]] == ["還沒做完"]


def test_逾期的工作項另外計數(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"title": "測試案"}).json()["data"]
        proj = client.post("/api/projects", json={"project_code": "P1", "project_name": "專案", "case_id": case["id"]}).json()["data"]
        client.post(f"/api/projects/{proj['id']}/items", json={"item_name": "已逾期", "end_date": _d(-5), "sub_total": 1, "sub_done": 0, "risk_note": "測試用"})
        client.post(f"/api/projects/{proj['id']}/items", json={"item_name": "快到了", "end_date": _d(5), "sub_total": 1, "sub_done": 0, "risk_note": "測試用"})

        d = _cards(client)
        assert d["wbs_due"]["count"] == 2 and d["wbs_due"]["overdue"] == 1   # 卡片上要標得出有幾項已經逾期


def test_核銷只看當月且未結案(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"title": "測試案"}).json()["data"]
        k = client.post("/api/contracts", json={"contract_code": "C1", "contract_name": "約", "case_id": case["id"]}).json()["data"]
        this_month = date.today().strftime("%Y-%m")
        client.post("/api/payments", json={"contract_id": k["id"], "payment_month": this_month, "payment_amount": 1000})
        paid = client.post("/api/payments", json={"contract_id": k["id"], "payment_month": this_month, "payment_amount": 500}).json()["data"]
        client.patch(f"/api/payments/{paid['id']}", json={"status": "closed"})       # 已結案不用再辦
        client.post("/api/payments", json={"contract_id": k["id"], "payment_month": "2020-01", "payment_amount": 700})  # 別的月份

        d = _cards(client)
        assert d["settlements"]["count"] == 1 and d["settlements"]["total"] == 1000


def test_承辦只看到自己負責案件底下的(tmp_path):
    with _client(tmp_path) as client:  # ap02 主管/助理：看得到全部
        mine = client.post("/api/cases", json={"title": "承辦的案", "owner": "ap03"}).json()["data"]
        other = client.post("/api/cases", json={"title": "別人的案", "owner": "ap05"}).json()["data"]
        client.post("/api/contracts", json={"contract_code": "MINE", "contract_name": "我的約", "case_id": mine["id"], "end_date": _d(10)})
        client.post("/api/contracts", json={"contract_code": "OTHER", "contract_name": "別人的約", "case_id": other["id"], "end_date": _d(10)})
        assert len(_cards(client)["contracts_expiring"]["items"]) == 2

        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        assert [c["contract_code"] for c in _cards(client)["contracts_expiring"]["items"]] == ["MINE"]


def test_待審核與本月新核准分開算(tmp_path):
    with _client(tmp_path) as client:
        a = client.post("/api/cases", json={"title": "送審中"}).json()["data"]
        client.post(f"/api/cases/{a['id']}/submit")
        b = client.post("/api/cases", json={"title": "要核准的"}).json()["data"]
        client.post(f"/api/cases/{b['id']}/submit")
        client.post("/api/auth/login", json={"username": "ap04", "password": "T3st!Pass"})
        client.post(f"/api/cases/{b['id']}/approve")

        d = _cards(client)
        assert [c["title"] for c in d["pending_review"]["items"]] == ["送審中"]
        assert [c["title"] for c in d["new_approved"]["items"]] == ["要核准的"]
