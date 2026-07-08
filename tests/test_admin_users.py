"""帳號權限管理：admin 建立/停用/刪除 DB 帳號；DB 帳號可登入；內建帳號受保護。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="admin"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "users.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_non_admin_cannot_manage_users(tmp_path):
    with _client(tmp_path, login="ap02") as client:
        assert client.get("/api/admin/users").status_code == 403
        assert client.post("/api/admin/users", json={"username": "x", "role_code": "handler", "password": "p"}).status_code == 403


def test_create_db_user_and_login(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/admin/users", json={"username": "alice", "role_code": "manager_assistant", "display_name": "Alice", "email": "a@co", "password": "Alice!123"})
        assert r.status_code == 201
        listed = client.get("/api/admin/users").json()["data"]["users"]
        assert any(u["username"] == "alice" and not u["builtin"] for u in listed)
        # 新帳號可登入，且拿到該角色的模組
        c2 = TestClient(client.app)
        me = c2.post("/api/auth/login", json={"username": "alice", "password": "Alice!123"}).json()["data"]
        assert me["role_code"] == "manager_assistant" and "cases-module" in me["allowed_modules"]


def test_disabled_user_cannot_login(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/admin/users", json={"username": "bob", "role_code": "handler", "password": "Bob!123"})
        client.patch("/api/admin/users/bob", json={"disabled": True})
        c2 = TestClient(client.app)
        assert c2.post("/api/auth/login", json={"username": "bob", "password": "Bob!123"}).status_code == 401


def test_reset_password(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/admin/users", json={"username": "carol", "role_code": "handler", "password": "old!123"})
        client.patch("/api/admin/users/carol", json={"password": "new!456"})
        c2 = TestClient(client.app)
        assert c2.post("/api/auth/login", json={"username": "carol", "password": "old!123"}).status_code == 401
        assert c2.post("/api/auth/login", json={"username": "carol", "password": "new!456"}).status_code == 200


def test_builtin_accounts_protected(tmp_path):
    with _client(tmp_path) as client:
        assert client.patch("/api/admin/users/ap02", json={"disabled": True}).status_code == 403
        assert client.delete("/api/admin/users/ap01").status_code == 403
        assert client.post("/api/admin/users", json={"username": "ap02", "role_code": "handler", "password": "p"}).status_code == 409


def test_create_bad_role_rejected(tmp_path):
    with _client(tmp_path) as client:
        assert client.post("/api/admin/users", json={"username": "dave", "role_code": "wizard", "password": "p"}).status_code == 422


def test_delete_db_user(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/admin/users", json={"username": "eve", "role_code": "handler", "password": "Eve!123"})
        assert client.delete("/api/admin/users/eve").status_code == 204
        assert not any(u["username"] == "eve" for u in client.get("/api/admin/users").json()["data"]["users"])
