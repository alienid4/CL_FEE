"""預算分攤方法：按人數自動計算。合成人數表→匯入→設方法→重算→驗比例＋整數合計。"""
import io
import os
from pathlib import Path

import openpyxl
import pytest
from fastapi.testclient import TestClient

REAL_HC = Path(__file__).resolve().parents[1] / "docs" / "費用分攤表NEW-20260422(截止115年6月份人數).xlsx"


def _real_hc_available() -> bool:
    try:
        with REAL_HC.open("rb") as fh:
            fh.read(1)
        return True
    except (FileNotFoundError, PermissionError, OSError):
        return False


def _headcount_wb() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "費用分攤表"
    ws.append(["費用分攤表"])
    ws.append(["代號", "部門", "金額", "人數"])
    ws.append(["A", "甲部門", 0, 2])
    ws.append(["B", "乙部門", 0, 3])
    ws.append(["C", "丙部門", 0, 5])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "methods.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_headcount_import_and_recompute(tmp_path):
    with _client(tmp_path) as client:
        prev = client.post("/api/budget-headcounts/import-xlsx?commit=false", content=_headcount_wb()).json()["data"]
        assert prev["count"] == 3
        client.post("/api/budget-headcounts/import-xlsx?commit=true", content=_headcount_wb())
        hc = client.get("/api/budget-headcounts").json()["data"]
        assert sum(h["headcount"] for h in hc) == 10

        b = client.post("/api/budgets", json={"budget_code": "HC-1", "amount": 1000, "alloc_method": "headcount"}).json()["data"]
        res = client.post(f"/api/budgets/{b['id']}/recompute").json()["data"]
        assert res["method"] == "headcount" and res["written"] == 3

        al = {a["unit_name"]: a for a in client.get(f"/api/budgets/{b['id']}/allocations").json()["data"]}
        assert al["甲部門"]["amount_int"] == 200 and al["乙部門"]["amount_int"] == 300 and al["丙部門"]["amount_int"] == 500
        assert sum(a["amount_int"] for a in al.values()) == 1000  # 整數合計＝總額


def test_fixed_method_recompute_is_noop(tmp_path):
    with _client(tmp_path) as client:
        b = client.post("/api/budgets", json={"budget_code": "FX-1", "amount": 500}).json()["data"]  # 預設 fixed
        res = client.post(f"/api/budgets/{b['id']}/recompute").json()["data"]
        assert res["method"] == "fixed" and res["written"] == 0


def test_headcount_import_blocked_for_handler(tmp_path):
    with _client(tmp_path, login="ap03") as client:
        r = client.post("/api/budget-headcounts/import-xlsx?commit=false", content=b"x")
        assert r.status_code == 403


@pytest.mark.skipif(not _real_hc_available(), reason="真實人數表 xlsx 不存在或被鎖住（docs/）")
def test_real_headcount_import(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/budget-headcounts/import-xlsx?commit=true", content=REAL_HC.read_bytes())
        hc = client.get("/api/budget-headcounts").json()["data"]
        assert len(hc) >= 30  # ~67 部門
        assert any(h["unit_name"] == "資訊架構部" and h["headcount"] == 258 for h in hc)
