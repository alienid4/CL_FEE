"""逾期/落後催辦清單 /api/reports/reminders。"""
import os
from datetime import date, timedelta

from fastapi.testclient import TestClient


def _d(days):
    return (date.today() + timedelta(days=days)).isoformat()


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "rem.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_lists_overdue_and_soon_cases(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/cases", json={"case_code": "OVERDUE", "title": "逾期案", "due_date": _d(-6)})
        client.post("/api/cases", json={"case_code": "SOON", "title": "快到期案", "due_date": _d(5)})
        client.post("/api/cases", json={"case_code": "FAR", "title": "還很久", "due_date": _d(60)})
        client.post("/api/cases", json={"case_code": "NODUE", "title": "沒設期限"})
        items = client.get("/api/reports/reminders").json()["data"]
        by_code = {i["code"]: i for i in items}
        assert by_code["OVERDUE"]["severity"] == "overdue"
        assert by_code["SOON"]["severity"] == "soon"
        assert "FAR" not in by_code  # 超出 14 天視窗
        assert "NODUE" not in by_code  # 沒設期限不催


def test_excludes_approved_case(tmp_path):
    with _client(tmp_path) as client:
        c = client.post("/api/cases", json={"case_code": "DONE", "title": "已完成", "due_date": _d(-3)}).json()["data"]
        client.post(f"/api/cases/{c['id']}/submit")
        client.post("/api/auth/login", json={"username": "ap04", "password": "T3st!Pass"})
        client.post(f"/api/cases/{c['id']}/approve")
        items = client.get("/api/reports/reminders").json()["data"]
        assert all(i["code"] != "DONE" for i in items)  # 已核准 = 已完成，不催


def test_includes_overdue_contract(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/contracts", json={"contract_code": "K-LATE", "contract_name": "逾期合約", "end_date": _d(-2)})
        items = client.get("/api/reports/reminders").json()["data"]
        k = next((i for i in items if i["code"] == "K-LATE"), None)
        assert k is not None and k["type"] == "contract" and k["severity"] == "overdue"


def test_includes_overdue_project(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/projects", json={"project_code": "PJ-LATE", "project_name": "落後專案", "due_date": _d(-4), "status": "active"})
        client.post("/api/projects", json={"project_code": "PJ-DONE", "project_name": "已完成", "due_date": _d(-4), "status": "completed"})
        items = client.get("/api/reports/reminders").json()["data"]
        by = {i["code"]: i for i in items}
        assert by["PJ-LATE"]["type"] == "project" and by["PJ-LATE"]["severity"] == "overdue"
        assert "PJ-DONE" not in by  # 已完成不催


def test_scoped_for_handler(tmp_path):
    with _client(tmp_path) as client:  # ap02 建兩筆
        client.post("/api/cases", json={"case_code": "MINE", "title": "我的", "owner": "ap03", "due_date": _d(-1)})
        client.post("/api/cases", json={"case_code": "THEIRS", "title": "別人的", "owner": "ap02", "due_date": _d(-1)})
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        codes = [i["code"] for i in client.get("/api/reports/reminders").json()["data"]]
        assert "MINE" in codes and "THEIRS" not in codes


def test_requires_login(tmp_path):
    with _client(tmp_path, login=None) as client:
        assert client.get("/api/reports/reminders").status_code == 401
