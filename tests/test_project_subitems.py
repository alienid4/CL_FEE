"""工作項底下的子項目（使用者 2026-08-12：「子項總數怎不能繼續追下去」）。

原本 sub_total／sub_done 只是兩個數字，填了 3/3 也看不出那三項是什麼。
拆了子項之後，那兩個數字改由子項算出來，並一路滾到工作項燈號與專案完成度。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "subitem.db")
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


def test_新增子項目後父工作項數字自動算(tmp_path):
    with _client(tmp_path) as client:
        p, it = _item(client)
        for name in ("網路設備", "主機設備", "資料庫設備"):
            client.post(f"/api/project-items/{it['id']}/subitems", json={"name": name})
        res = client.post(f"/api/project-items/{it['id']}/subitems",
                          json={"name": "資安設備", "done": 1}).json()["data"]
        assert res["item"]["sub_total"] == 4 and res["item"]["sub_done"] == 1
        assert res["item"]["progress"] == 25.0          # 1/4，人不用自己填

        subs = client.get(f"/api/project-items/{it['id']}/subitems").json()["data"]
        assert [s["name"] for s in subs] == ["網路設備", "主機設備", "資料庫設備", "資安設備"]
        assert [s["seq"] for s in subs] == [1, 2, 3, 4]  # 標號自動排


def test_勾完成會一路滾到專案完成度(tmp_path):
    with _client(tmp_path) as client:
        p, it = _item(client)
        ids = [client.post(f"/api/project-items/{it['id']}/subitems",
                           json={"name": f"第{i}項"}).json()["data"]["subitem"]["id"]
               for i in range(1, 5)]
        for sid in ids:
            client.patch(f"/api/project-subitems/{sid}", json={"done": 1})

        item = client.get(f"/api/projects/{p['id']}/items").json()["data"][0]
        assert item["sub_done"] == 4 and item["progress"] == 100.0
        assert item["rag"] == "gray"                    # 全做完＝灰燈
        prj = [x for x in client.get("/api/projects").json()["data"] if x["id"] == p["id"]][0]
        assert prj["progress"] == 100.0                 # 專案完成度跟著長出來


def test_刪掉子項目數字跟著回來(tmp_path):
    with _client(tmp_path) as client:
        p, it = _item(client)
        a = client.post(f"/api/project-items/{it['id']}/subitems",
                        json={"name": "A", "done": 1}).json()["data"]["subitem"]
        client.post(f"/api/project-items/{it['id']}/subitems", json={"name": "B"})

        res = client.delete(f"/api/project-subitems/{a['id']}").json()["data"]
        assert res["item"]["sub_total"] == 1 and res["item"]["sub_done"] == 0


def test_舊資料只有數字可以拆成子項目(tmp_path):
    """Excel 帶進來的是 3/3，那三項是什麼沒人知道——照數字拆出空白列讓承辦自己補，
    名稱不猜內容（猜出來的名字看起來像真的，最危險）。"""
    with _client(tmp_path) as client:
        p, it = _item(client, sub_total=3, sub_done=2, owner="林信成")
        res = client.post(f"/api/project-items/{it['id']}/split").json()["data"]
        assert res["created"] == 3 and res["done"] == 2

        subs = client.get(f"/api/project-items/{it['id']}/subitems").json()["data"]
        assert [s["name"] for s in subs] == ["子項目 1", "子項目 2", "子項目 3"]
        assert [s["done"] for s in subs] == [1, 1, 0]   # 前兩筆對齊原本的已完成數
        assert all(s["owner"] == "林信成" for s in subs)  # 負責人先沿用工作項的
        assert res["item"]["sub_total"] == 3 and res["item"]["sub_done"] == 2   # 數字不變


def test_已經有子項就不給重拆(tmp_path):
    with _client(tmp_path) as client:
        p, it = _item(client, sub_total=2)
        client.post(f"/api/project-items/{it['id']}/subitems", json={"name": "已經有的"})
        r = client.post(f"/api/project-items/{it['id']}/split")
        assert r.status_code == 409 and "已經有子項目" in r.json()["detail"]


def test_沒有數字可拆時說清楚(tmp_path):
    with _client(tmp_path) as client:
        p, it = _item(client)                            # sub_total 0
        r = client.post(f"/api/project-items/{it['id']}/split")
        assert r.status_code == 422 and "直接新增子項目" in r.json()["detail"]


def test_子項全刪光退回用執行進度判斷(tmp_path):
    """拆過又全刪掉，不能卡在 0%——回到跟沒拆過的工作項一樣，看「執行進度」那欄。"""
    with _client(tmp_path) as client:
        p, it = _item(client, exec_status="已完成", end_date="2025-08-29")
        s = client.post(f"/api/project-items/{it['id']}/subitems",
                        json={"name": "唯一一項"}).json()["data"]
        assert s["item"]["progress"] == 0.0              # 有子項時以子項為準：0/1
        res = client.delete(f"/api/project-subitems/{s['subitem']['id']}").json()["data"]
        assert res["item"]["progress"] == 100.0          # 沒子項了 → 看執行進度「已完成」
        assert res["item"]["rag"] == "gray"


def test_名稱必填與找不到的情形(tmp_path):
    with _client(tmp_path) as client:
        p, it = _item(client)
        assert client.post(f"/api/project-items/{it['id']}/subitems", json={"name": ""}).status_code == 422
        assert client.post("/api/project-items/99999/subitems", json={"name": "X"}).status_code == 404
        assert client.patch("/api/project-subitems/99999", json={"done": 1}).status_code == 404
        assert client.delete("/api/project-subitems/99999").status_code == 404
