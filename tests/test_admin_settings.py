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


def test_email_map_wildcard(tmp_path):
    with _client(tmp_path) as client:  # admin
        client.patch("/api/admin/settings", json={"email_map": "*=test@example.com"})
        from app import notify
        assert notify._email_map() == {"*": "test@example.com"}


def test_recipient_resolution(tmp_path):
    with _client(tmp_path) as client:  # admin
        client.post("/api/admin/users", json={"username": "dave", "role_code": "handler", "email": "dave@co", "password": "Dave!123"})
        from app import notify
        assert notify._recipient_for("dave", {"dave": "x@co"}) == "x@co"   # 個別對照優先
        assert notify._recipient_for("dave", {}) == "dave@co"              # 退回帳號 email
        assert notify._recipient_for("ghost", {"*": "all@co"}) == "all@co"  # catch-all
        assert notify._recipient_for("ghost", {}) == ""                    # 全無


def test_backup_download(tmp_path):
    with _client(tmp_path) as client:
        r = client.get("/api/admin/backup")
        assert r.status_code == 200
        assert r.content[:16] == b"SQLite format 3\x00"  # 是真的 SQLite 檔


def test_backup_blocked_for_non_admin(tmp_path):
    with _client(tmp_path, login="ap02") as client:
        assert client.get("/api/admin/backup").status_code == 403


def test_options_defaults_and_admin_override(tmp_path):
    with _client(tmp_path) as client:  # admin
        o = client.get("/api/options").json()["data"]
        assert "基礎建設" in o["budget_categories"] and "必要" in o["project_necessity"]
        client.patch("/api/admin/settings", json={"opt_budget_categories": "甲,乙,丙"})
        o2 = client.get("/api/options").json()["data"]
        assert o2["budget_categories"] == ["甲", "乙", "丙"]


def test_options_readable_by_manager(tmp_path):
    with _client(tmp_path, login="ap02") as client:
        assert client.get("/api/options").status_code == 200  # 任何登入者可讀選項


def test_admin_sees_only_admin_console(tmp_path):
    with _client(tmp_path) as client:
        me = client.get("/api/auth/me").json()["data"]
        assert me["allowed_modules"] == ["admin-console"]
        assert me["role_code"] == "admin"
