"""人員盤點與離職交接（使用者 2026-08-12「以後離職人員要怎麼處理」）。

兩個容易做錯的地方，這裡都測：
1. 案件的負責人存**登入帳號**，其他模組存**人名**——盤點兩種都要抓，只抓一種會漏一半。
2. 人名欄位允許共同負責人（實際資料裡有「陳昱杉/洪似妮」），轉走一個人不能把另一個也換掉。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "handover.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_共同負責人只換自己那一份(tmp_path):
    from app.store import _replace_person, _name_matches

    assert _replace_person("陳昱杉/洪似妮", "陳昱杉", "王大明") == "王大明/洪似妮"
    assert _replace_person("洪似妮/陳昱杉", "陳昱杉", "王大明") == "洪似妮/王大明"
    assert _replace_person("吳承翰&楊凡", "楊凡", "王大明") == "吳承翰&王大明"
    assert _name_matches("陳昱杉/洪似妮", "洪似妮") and not _name_matches("陳昱杉/洪似妮", "洪似")


def test_盤點同時抓帳號與人名(tmp_path):
    with _client(tmp_path) as client:
        # 案件掛帳號 ap03；專案與工作項掛人名
        client.post("/api/cases", json={"title": "青埔機房搬遷", "owner": "ap03"})
        p = client.post("/api/projects", json={"project_name": "機房搬遷專案", "owner": "林信成"}).json()["data"]
        client.post(f"/api/projects/{p['id']}/items", json={"item_name": "需求訪談", "owner": "林信成"})

        w = client.get("/api/personnel-workload/detail",
                       params={"name": "林信成", "username": "ap03"}).json()["data"]
        labels = {b["label"]: b["total"] for b in w["blocks"]}
        assert labels.get("案件") == 1        # 用帳號比對到的
        assert labels.get("專案") == 1 and labels.get("工作項") == 1   # 用人名比對到的
        assert w["total"] == 3

        # 只給人名 → 案件那塊抓不到（回傳有講明比對規則，不會讓人誤以為真的沒有）
        only_name = client.get("/api/personnel-workload/detail", params={"name": "林信成"}).json()["data"]
        assert "案件" not in {b["label"] for b in only_name["blocks"]}
        assert "帳號" in only_name["note"]


def test_交接前先看會動到哪些(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/projects", json={"project_name": "進行中的", "owner": "林信成"})
        done = client.post("/api/projects", json={"project_name": "已完成的", "owner": "林信成"}).json()["data"]
        client.patch(f"/api/projects/{done['id']}", json={"status": "completed"})

        pv = client.get("/api/handover/preview", params={"from_name": "林信成"}).json()["data"]
        assert pv["transfer_count"] == 1 and pv["keep_count"] == 1
        assert "歷史事實" in pv["keep_reason"]

        # 要連已結案一起轉也可以，但要自己勾
        pv2 = client.get("/api/handover/preview",
                         params={"from_name": "林信成", "include_closed": "true"}).json()["data"]
        assert pv2["transfer_count"] == 2 and pv2["keep_count"] == 0


def test_交接把資料轉給接手人並留稽核(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/cases", json={"title": "案子", "owner": "ap03"})
        client.post("/api/projects", json={"project_name": "專案", "owner": "林信成"})
        client.post("/api/projects", json={"project_name": "共同負責", "owner": "林信成/洪似妮"})

        r = client.post("/api/handover/apply", json={
            "from_name": "林信成", "to_name": "王大明",
            "from_username": "ap03", "to_username": "ap04", "reason": "林信成 8/31 離職",
        }).json()["data"]
        assert r["moved_count"] == 3

        # 只看我建的那筆：建專案時系統會自動配案件，那些的負責人是空的，本來就不該被轉
        cases = {c["title"]: c["owner"] for c in client.get("/api/cases").json()["data"]}
        assert cases["案子"] == "ap04"                            # 案件換成新帳號
        names = {p["project_name"]: p["owner"] for p in client.get("/api/projects").json()["data"]}
        assert names["專案"] == "王大明"
        assert names["共同負責"] == "王大明/洪似妮"                 # 另一個人沒被動到

        logs = client.get("/api/audit-logs", params={"action": "handover"}).json()["data"]
        assert len(logs) == 3                                    # 誰把誰轉給誰，查得到


def test_已結案的預設不轉(tmp_path):
    with _client(tmp_path) as client:
        a = client.post("/api/projects", json={"project_name": "還在跑", "owner": "林信成"}).json()["data"]
        b = client.post("/api/projects", json={"project_name": "早就結了", "owner": "林信成"}).json()["data"]
        client.patch(f"/api/projects/{b['id']}", json={"status": "completed"})

        r = client.post("/api/handover/apply", json={
            "from_name": "林信成", "to_name": "王大明"}).json()["data"]
        assert r["moved_count"] == 1

        owners = {p["project_name"]: p["owner"] for p in client.get("/api/projects").json()["data"]}
        assert owners["還在跑"] == "王大明"
        assert owners["早就結了"] == "林信成"      # 歷史留著：這案子當初是誰做的
        assert a["id"] and b["id"]


def test_全員負擔一覽依還在跑的排序(tmp_path):
    with _client(tmp_path) as client:
        for name in ("甲員", "乙員"):
            client.post("/api/personnel-master", json={"name": name, "group_name": "主機組"})
        client.post("/api/projects", json={"project_name": "P1", "owner": "乙員"})
        client.post("/api/projects", json={"project_name": "P2", "owner": "乙員"})
        client.post("/api/projects", json={"project_name": "P3", "owner": "甲員"})

        people = client.get("/api/personnel-workload").json()["data"]["people"]
        top = [p for p in people if p["name"] in ("甲員", "乙員")]
        assert top[0]["name"] == "乙員" and top[0]["active"] == 2   # 負擔重的排前面
        assert top[1]["name"] == "甲員" and top[1]["active"] == 1


def test_沒登記在主檔的人也要盤得到(tmp_path):
    """實測這台的人員主檔只登記 1 個人，但專案負責人有 8 個以上。
    只從主檔出發的話，真正要交接的人全部盤不到，功能等於白做。"""
    with _client(tmp_path) as client:
        client.post("/api/projects", json={"project_name": "沒登記的人在做", "owner": "路人甲"})
        client.post("/api/projects", json={"project_name": "共同負責", "owner": "路人甲/路人乙"})

        data = client.get("/api/personnel-workload").json()["data"]
        by_name = {p["name"]: p for p in data["people"]}
        assert by_name["路人甲"]["active"] == 2        # 兩筆都算他（含共同負責那筆）
        assert by_name["路人乙"]["active"] == 1        # 共同負責人各算一份
        assert by_name["路人甲"]["in_master"] is False  # 標出來提醒補登記
        assert data["not_in_master"] >= 2


def test_擋掉沒意義的交接(tmp_path):
    with _client(tmp_path) as client:
        assert client.post("/api/handover/apply", json={
            "from_name": "林信成", "to_name": "林信成"}).status_code == 422
        assert client.post("/api/handover/apply", json={
            "from_name": "", "to_name": "王大明"}).status_code == 422
