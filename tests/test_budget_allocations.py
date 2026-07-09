"""預算共同費用分攤：合成 xlsx 測 解析→匯入→分攤清單→單位彙總（不依賴真檔），另跑真檔（鎖住則跳過）。"""
import io
import os
from pathlib import Path

import openpyxl
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


def _budget_wb() -> bytes:
    """迷你分攤表：一個共用費用（全年度 1000），攤給甲/乙/丙三個單位（600/300/100）。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "共用系統維護"
    ws.append(["統籌預估表"])
    ws.append([None, "預算項目：", "修繕維護費-資訊"])
    ws.append([None, "填寫部門：", "資訊管理處"])
    ws.append([None, "費用內容：", "XX 系統授權暨維護"])
    ws.append([None, None, None, None, "全年度費用"])
    ws.append([None, None, None, "115年度", 1000])
    ws.append([None, "部門代號", "部門別", "合計"])
    ws.append([None, "A01", "甲部門", 600])
    ws.append([None, "A02", "乙部門", 300])
    ws.append([None, "A03", "丙部門", 100])
    ws.append([None, None, "合計", 1000])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "balloc.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_parse_extracts_allocations():
    from app.store import parse_budget_xlsx

    recs = parse_budget_xlsx(_budget_wb())
    assert len(recs) == 1
    b = recs[0]
    assert b["amount"] == 1000 and b["fiscal_year"] == "115年度"
    al = b["allocations"]
    assert [a["unit_name"] for a in al] == ["甲部門", "乙部門", "丙部門"]
    assert al[0]["unit_code"] == "A01" and al[0]["amount"] == 600 and al[0]["share_pct"] == 60.0
    assert round(sum(a["amount"] for a in al), 2) == b["amount"]  # 分攤合計＝項目總額


def test_import_writes_allocations_and_apis(tmp_path):
    with _client(tmp_path) as client:
        res = client.post("/api/budgets/import-xlsx?commit=true", content=_budget_wb()).json()["data"]
        assert res["created_count"] == 1 and res["allocations_count"] == 3
        bid = client.get("/api/budgets").json()["data"][0]["id"]

        # 以費用項目看：這筆攤給哪些單位
        al = client.get(f"/api/budgets/{bid}/allocations").json()["data"]
        assert [a["unit_name"] for a in al] == ["甲部門", "乙部門", "丙部門"]  # 依金額大到小

        # 以單位看：彙總
        units = client.get("/api/budget-units").json()["data"]["units"]
        names = {u["unit_name"]: u["total_amount"] for u in units}
        assert names["甲部門"] == 600 and names["丙部門"] == 100
        # 單一單位明細
        detail = client.get("/api/budget-units", params={"unit_code": "A01"}).json()["data"]["detail"]
        assert len(detail) == 1 and detail[0]["amount"] == 600

        # 再匯一次：同碼更新、不重複
        client.post("/api/budgets/import-xlsx?commit=true", content=_budget_wb())
        assert len(client.get(f"/api/budgets/{bid}/allocations").json()["data"]) == 3


@pytest.mark.skipif(not _real_available(), reason="真實預算 xlsx 不存在或被鎖住（docs/）")
def test_real_budget_allocations_sum_matches_total(tmp_path):
    data = REAL.read_bytes()
    with _client(tmp_path) as client:
        client.post("/api/budgets/import-xlsx?commit=true", content=data)
        bid = client.get("/api/budgets").json()["data"][0]["id"]
        b = next(x for x in client.get("/api/budgets").json()["data"] if x["id"] == bid)
        al = client.get(f"/api/budgets/{bid}/allocations").json()["data"]
        assert len(al) >= 50  # 約 62~64 個單位
        assert round(sum(a["amount"] for a in al), 0) == round(b["amount"], 0)  # 分攤合計＝項目總額
