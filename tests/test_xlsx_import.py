"""Excel(.xlsx) 上傳匯入專案：用真實檔測解析 + 預覽 + 正式寫入 + 冪等 + 權限。"""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REAL = Path(__file__).resolve().parents[1] / "docs" / "資訊架構部處級專案進度追蹤總表.xlsx"


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "xlsx.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


pytestmark = pytest.mark.skipif(not REAL.exists(), reason="缺真實專案 xlsx（docs/）")


def test_preview_then_commit_real_projects(tmp_path):
    data = REAL.read_bytes()
    with _client(tmp_path) as client:
        # 預覽：解析出多個專案，不寫入
        prev = client.post("/api/projects/import-xlsx?commit=false", content=data).json()["data"]
        assert prev["preview"] is True and prev["count"] >= 10
        assert client.get("/api/projects").json()["data"] == []  # 預覽不寫

        # 正式匯入：寫入
        res = client.post("/api/projects/import-xlsx?commit=true", content=data).json()["data"]
        assert res["created_count"] == prev["count"]
        rows = client.get("/api/projects").json()["data"]
        assert len(rows) == prev["count"]
        assert any(r["source"] for r in rows)  # 記了組別
        assert any(r["progress"] > 0 for r in rows)  # 進度換算成百分比

        # 冪等：再匯一次全部跳過
        res2 = client.post("/api/projects/import-xlsx?commit=true", content=data).json()["data"]
        assert res2["created_count"] == 0 and res2["skipped_count"] == prev["count"]


def test_import_blocked_for_handler(tmp_path):
    with _client(tmp_path, login="ap03") as client:  # 承辦不可匯入專案
        r = client.post("/api/projects/import-xlsx?commit=false", content=b"x")
        assert r.status_code == 403


def test_bad_file_rejected(tmp_path):
    with _client(tmp_path) as client:
        assert client.post("/api/projects/import-xlsx?commit=false", content=b"not-an-xlsx").status_code == 400
