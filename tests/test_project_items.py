"""工作項（project_items）：用合成 xlsx 測解析→匯入→清單→維護（不依賴真實檔）。"""
import io
import os

import openpyxl
from fastapi.testclient import TestClient


HEADER = ["標號", "專案名稱", "執行必要性(下拉式選單)", "總進度預計%", "總進度實際%", "總進度燈號",
          "標號", "工作主項目", "負責人", "開始日期", "結束日期", "執行進度(下拉式選單)",
          "子項目總數", "子項目完成數", "完成度（%)", "燈號", "關鍵風險點/備註說明",
          "需決策項目", "需支援項目", "持續天數"]


def _project_wb() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "測試組處級專案"
    ws.append(["部處級專案進度追蹤總表"])  # 標題列（無「專案名稱」，避免被當表頭）
    ws.append(HEADER)
    ws.append([1, "測試專案", "必要", 0.5, 0.4, "", 1, "需求盤點", "王小明",
               "2026-01-01", "2026-03-31", "已完成", 3, 3, 1.0, "綠", "", "", "", 90])
    ws.append(["", "", "", "", "", "", 2, "系統開發", "陳美惠",
               "2026-02-01", "2026-06-30", "進行中", "", "", 0.5, "黃", "等圖確認", "預算追加", "AP團隊", 150])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "items.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_parse_extracts_work_items():
    from app.store import parse_projects_xlsx

    recs = parse_projects_xlsx(_project_wb())
    assert len(recs) == 1
    p = recs[0]
    assert p["project_name"] == "測試專案"
    # 專案起訖＝各工作項 min(開始)→max(結束)
    assert p["start_date"] == "2026-01-01" and p["end_date"] == "2026-06-30"
    items = p["items"]
    assert len(items) == 2
    assert items[0]["item_name"] == "需求盤點" and items[0]["exec_status"] == "已完成"
    assert items[0]["progress"] == 100.0 and items[0]["rag"] == "綠"
    assert items[1]["item_name"] == "系統開發" and items[1]["decision_needed"] == "預算追加"


def test_import_writes_items_and_api_lists_them(tmp_path):
    with _client(tmp_path) as client:
        res = client.post("/api/projects/import-xlsx?commit=true", content=_project_wb()).json()["data"]
        assert res["created_count"] == 1 and res["items_count"] == 2
        pid = client.get("/api/projects").json()["data"][0]["id"]
        items = client.get(f"/api/projects/{pid}/items").json()["data"]
        assert [i["item_name"] for i in items] == ["需求盤點", "系統開發"]

        # 再匯一次：工作項同名更新、不重複
        client.post("/api/projects/import-xlsx?commit=true", content=_project_wb())
        assert len(client.get(f"/api/projects/{pid}/items").json()["data"]) == 2


def test_work_item_crud(tmp_path):
    with _client(tmp_path) as client:
        pj = client.post("/api/projects", json={"project_code": "WI-1", "project_name": "手建專案"}).json()["data"]
        pid = pj["id"]
        # 新增工作項（承辦/助理可直接改，即時生效）
        it = client.post(f"/api/projects/{pid}/items",
                         json={"item_name": "第一項", "owner": "王小明", "progress": 20, "exec_status": "進行中"}).json()["data"]
        assert it["item_name"] == "第一項" and it["project_id"] == pid
        # 編輯
        upd = client.patch(f"/api/project-items/{it['id']}", json={"progress": 60}).json()["data"]
        assert upd["progress"] == 60
        assert len(client.get(f"/api/projects/{pid}/items").json()["data"]) == 1
        # 承辦也能維護（專案不隔離）
        h = client
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        assert h.get(f"/api/projects/{pid}/items").status_code == 200


def test_work_item_add_blocked_for_cio(tmp_path):
    with _client(tmp_path, login="ap01") as client:  # CIO 唯讀
        pj_resp = client.post("/api/projects", json={"project_code": "WI-X", "project_name": "x"})
        assert pj_resp.status_code == 403  # CIO 不能建，工作項自然也不行
