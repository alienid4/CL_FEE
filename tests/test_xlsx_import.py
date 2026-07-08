"""Excel(.xlsx) 上傳匯入專案：用真實檔測解析 + 預覽 + 正式寫入 + 冪等 + 權限。"""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REAL = Path(__file__).resolve().parents[1] / "docs" / "資訊架構部處級專案進度追蹤總表.xlsx"


def _real_available() -> bool:
    """檔案存在且能讀（Windows 下若被 Excel 開著會鎖住 → 視為不可用，跳過而非爆掉）。"""
    try:
        with REAL.open("rb") as fh:
            fh.read(1)
        return True
    except (FileNotFoundError, PermissionError, OSError):
        return False


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "xlsx.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


pytestmark = pytest.mark.skipif(not _real_available(), reason="真實專案 xlsx 不存在或被鎖住（docs/，可能正被 Excel 開啟）")


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
        # 依欄名對應：起訖日抓進來、每個專案都有（供進度總表算落後）
        assert all(r["start_date"] and r["end_date"] for r in rows)
        # 燈號不再誤抓成小數（AI 表欄位右移曾造成此問題）
        import re
        assert not any(re.match(r"^0?\.\d+$", r.get("rag_status") or "") for r in rows)

        # 再匯一次：同名專案改『更新』而非新增（不會長出重複、既有資料被刷新）
        res2 = client.post("/api/projects/import-xlsx?commit=true", content=data).json()["data"]
        assert res2["created_count"] == 0 and res2["updated_count"] == prev["count"]
        assert len(client.get("/api/projects").json()["data"]) == prev["count"]  # 筆數不變


def test_import_blocked_for_handler(tmp_path):
    with _client(tmp_path, login="ap03") as client:  # 承辦不可匯入專案
        r = client.post("/api/projects/import-xlsx?commit=false", content=b"x")
        assert r.status_code == 403


def test_bad_file_rejected(tmp_path):
    with _client(tmp_path) as client:
        assert client.post("/api/projects/import-xlsx?commit=false", content=b"not-an-xlsx").status_code == 400
