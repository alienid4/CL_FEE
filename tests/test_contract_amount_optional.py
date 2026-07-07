"""合約金額留空時應存為 0，而非 422（前端空欄會送 null）。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "contract_amount.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_create_contract_with_null_amount(tmp_path):
    with _client(tmp_path) as client:
        r = client.post(
            "/api/contracts",
            json={"contract_code": "C-NULLAMT", "contract_name": "金額留空合約", "amount": None},
        )
        assert r.status_code == 201, r.text
        assert r.json()["data"]["amount"] == 0

        listed = client.get("/api/contracts").json()["data"]
        assert any(row["contract_code"] == "C-NULLAMT" for row in listed)


def test_create_contract_without_amount_field(tmp_path):
    with _client(tmp_path) as client:
        r = client.post(
            "/api/contracts",
            json={"contract_code": "C-NOAMT", "contract_name": "未帶金額欄位"},
        )
        assert r.status_code == 201, r.text
        assert r.json()["data"]["amount"] == 0
