"""工作項「執行進度＝已完成」但沒拆子項時，燈號不該被判成已延遲。

使用者 2026-08-12 在正式庫看到的：同一列「執行進度：已完成」「燈號：已延遲」，
26 個專案都中——子項總數 0 → 完成度算 0% → 過了結束日就自動判紅燈。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "wbslight.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _project(client):
    return client.post("/api/projects", json={"project_name": "機房搬遷"}).json()["data"]


def test_已完成但沒拆子項不再被判已延遲(tmp_path):
    with _client(tmp_path) as client:
        p = _project(client)
        item = client.post(f"/api/projects/{p['id']}/items", json={
            "item_name": "廠商HPE需求訪談", "exec_status": "已完成",
            "start_date": "2025-08-08", "end_date": "2025-08-29",   # 早就過期了
            "sub_total": 0, "sub_done": 0,
        }).json()["data"]
        assert item["progress"] == 100          # 承辦說做完了，就是 100%
        assert item["rag"] == "gray"            # 灰＝已完成，不是紅＝已延遲


def test_有拆子項時仍以子項為準(tmp_path):
    """助理規格：進度由子項目數算。有子項就別讓文字欄位蓋掉真實數字。"""
    with _client(tmp_path) as client:
        p = _project(client)
        item = client.post(f"/api/projects/{p['id']}/items", json={
            "item_name": "設備清單提供", "exec_status": "已完成",
            "sub_total": 4, "sub_done": 1,
        }).json()["data"]
        assert item["progress"] == 25           # 1/4，不是 100


def test_未完成不能被誤判成完成(tmp_path):
    with _client(tmp_path) as client:
        p = _project(client)
        item = client.post(f"/api/projects/{p['id']}/items", json={
            "item_name": "驗收", "exec_status": "尚未完成",
            "start_date": "2025-01-01", "end_date": "2025-02-01", "risk_note": "廠商延遲交貨",
        }).json()["data"]
        assert item["progress"] == 0            # 「尚未完成」含「完成」兩字，但不是完成
        assert item["rag"] == "red"


def test_舊資料重開服務就自動修正(tmp_path):
    """既有工作項的進度與燈號是存在資料庫裡的，修了算法還要把舊資料刷過才看得到效果。"""
    with _client(tmp_path) as client:
        import app.store as store

        p = _project(client)
        it = client.post(f"/api/projects/{p['id']}/items", json={
            "item_name": "需求訪談", "exec_status": "已完成",
            "start_date": "2025-08-08", "end_date": "2025-08-29",
        }).json()["data"]
        # 退回成修正前的樣子：進度 0、燈號紅
        with store.connect() as conn:
            conn.execute("UPDATE project_items SET progress = 0, rag = 'red' WHERE id = ?", (it["id"],))
        stale = client.get(f"/api/projects/{p['id']}/items").json()["data"][0]
        assert stale["progress"] == 0 and stale["rag"] == "red"

    with _client(tmp_path) as client2:          # 重開服務（＝使用者更新後重啟）
        fixed = client2.get(f"/api/projects/{p['id']}/items").json()["data"][0]
        assert fixed["progress"] == 100 and fixed["rag"] == "gray"
        # 專案主檔的完成度也要跟著重算，不然清單還是舊數字
        prj = [x for x in client2.get("/api/projects").json()["data"] if x["id"] == p["id"]][0]
        assert prj["progress"] == 100


def test_人工指定過的燈號不被覆蓋(tmp_path):
    """需求書 §6：燈號可由系統判斷，也保留人工調整。人工決定的不能被開機修正洗掉。"""
    with _client(tmp_path) as client:
        import app.store as store

        p = _project(client)
        it = client.post(f"/api/projects/{p['id']}/items", json={
            "item_name": "上線", "exec_status": "已完成", "end_date": "2025-08-29",
            "rag": "yellow", "risk_note": "雖然做完但要觀察一週",
        }).json()["data"]
        with store.connect() as conn:
            conn.execute("UPDATE project_items SET progress = 0 WHERE id = ?", (it["id"],))

    with _client(tmp_path) as client2:
        after = client2.get(f"/api/projects/{p['id']}/items").json()["data"][0]
        assert after["progress"] == 100         # 進度該補
        assert after["rag"] == "yellow"         # 但人工指定的燈號留著
