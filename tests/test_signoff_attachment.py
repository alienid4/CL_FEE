"""簽呈附件參照（勾稽用連結/路徑）：存得進、讀得回；空白預設不擋。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "signoff.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_signoff_attachment_ref_roundtrip(tmp_path):
    with _client(tmp_path) as client:
        s = client.post("/api/signoffs", json={
            "signoff_code": "36E100011300306", "subject": "EDR採購簽呈", "amount": 2400000,
            "status": "approved", "attachment_ref": "https://sign.example.com/doc/36E100011300306"}).json()["data"]
        got = next(r for r in client.get("/api/signoffs").json()["data"] if r["id"] == s["id"])
        assert got["attachment_ref"] == "https://sign.example.com/doc/36E100011300306"


def test_signoff_without_attachment_ok(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/signoffs", json={"signoff_code": "S-2", "subject": "無附件簽呈"})
        assert r.status_code == 201 and r.json()["data"]["attachment_ref"] == ""
