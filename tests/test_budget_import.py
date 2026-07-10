"""表單型『預算』xlsx 匯入：認標籤解析 + 預覽 + 正式寫入 + 同名更新。用真實檔測。"""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REAL = Path(__file__).resolve().parents[1] / "docs" / "一、預算.xlsx"


def _real_available() -> bool:
    try:
        with REAL.open("rb") as fh:
            fh.read(1)
        return True
    except (FileNotFoundError, PermissionError, OSError):
        return False


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "budget.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


pytestmark = pytest.mark.skipif(not _real_available(), reason="真實預算 xlsx 不存在或被鎖住（docs/）")


def test_preview_then_commit_real_budgets(tmp_path):
    data = REAL.read_bytes()
    with _client(tmp_path) as client:
        prev = client.post("/api/budgets/import-xlsx?commit=false", content=data).json()["data"]
        assert prev["preview"] is True and prev["count"] >= 1
        assert client.get("/api/budgets").json()["data"] == []  # 預覽不寫

        res = client.post("/api/budgets/import-xlsx?commit=true", content=data).json()["data"]
        assert res["created_count"] == prev["count"]
        rows = client.get("/api/budgets").json()["data"]
        assert len(rows) == prev["count"]
        assert any(r["amount"] > 0 for r in rows)        # 金額有抓到
        assert any(r["unit_name"] for r in rows)         # 填寫部門有抓到
        # L3：年度費用明細（budget_periods）也一起匯入，年度費用比較算得出來
        assert res.get("periods_count", 0) >= 1
        annual = client.get(f"/api/budgets/{rows[0]['id']}/annual").json()["data"]
        assert len(annual["years"]) >= 1 and annual["periods"]  # 有年度、有期間欄

        # 再匯一次：同名更新、不重複
        res2 = client.post("/api/budgets/import-xlsx?commit=true", content=data).json()["data"]
        assert res2["created_count"] == 0 and res2["updated_count"] == prev["count"]
        assert len(client.get("/api/budgets").json()["data"]) == prev["count"]


def test_budget_import_blocked_for_handler(tmp_path):
    with _client(tmp_path, login="ap03") as client:
        r = client.post("/api/budgets/import-xlsx?commit=false", content=b"x")
        assert r.status_code == 403
