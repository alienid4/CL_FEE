"""合約續約提醒 /api/reports/expiring-contracts。"""
import os
from datetime import date, timedelta

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "exp.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_expiring_lists_soon_and_past_not_far(tmp_path):
    with _client(tmp_path) as client:
        soon = (date.today() + timedelta(days=30)).isoformat()
        past = (date.today() - timedelta(days=10)).isoformat()
        far = (date.today() + timedelta(days=200)).isoformat()
        client.post("/api/contracts", json={"contract_code": "C-SOON", "contract_name": "快到期", "end_date": soon})
        client.post("/api/contracts", json={"contract_code": "C-PAST", "contract_name": "已過期", "end_date": past})
        client.post("/api/contracts", json={"contract_code": "C-FAR", "contract_name": "還很久", "end_date": far})
        client.post("/api/contracts", json={"contract_code": "C-NONE", "contract_name": "沒填到期日"})
        codes = {r["contract_code"] for r in client.get("/api/reports/expiring-contracts").json()["data"]}
        assert "C-SOON" in codes     # 90 天內
        assert "C-PAST" in codes      # 已過期也要提醒
        assert "C-FAR" not in codes   # 200 天後不算
        assert "C-NONE" not in codes  # 沒到期日不算


def test_expiring_requires_login(tmp_path):
    with _client(tmp_path, login=None) as client:
        assert client.get("/api/reports/expiring-contracts").status_code == 401
