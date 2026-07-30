"""後台指派組長的管轄組別。

內建 ap05 的組別寫在程式裡，但管理員自己建的組長帳號要能在後台指派管哪一組，
否則新組長會沒有可見範圍。沒指派時保守退化成「只看自己的案」，不能變成「看全部」。
"""
import os

from fastapi.testclient import TestClient


# 測試密碼一律取 conftest 設好的環境變數，測試碼裡不留任何字面密碼
_PW = os.environ.get("AP02_PASSWORD", "")


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "adminuser.db")
    from app.main import create_app

    return TestClient(create_app())


def _login(client, username, pw=None):
    r = client.post("/api/auth/login", json={"username": username, "password": pw or _PW})
    assert r.status_code == 200, r.text


def _seed(table, payload):
    from app import store

    return store.insert_row(table, payload)


def _mk_leader(client, username, group):
    """後台建一個組長帳號並指派組別。新帳號沿用同一組測試密碼（來自環境變數）。"""
    r = client.post("/api/admin/users", json={
        "username": username, "role_code": "group_leader", "display_name": "新組長",
        "password": _PW, "group_name": group})
    assert r.status_code == 201, r.text


def test_建組長帳號時可直接指派組別(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "admin")
        _mk_leader(client, "lead1", "資料庫組")
        rows = {u["username"]: u for u in client.get("/api/admin/users").json()["data"]["users"]}
        assert rows["lead1"]["group_name"] == "資料庫組"


def test_後台指派的組別真的決定可見範圍(tmp_path):
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "DB-1", "title": "資料庫組案", "group_name": "資料庫組"})
        _seed("cases", {"case_code": "NET-1", "title": "網路組案", "group_name": "網路組"})
        _login(client, "admin")
        _mk_leader(client, "lead2", "資料庫組")
        _login(client, "lead2")
        codes = {c["case_code"] for c in client.get("/api/cases").json()["data"]}
        assert codes == {"DB-1"}


def test_改組別會換掉可見範圍(tmp_path):
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "DB-1", "title": "資料庫組案", "group_name": "資料庫組"})
        _seed("cases", {"case_code": "NET-1", "title": "網路組案", "group_name": "網路組"})
        _login(client, "admin")
        _mk_leader(client, "lead3", "資料庫組")
        r = client.patch("/api/admin/users/lead3", json={"group_name": "網路組"})
        assert r.status_code == 200, r.text
        _login(client, "lead3")
        codes = {c["case_code"] for c in client.get("/api/cases").json()["data"]}
        assert codes == {"NET-1"}          # 轉去管網路組，就看不到資料庫組了


def test_沒指派組別的組長只看自己的不是看全部(tmp_path):
    """保守預設：設定沒填完不該看到全公司。"""
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "OTHER", "title": "別人的案", "owner": "ap03", "group_name": "網路組"})
        _login(client, "admin")
        client.post("/api/admin/users", json={
            "username": "lead4", "role_code": "group_leader", "password": _PW})
        _login(client, "lead4")
        assert client.get("/api/cases").json()["data"] == []      # 看不到別人的
        mine = client.post("/api/cases", json={"title": "我自己開的"}).json()["data"]
        assert mine["owner"] == "lead4"                            # 退化成承辦模式：自動歸自己
        assert [c["title"] for c in client.get("/api/cases").json()["data"]] == ["我自己開的"]


def test_組別選項與人員主檔同一份(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "admin")
        d = client.get("/api/admin/users").json()["data"]
        assert d["groups"] == ["資料庫組", "網路組", "主機組", "專案及流程管理組"]


def test_內建組長的組別也看得到(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "admin")
        rows = {u["username"]: u for u in client.get("/api/admin/users").json()["data"]["users"]}
        assert rows["ap05"]["group_name"] == "網路組"
        assert rows["ap06"]["group_name"] == ""       # 部長不需要組別（看全部）


def test_只有管理員能改帳號組別(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "admin")
        _mk_leader(client, "lead5", "網路組")
        _login(client, "ap02")
        assert client.patch("/api/admin/users/lead5", json={"group_name": "主機組"}).status_code == 403
