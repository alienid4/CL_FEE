"""標準採購流程的 WBS 工作項（黃助理 0803 附件二第三點；另一位助理 0807 的流程圖同一份）。
勾「涉及請購或合約」就把七個工作項排好，承辦仍可自己增刪。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "wbs.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


STANDARD = ["需求確認", "廠商報價", "上簽申請與核准", "議價", "合約簽訂", "執行／建置", "驗收", "結案"]


def test_勾了涉及請購就自動排標準流程(tmp_path):
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={
            "project_name": "機房擴充", "owner": "王小明", "involves_procurement": 1}).json()["data"]
        assert p["standard_wbs"]["created_count"] == len(STANDARD)
        items = client.get(f"/api/projects/{p['id']}/items").json()["data"]
        assert [i["item_name"] for i in items] == STANDARD
        # 助理特別強調：每一項都是完整的 WBS 項目，不是流程圖上的文字節點
        first = items[0]
        for field in ("owner", "start_date", "end_date", "sub_total", "sub_done", "progress", "rag", "risk_note"):
            assert field in first
        assert first["owner"] == "王小明"          # 負責人先帶專案負責人，之後可各自改
        assert first["seq"] == 1 and items[-1]["seq"] == len(STANDARD)


def test_沒勾就不排讓同仁自己建(tmp_path):
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={"project_name": "一般專案"}).json()["data"]
        assert "standard_wbs" not in p
        assert client.get(f"/api/projects/{p['id']}/items").json()["data"] == []


def test_既有專案可補排且不覆蓋已填內容(tmp_path):
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={"project_name": "0803 之前建的"}).json()["data"]
        # 承辦已經自己建了一項同名的，而且填了進度
        client.post(f"/api/projects/{p['id']}/items", json={
            "item_name": "需求確認", "sub_total": 4, "sub_done": 2})

        r = client.post(f"/api/projects/{p['id']}/standard-wbs").json()["data"]
        assert r["created_count"] == len(STANDARD) - 1
        assert r["skipped"] == ["需求確認"]

        items = {i["item_name"]: i for i in client.get(f"/api/projects/{p['id']}/items").json()["data"]}
        assert len(items) == len(STANDARD)                 # 沒有長出重複的
        assert items["需求確認"]["sub_done"] == 2          # 既有內容原封不動


def test_重複按不會長出兩套(tmp_path):
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={
            "project_name": "重跑", "involves_procurement": 1}).json()["data"]
        again = client.post(f"/api/projects/{p['id']}/standard-wbs").json()["data"]
        assert again["created_count"] == 0 and again["skipped_count"] == len(STANDARD)
        assert len(client.get(f"/api/projects/{p['id']}/items").json()["data"]) == len(STANDARD)


def test_工作項名稱可由後台改(tmp_path):
    """助理原話：「系統不預先限制 WBS 工作項目名稱，上述僅為建議的標準工作項目」。"""
    with _client(tmp_path, login="admin") as admin:
        admin.patch("/api/admin/settings", json={"opt_wbs_standard_items": "甲階段,乙階段"})
    with _client(tmp_path) as client:
        assert client.get("/api/options").json()["data"]["wbs_standard_items"] == ["甲階段", "乙階段"]
        p = client.post("/api/projects", json={
            "project_name": "自訂流程", "involves_procurement": 1}).json()["data"]
        items = client.get(f"/api/projects/{p['id']}/items").json()["data"]
        assert [i["item_name"] for i in items] == ["甲階段", "乙階段"]


def test_排完的工作項不會一建好就亂判燈號(tmp_path):
    """剛排進來還沒填起訖日，硬判燈號會讓整排專案一開好就是紅的。"""
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={
            "project_name": "燈號", "involves_procurement": 1}).json()["data"]
        items = client.get(f"/api/projects/{p['id']}/items").json()["data"]
        assert all(i["rag"] in ("", "white", "todo") for i in items), [i["rag"] for i in items]
        assert all(i["progress"] == 0 for i in items)


def test_專案找不到時回404(tmp_path):
    with _client(tmp_path) as client:
        assert client.post("/api/projects/99999/standard-wbs").status_code == 404
