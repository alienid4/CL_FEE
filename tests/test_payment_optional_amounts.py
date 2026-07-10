"""付款「未稅金額/營業稅」為選填：前端留空會送 JSON null，後端須視為 0（同 ContractIn.amount 慣例）。

迴歸涵蓋的 bug：PaymentIn.net_amount/tax_amount 原本是 `float = 0`（非 Optional），
收到 null 會被 pydantic 拒絕（422），導致使用者只要不填這兩個選填欄位就存不了付款。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "pay_opt.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_create_payment_with_null_amounts_defaults_to_zero(tmp_path):
    with _client(tmp_path) as client:
        ct = client.post("/api/contracts", json={"contract_code": "K-OPT", "contract_name": "合約"}).json()["data"]
        r = client.post("/api/payments", json={
            "contract_id": ct["id"], "payment_month": "2026-08", "payment_amount": 1000,
            "net_amount": None, "tax_amount": None,
        })
        assert r.status_code == 201, r.text
        payment = r.json()["data"]
        assert payment["net_amount"] == 0
        assert payment["tax_amount"] == 0


def test_create_payment_without_amounts_field_still_defaults_to_zero(tmp_path):
    with _client(tmp_path) as client:
        ct = client.post("/api/contracts", json={"contract_code": "K-OPT2", "contract_name": "合約"}).json()["data"]
        r = client.post("/api/payments", json={
            "contract_id": ct["id"], "payment_month": "2026-08", "payment_amount": 1000,
        })
        assert r.status_code == 201, r.text
        payment = r.json()["data"]
        assert payment["net_amount"] == 0
        assert payment["tax_amount"] == 0
