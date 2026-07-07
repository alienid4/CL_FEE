"""需處理案件待辦清單 /api/todo。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "todo.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_todo_includes_reviewing_or_has_next_step_only(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/cases", json={"case_code": "T-REVIEW", "title": "審核中案", "status": "reviewing"})
        client.post("/api/cases", json={"case_code": "T-NEXT", "title": "有下一步", "status": "draft", "next_step": "補來源"})
        client.post("/api/cases", json={"case_code": "T-PLAIN", "title": "普通草稿", "status": "draft"})
        client.post("/api/cases", json={"case_code": "T-APPROVED", "title": "已核准", "status": "approved"})
        codes = {r["case_code"] for r in client.get("/api/todo").json()["data"]}
        assert "T-REVIEW" in codes           # 審核中 → 待辦
        assert "T-NEXT" in codes             # 有下一步 → 待辦
        assert "T-PLAIN" not in codes        # 普通草稿 → 不在待辦
        assert "T-APPROVED" not in codes     # 已核准且無下一步 → 不在待辦


def test_todo_requires_login(tmp_path):
    with _client(tmp_path, login=None) as client:
        assert client.get("/api/todo").status_code == 401


def test_todo_scoped_for_handler(tmp_path):
    from app import store

    with _client(tmp_path, login=None) as client:
        store.insert_row("cases", {"case_code": "MINE-R", "title": "m", "status": "reviewing", "owner": "ap03"})
        store.insert_row("cases", {"case_code": "THEIRS-R", "title": "t", "status": "reviewing", "owner": "ap02"})
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        codes = {r["case_code"] for r in client.get("/api/todo").json()["data"]}
        assert codes == {"MINE-R"}  # 承辦只看自己的待辦
