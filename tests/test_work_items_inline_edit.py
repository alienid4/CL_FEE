"""工作項 inline 編輯：驗證前端 inline 依賴的後端 partial PATCH，以及前端關鍵接線存在。

inline 編輯的設計是「每格只送有動到的欄位」，所以後端必須支援單欄／多欄的部分更新，
而且不能把沒送的欄位洗掉（exclude_unset）。這裡用純 API 驗這個契約，不需瀏覽器；
另補一個靜態檢查，確保前端 inline 接線在、舊的逐列「編輯」按鈕已移除。
"""
import os
from pathlib import Path

from fastapi.testclient import TestClient

WEB = Path(__file__).resolve().parent.parent / "app" / "web"


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "inline.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _new_item(client):
    pid = client.post(
        "/api/projects", json={"project_code": "INL-1", "project_name": "inline專案"}
    ).json()["data"]["id"]
    it = client.post(
        f"/api/projects/{pid}/items",
        json={"item_name": "項目A", "owner": "王小明", "exec_status": "進行中", "rag": "綠"},
    ).json()["data"]
    return pid, it


def test_inline_patch_single_and_composite_fields(tmp_path):
    """燈號(rag)、追蹤三欄、日期都要能各自 partial 更新，且互不覆蓋。"""
    with _client(tmp_path) as client:
        pid, it = _new_item(client)
        iid = it["id"]

        # 執行進度格：exec_status + 燈號一起改
        upd = client.patch(
            f"/api/project-items/{iid}", json={"exec_status": "已完成", "rag": "紅"}
        ).json()["data"]
        assert upd["exec_status"] == "已完成" and upd["rag"] == "紅"

        # 追蹤事項格：風險/決策/支援三欄一起送
        upd = client.patch(
            f"/api/project-items/{iid}",
            json={"risk_note": "供應商延誤", "decision_needed": "是否加預算", "support_needed": "採購協助"},
        ).json()["data"]
        assert upd["risk_note"] == "供應商延誤"
        assert upd["decision_needed"] == "是否加預算"
        assert upd["support_needed"] == "採購協助"

        # 只改單一格：負責人 / 開始日，不能動到其他欄位
        client.patch(f"/api/project-items/{iid}", json={"owner": "陳美惠"})
        client.patch(f"/api/project-items/{iid}", json={"start_date": "2026-06-01"})

        final = next(
            x for x in client.get(f"/api/projects/{pid}/items").json()["data"] if x["id"] == iid
        )
        assert final["owner"] == "陳美惠"
        assert final["start_date"] == "2026-06-01"
        # 前面設過的值沒被後續單欄 PATCH 洗掉（exclude_unset 生效）
        assert final["exec_status"] == "已完成" and final["rag"] == "紅"
        assert final["risk_note"] == "供應商延誤"


def test_inline_edit_frontend_contract():
    """前端 inline 接線在，且舊的逐列『編輯』按鈕已移除（避免不小心改回表單式）。"""
    app_js = (WEB / "app.js").read_text(encoding="utf-8")
    styles = (WEB / "styles.css").read_text(encoding="utf-8")

    # inline 引擎與單欄 PATCH
    assert "function pfBeginEdit" in app_js
    assert "function pfCommitEdit" in app_js
    assert "/api/project-items/${id}" in app_js
    assert 'data-field="' in app_js  # 可編輯格帶欄位標記
    assert "function pfItemRag" in app_js  # 燈號依開始/結束日與完成度自動判定
    assert "pfRagOptions" not in app_js  # 手動燈號選單已移除（改自動）

    # 舊的逐列「編輯」按鈕已拿掉，改成直接點格子
    assert "data-item-edit" not in app_js

    # CSS：固定欄寬 + 可編輯格樣式
    assert ".pf-items-table" in styles
    assert "td.editable" in styles
