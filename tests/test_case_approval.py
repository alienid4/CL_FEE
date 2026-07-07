"""雙人複核工作流：送出 → 另一人核准；不能自己核自己；承辦/CIO 不能核。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login=None):
    os.environ["SQLITE_PATH"] = str(tmp_path / "approval.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        _login(client, login)
    return client


def _login(client, user):
    return client.post("/api/auth/login", json={"username": user, "password": "T3st!Pass"})


def _new_case(client, code):
    return client.post("/api/cases", json={"case_code": code, "title": f"{code} 案"}).json()["data"]


def test_handler_submit_assistant_approve(tmp_path):
    with _client(tmp_path, "ap03") as client:  # 承辦建案
        case = _new_case(client, "AP-1")
        assert case["status"] == "draft"
        assert case["created_by"] == "ap03"
        assert client.post(f"/api/cases/{case['id']}/submit").json()["data"]["status"] == "pending_review"
        # 換助理 ap02 核准（≠ 建立者 ap03）
        _login(client, "ap02")
        approved = client.post(f"/api/cases/{case['id']}/approve").json()["data"]
        assert approved["status"] == "approved"
        assert approved["approved_by"] == "ap02"
        assert approved["approved_at"]


def test_cannot_approve_own_case(tmp_path):
    with _client(tmp_path, "ap02") as client:  # 助理自己建
        case = _new_case(client, "AP-2")
        client.post(f"/api/cases/{case['id']}/submit")
        r = client.post(f"/api/cases/{case['id']}/approve")  # 自己核自己
        assert r.status_code == 403
        # 需另一位助理 ap04 來核
        _login(client, "ap04")
        assert client.post(f"/api/cases/{case['id']}/approve").status_code == 200


def test_handler_cannot_approve(tmp_path):
    with _client(tmp_path, "ap02") as client:
        case = _new_case(client, "AP-3")
        client.post(f"/api/cases/{case['id']}/submit")
        _login(client, "ap03")  # 承辦無權核准
        assert client.post(f"/api/cases/{case['id']}/approve").status_code == 403


def test_cio_cannot_approve(tmp_path):
    with _client(tmp_path, "ap02") as client:
        case = _new_case(client, "AP-4")
        client.post(f"/api/cases/{case['id']}/submit")
        _login(client, "ap01")  # CIO 唯讀，連寫入都被擋
        assert client.post(f"/api/cases/{case['id']}/approve").status_code == 403


def test_cannot_approve_when_not_pending(tmp_path):
    with _client(tmp_path, "ap02") as client:
        case = _new_case(client, "AP-5")  # 還沒送出（draft）
        _login(client, "ap04")
        assert client.post(f"/api/cases/{case['id']}/approve").status_code == 409


def test_cannot_set_approved_directly(tmp_path):
    with _client(tmp_path, "ap02") as client:
        # 建立時不得直接設已核准
        assert client.post("/api/cases", json={"case_code": "AP-6", "title": "x", "status": "approved"}).status_code == 422
        # 編輯時也不得直接改成已核准（必須走複核）
        case = _new_case(client, "AP-7")
        assert client.patch(f"/api/cases/{case['id']}", json={"status": "approved"}).status_code == 422
