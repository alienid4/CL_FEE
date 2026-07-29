"""人員主檔：組別歸屬 ＋ 後台增刪改。

助理回報「負責人下拉沒有資料可選」。除了要有名單，還要能長期維護——
人會轉組、會改名、會離職，所以每一筆都要能改組別、停用、刪除。
停用＝下拉選不到但歷史資料不動（案件上存的是名字文字，不是外鍵）。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "person.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _add(client, name, group="", note=""):
    r = client.post("/api/personnel-master", json={"name": name, "group_name": group, "note": note})
    assert r.status_code == 201, r.text
    return r.json()["data"]


def test_seed_demo_gives_four_groups_of_three(tmp_path):
    """示範名單：四組各三人，讓下拉一開始就有東西可選。"""
    with _client(tmp_path) as client:
        res = client.post("/api/personnel-master/seed-demo").json()["data"]
        assert res["created_count"] == 12
        data = client.get("/api/personnel-master").json()["data"]
        by_group = {}
        for p in data["masters"]:
            by_group.setdefault(p["group_name"], []).append(p["name"])
        assert set(by_group) == {"資料庫組", "網路組", "主機組", "專案及流程管理組"}
        assert all(len(v) == 3 for v in by_group.values())
        assert all(p["note"] == "示範資料" for p in data["masters"])  # 之後要清掉分得出來


def test_seed_demo_is_repeatable(tmp_path):
    """重複執行不會變成兩份（同名跳過）。"""
    with _client(tmp_path) as client:
        client.post("/api/personnel-master/seed-demo")
        again = client.post("/api/personnel-master/seed-demo").json()["data"]
        assert again["created_count"] == 0 and again["skipped_count"] == 12
        assert client.get("/api/personnel-master").json()["data"]["count"] == 12


def test_create_with_group_and_reject_duplicate(tmp_path):
    with _client(tmp_path) as client:
        p = _add(client, "王小明", "網路組", "測試")
        assert p["group_name"] == "網路組"
        dup = client.post("/api/personnel-master", json={"name": "王小明"})
        assert dup.status_code == 422    # 同名擋下，避免同一人兩種寫法


def test_transfer_group_and_rename(tmp_path):
    """轉組、改名都要改得動。"""
    with _client(tmp_path) as client:
        p = _add(client, "李大華", "主機組")
        r = client.patch(f"/api/personnel-master/{p['id']}", json={"group_name": "資料庫組"})
        assert r.status_code == 200, r.text
        assert r.json()["data"]["group_name"] == "資料庫組"
        r2 = client.patch(f"/api/personnel-master/{p['id']}", json={"name": "李大華(代理)"})
        assert r2.json()["data"]["name"] == "李大華(代理)"


def test_rename_into_existing_name_rejected(tmp_path):
    with _client(tmp_path) as client:
        _add(client, "甲君", "網路組")
        b = _add(client, "乙君", "網路組")
        assert client.patch(f"/api/personnel-master/{b['id']}", json={"name": "甲君"}).status_code == 422


def test_disable_hides_from_dropdown_but_keeps_record(tmp_path):
    """離職＝停用：表單下拉選不到，後台仍看得到（才能重新啟用）。"""
    with _client(tmp_path) as client:
        p = _add(client, "丙君", "主機組")
        client.patch(f"/api/personnel-master/{p['id']}", json={"status": "disabled"})
        assert client.get("/api/personnel-master").json()["data"]["count"] == 0          # 下拉拿不到
        full = client.get("/api/personnel-master", params={"include_disabled": True}).json()["data"]
        assert [x["status"] for x in full["masters"]] == ["disabled"]                    # 後台還在
        client.patch(f"/api/personnel-master/{p['id']}", json={"status": "active"})      # 可復職
        assert client.get("/api/personnel-master").json()["data"]["count"] == 1


def test_bad_status_rejected(tmp_path):
    with _client(tmp_path) as client:
        p = _add(client, "丁君")
        assert client.patch(f"/api/personnel-master/{p['id']}", json={"status": "離職中"}).status_code == 422


def test_delete_person(tmp_path):
    with _client(tmp_path) as client:
        p = _add(client, "戊君", "網路組")
        assert client.delete(f"/api/personnel-master/{p['id']}").status_code == 204
        assert client.get("/api/personnel-master").json()["data"]["count"] == 0


def test_person_group_options_available(tmp_path):
    """組別是後台可維護的選項（不同單位組織不一樣，不寫死）。"""
    with _client(tmp_path) as client:
        groups = client.get("/api/options").json()["data"]["person_groups"]
        assert groups == ["資料庫組", "網路組", "主機組", "專案及流程管理組"]


def test_handler_cannot_manage_personnel(tmp_path):
    """人員主檔屬後台維護，承辦不能改。"""
    with _client(tmp_path) as client:
        p = _add(client, "己君")
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        assert client.post("/api/personnel-master", json={"name": "偷加的"}).status_code == 403
        assert client.patch(f"/api/personnel-master/{p['id']}", json={"name": "改名"}).status_code == 403
        assert client.delete(f"/api/personnel-master/{p['id']}").status_code == 403
        assert client.post("/api/personnel-master/seed-demo").status_code == 403
