"""系統管理後台：設定讀寫、admin-only、SMTP 密碼 write-only。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="admin"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "admin.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_non_admin_blocked(tmp_path):
    with _client(tmp_path, login="ap02") as client:
        assert client.get("/api/admin/settings").status_code == 403
        assert client.patch("/api/admin/settings", json={"smtp_host": "x"}).status_code == 403


def test_admin_reads_and_writes_settings(tmp_path):
    with _client(tmp_path) as client:
        r = client.get("/api/admin/settings")
        assert r.status_code == 200
        assert r.json()["data"]["smtp_password_set"] is False

        client.patch("/api/admin/settings", json={"smtp_host": "mail.co", "smtp_port": "587", "email_map": "ap02=a@co"})
        data = client.get("/api/admin/settings").json()["data"]
        assert data["smtp_host"] == "mail.co" and data["smtp_port"] == "587"
        assert data["email_map"] == "ap02=a@co"


def test_smtp_password_write_only(tmp_path):
    with _client(tmp_path) as client:
        client.patch("/api/admin/settings", json={"smtp_password": "s3cret"})
        data = client.get("/api/admin/settings").json()["data"]
        assert data["smtp_password_set"] is True
        assert "smtp_password" not in data  # 永不回傳明碼

        # 空密碼不清掉已設定的
        client.patch("/api/admin/settings", json={"smtp_password": "", "smtp_host": "mail2.co"})
        data2 = client.get("/api/admin/settings").json()["data"]
        assert data2["smtp_password_set"] is True
        assert data2["smtp_host"] == "mail2.co"


def test_test_email_without_smtp(tmp_path):
    with _client(tmp_path) as client:
        res = client.post("/api/admin/settings/test-email", json={"to": "x@co"}).json()["data"]
        assert res["sent"] is False and "SMTP" in res["reason"]


def test_admin_sees_only_admin_console(tmp_path):
    with _client(tmp_path) as client:
        me = client.get("/api/auth/me").json()["data"]
        assert me["allowed_modules"] == ["admin-console"]
        assert me["role_code"] == "admin"
