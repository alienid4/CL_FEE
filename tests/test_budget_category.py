"""按類別分攤（Phase 2）：類別基準匯入→設類別→重算→驗『分攤=費用×單位%、每類=100%、整數合計=費用』。"""
import io
import os
from pathlib import Path

import openpyxl
import pytest
from fastapi.testclient import TestClient

REAL = Path(__file__).resolve().parents[1] / "docs" / "資訊架構部費用分攤表_2026.01.02起用(20260102修訂).xlsx"


def _real_available() -> bool:
    try:
        with REAL.open("rb") as fh:
            fh.read(1)
        return True
    except (FileNotFoundError, PermissionError, OSError):
        return False


def _matrix_wb() -> bytes:
    """合成一張含『對照』表的最小檔：兩類別 × 兩單位，NEW 欄各加總=1.0。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "對照"
    ws.append(["代號", "部門", "台股功能", "台股功能", "複委託功能", "複委託功能"])
    ws.append(["", "部門", "(現行)", "(NEW)", "(現行)", "(NEW)"])
    ws.append(["A", "甲部門", 0.5, 0.4, 0.5, 0.6])
    ws.append(["B", "乙部門", 0.5, 0.6, 0.5, 0.4])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "cat.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_import_and_category_recompute(tmp_path):
    with _client(tmp_path) as client:
        prev = client.post("/api/category-shares/import-xlsx?commit=false", content=_matrix_wb()).json()["data"]
        assert prev["count"] == 4 and set(prev["categories"]) == {"台股功能", "複委託功能"}
        client.post("/api/category-shares/import-xlsx?commit=true", content=_matrix_wb())

        cats = {c["category"]: c for c in client.get("/api/category-shares").json()["data"]["categories"]}
        assert cats["台股功能"]["pct_sum"] == 100.0 and cats["複委託功能"]["pct_sum"] == 100.0

        b = client.post("/api/budgets", json={"budget_code": "CAT-1", "amount": 1000,
                                              "alloc_method": "category", "alloc_category": "台股功能"}).json()["data"]
        res = client.post(f"/api/budgets/{b['id']}/recompute").json()["data"]
        assert res["method"] == "category" and res["written"] == 2

        al = {a["unit_name"]: a for a in client.get(f"/api/budgets/{b['id']}/allocations").json()["data"]}
        assert al["甲部門"]["amount_int"] == 400 and al["乙部門"]["amount_int"] == 600
        assert sum(a["amount_int"] for a in al.values()) == 1000  # 整數合計＝費用


def test_category_recompute_without_category_errors(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/category-shares/import-xlsx?commit=true", content=_matrix_wb())
        b = client.post("/api/budgets", json={"budget_code": "CAT-2", "amount": 500, "alloc_method": "category"}).json()["data"]
        r = client.post(f"/api/budgets/{b['id']}/recompute")
        assert r.status_code == 400  # 沒選類別


def test_category_import_blocked_for_handler(tmp_path):
    with _client(tmp_path, login="ap03") as client:
        r = client.post("/api/category-shares/import-xlsx?commit=false", content=b"x")
        assert r.status_code == 403


@pytest.mark.skipif(not _real_available(), reason="真實費用分攤表 xlsx 不存在或被鎖住（docs/）")
def test_real_category_matrix_each_sums_100(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/category-shares/import-xlsx?commit=true", content=REAL.read_bytes())
        cats = client.get("/api/category-shares").json()["data"]["categories"]
        assert len(cats) >= 3
        for c in cats:
            assert abs(c["pct_sum"] - 100.0) < 0.5  # 每類加總≈100%
