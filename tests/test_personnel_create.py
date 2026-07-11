"""人員主檔：主動新增乾淨人員（給表單下拉選單用）。建立前擋撞名。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "personnelcreate.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_create_personnel_success(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/personnel-master", json={"name": "測試人員甲"})
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        assert d["name"] == "測試人員甲"
        masters = client.get("/api/personnel-master").json()["data"]["masters"]
        assert any(m["name"] == "測試人員甲" for m in masters)


def test_duplicate_name_rejected(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/personnel-master", json={"name": "測試人員甲"})
        r = client.post("/api/personnel-master", json={"name": "測試人員甲"})
        assert r.status_code == 422
        assert "已存在" in r.json()["detail"]


def test_blank_name_rejected(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/personnel-master", json={"name": "  "})
        assert r.status_code == 422


def test_handler_cannot_create_personnel(tmp_path):
    with _client(tmp_path, login="ap03") as client:
        r = client.post("/api/personnel-master", json={"name": "承辦不該能建"})
        assert r.status_code == 403
