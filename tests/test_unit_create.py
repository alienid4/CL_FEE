"""單位主檔：主動新增乾淨單位（給表單下拉選單用），跟合併機制分開。建立前擋撞名（代號/名稱/別名）。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "unitcreate.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_create_unit_success(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/unit-master", json={"canonical_code": "9001", "canonical_name": "測試新單位"})
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        assert d["canonical_code"] == "9001" and d["canonical_name"] == "測試新單位"
        masters = client.get("/api/unit-master").json()["data"]["masters"]
        assert any(m["canonical_name"] == "測試新單位" for m in masters)


def test_duplicate_name_rejected(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/unit-master", json={"canonical_code": "9001", "canonical_name": "測試新單位"})
        r = client.post("/api/unit-master", json={"canonical_code": "9002", "canonical_name": "測試新單位"})
        assert r.status_code == 422
        assert "已存在" in r.json()["detail"]


def test_duplicate_code_rejected(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/unit-master", json={"canonical_code": "9001", "canonical_name": "單位A"})
        r = client.post("/api/unit-master", json={"canonical_code": "9001", "canonical_name": "單位B"})
        assert r.status_code == 422
        assert "已存在" in r.json()["detail"]


def test_name_already_an_alias_rejected(tmp_path):
    with _client(tmp_path) as client:
        # 用合併機制把「舊寫法」掛成「正式名稱」的別名
        client.post("/api/unit-merge", json={
            "variants": [{"unit_code": "9003", "unit_name": "舊寫法"}],
            "canonical_code": "9003", "canonical_name": "正式名稱",
            "reason": "測試前置",
        })
        r = client.post("/api/unit-master", json={"canonical_name": "舊寫法"})
        assert r.status_code == 422
        assert "別名" in r.json()["detail"]


def test_blank_name_rejected(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/unit-master", json={"canonical_name": "  "})
        assert r.status_code == 422


def test_handler_cannot_create_unit(tmp_path):
    with _client(tmp_path, login="ap03") as client:
        r = client.post("/api/unit-master", json={"canonical_name": "承辦不該能建"})
        assert r.status_code == 403
