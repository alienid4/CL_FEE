"""案件匯出 CSV /api/cases.csv。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "exp2.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _seed(table, payload):
    from app import store

    return store.insert_row(table, payload)


def test_export_cases_csv(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/cases", json={"case_code": "EXP-1", "title": "匯出測試", "note": "備註內容"})
        r = client.get("/api/cases.csv")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        assert "attachment" in r.headers.get("content-disposition", "")
        assert r.text.startswith("﻿")  # Excel 用的 UTF-8 BOM
        assert "案件編號" in r.text and "EXP-1" in r.text and "匯出測試" in r.text


def test_export_requires_login(tmp_path):
    with _client(tmp_path, login=None) as client:
        assert client.get("/api/cases.csv").status_code == 401


def test_export_scoped_for_handler(tmp_path):
    with _client(tmp_path, login=None) as client:
        _seed("cases", {"case_code": "THEIRS", "title": "t", "owner": "ap02"})
        _seed("cases", {"case_code": "MINE", "title": "m", "owner": "ap03"})
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        text = client.get("/api/cases.csv").text
        assert "MINE" in text and "THEIRS" not in text  # 承辦只匯出自己的
