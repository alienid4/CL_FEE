"""試辦免密碼登入：預設仍需密碼；PILOT_PASSWORDLESS=1 時選角色即可登入。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "pw.db")
    from app.main import create_app

    return TestClient(create_app())


def test_options_lists_accounts_and_password_required_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("PILOT_PASSWORDLESS", raising=False)
    with _client(tmp_path) as c:
        opt = c.get("/api/auth/options").json()["data"]
        assert opt["passwordless"] is False
        usernames = {a["username"] for a in opt["accounts"]}
        assert {"ap01", "ap02", "ap03"} <= usernames  # 下拉至少有三個主要角色
        # 預設：無密碼被拒、正確密碼才過
        assert c.post("/api/auth/login", json={"username": "ap02"}).status_code == 401
        assert c.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"}).status_code == 200


def test_passwordless_login_when_flag_on(tmp_path, monkeypatch):
    monkeypatch.setenv("PILOT_PASSWORDLESS", "1")
    with _client(tmp_path) as c:
        assert c.get("/api/auth/options").json()["data"]["passwordless"] is True
        r = c.post("/api/auth/login", json={"username": "ap02"})  # 免密碼、只給角色
        assert r.status_code == 200 and r.json()["data"]["username"] == "ap02"
        # 非內建帳號不吃免密碼（就算旗標開著也一樣要密碼）
        assert c.post("/api/auth/login", json={"username": "nobody"}).status_code == 401
