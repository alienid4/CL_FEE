"""WBS 展延（第三次回饋 8.4「申請展延日期」）。

工作項逾期需要展延結束日時，不能直接把 end_date 蓋掉——答不出「原本訂哪天、為什麼展延、
展延到哪天、誰展延的」。跟 §10 合約費用調整（contract_adjustments）同一個 pattern：
end_date 欄位永遠是「現在的結束日」，歷史另存一張表。本測試涵蓋：
  - 展延後 end_date 變成新值，歷史留在 project_item_extensions
  - 燈號隨新結束日重判（除非是人工指定）
  - 紅/黃燈時關鍵風險點必填才能展延
  - 同日期不記錄、工作項不存在要擋
  - 展延會寫進稽核軌跡、也會反映到專案彙總
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "ext.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _item(client, **kw):
    p = client.post("/api/projects", json={"project_name": "機房搬遷"}).json()["data"]
    body = {"item_name": "設備清單提供", **kw}
    it = client.post(f"/api/projects/{p['id']}/items", json=body).json()["data"]
    return p, it


def test_extension_updates_end_date_and_keeps_history(tmp_path):
    with _client(tmp_path) as client:
        p, it = _item(client, start_date="2026-07-01", end_date="2026-07-10", risk_note="廠商延遲")
        assert it["rag"] == "red"          # 已過完成日還沒做完
        r = client.post(f"/api/project-items/{it['id']}/extensions", json={
            "new_end_date": "2026-09-30", "reason": "廠商延遲交貨"})
        assert r.status_code == 201, r.text
        history = r.json()["data"]
        assert len(history) == 1
        assert history[0]["old_end_date"] == "2026-07-10"
        assert history[0]["new_end_date"] == "2026-09-30"
        assert history[0]["reason"] == "廠商延遲交貨"
        assert history[0]["created_by"] == "ap02"

        after = client.get(f"/api/projects/{p['id']}/items").json()["data"][0]
        assert after["end_date"] == "2026-09-30"   # 現值已更新
        assert after["rag"] != "red"               # 展延到未來日期，燈號跟著重判，不再是已延遲


def test_multiple_extensions_accumulate_newest_first(tmp_path):
    with _client(tmp_path) as client:
        p, it = _item(client, start_date="2026-07-01", end_date="2026-07-10", risk_note="卡關")
        client.post(f"/api/project-items/{it['id']}/extensions", json={"new_end_date": "2026-08-01"})
        client.post(f"/api/project-items/{it['id']}/extensions", json={"new_end_date": "2026-09-30"})
        history = client.get(f"/api/project-items/{it['id']}/extensions").json()["data"]
        assert len(history) == 2
        assert history[0]["old_end_date"] == "2026-08-01" and history[0]["new_end_date"] == "2026-09-30"
        assert history[1]["old_end_date"] == "2026-07-10" and history[1]["new_end_date"] == "2026-08-01"


def test_same_end_date_is_rejected(tmp_path):
    with _client(tmp_path) as client:
        p, it = _item(client, end_date="2026-12-31")
        r = client.post(f"/api/project-items/{it['id']}/extensions", json={"new_end_date": "2026-12-31"})
        assert r.status_code == 400, r.text


def test_unknown_item_rejected(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/project-items/99999/extensions", json={"new_end_date": "2026-12-31"})
        assert r.status_code == 400, r.text


def test_red_or_yellow_after_extension_requires_risk_note(tmp_path):
    """展延後如果落在紅/黃燈區間（如展延到的日子還是很趕），沒填風險點要擋下來。
    起始狀態刻意不給起訖日＝建立當下是白燈（沒排日期），不用 risk_note 就能建立，
    問題出在「展延之後」才變黃燈，這時仍要擋。"""
    with _client(tmp_path) as client:
        p, it = _item(client)  # 沒給起訖日，建立當下是白燈，沒有 risk_note
        assert it["rag"] in ("", "white")
        r = client.post(f"/api/project-items/{it['id']}/extensions", json={
            # 展延到「今天」14 天內，near_due 規則會判成黃燈，仍要求風險點
            "new_end_date": "2026-08-20"})
        assert r.status_code == 400, r.text
        assert "關鍵風險點" in r.json()["detail"]
        # 沒有寫入任何歷史（擋在寫入之前）
        assert client.get(f"/api/project-items/{it['id']}/extensions").json()["data"] == []


def test_manual_rag_not_overridden_by_extension(tmp_path):
    """人工指定過燈號的（rag_manual=1），展延後燈號沿用人工值，不被自動判定蓋掉。"""
    with _client(tmp_path) as client:
        p, it = _item(client, start_date="2026-07-01", end_date="2026-07-10", risk_note="人工判斷正常")
        client.patch(f"/api/project-items/{it['id']}", json={"rag": "green"})   # 人工指定成綠燈
        after_patch = client.get(f"/api/projects/{p['id']}/items").json()["data"][0]
        assert after_patch["rag_manual"] == 1 and after_patch["rag"] == "green"

        client.post(f"/api/project-items/{it['id']}/extensions", json={"new_end_date": "2026-09-30"})
        after_ext = client.get(f"/api/projects/{p['id']}/items").json()["data"][0]
        assert after_ext["rag"] == "green"   # 人工值不被展延的自動判定蓋掉


def test_extension_is_audited(tmp_path):
    with _client(tmp_path) as client:
        p, it = _item(client, start_date="2026-07-01", end_date="2026-07-10", risk_note="卡關")
        client.post(f"/api/project-items/{it['id']}/extensions", json={"new_end_date": "2026-09-30"})
        logs = client.get("/api/audit-logs", params={"table_name": "project_items", "row_id": it["id"]}).json()["data"]
        assert any(x["action"] == "update" for x in logs)


def test_extension_rolls_up_to_project(tmp_path):
    """工作項展延後，專案主檔的彙總結束日要跟著變（沿用既有的彙總機制，不是新邏輯）。"""
    with _client(tmp_path) as client:
        p, it = _item(client, start_date="2026-07-01", end_date="2026-07-10", risk_note="卡關")
        client.post(f"/api/project-items/{it['id']}/extensions", json={"new_end_date": "2026-11-30"})
        proj = client.get("/api/projects").json()["data"][0]
        assert proj["end_date"] == "2026-11-30"
