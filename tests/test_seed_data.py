"""測試種子資料（demo）：一鍵載入 / 一鍵清空 + 權限 + 不碰真資料。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "seed.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_load_then_clear(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/dev-console/demo-data/load")
        assert r.status_code == 200, r.text
        assert r.json()["data"]["cases"] == 3

        cases = client.get("/api/cases").json()["data"]
        assert any(c["case_code"] == "DEMO-C01" for c in cases)
        # demo 每筆都明顯標示
        assert all(c["title"].startswith("［測試］") for c in cases if c["case_code"].startswith("DEMO-"))

        contracts = client.get("/api/contracts").json()["data"]
        assert any(c["contract_code"] == "DEMO-K01" for c in contracts)
        payments = client.get("/api/payments").json()["data"]
        assert len(payments) == 4  # 3 筆固定月份 + 1 筆動態「下月」給 CIO 看板

        r = client.post("/api/dev-console/demo-data/clear")
        assert r.status_code == 200
        assert client.get("/api/cases").json()["data"] == [] or all(
            not c["case_code"].startswith("DEMO-") for c in client.get("/api/cases").json()["data"]
        )
        assert client.get("/api/payments").json()["data"] == []


def test_load_is_idempotent(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/dev-console/demo-data/load")
        client.post("/api/dev-console/demo-data/load")
        demo_cases = [c for c in client.get("/api/cases").json()["data"] if c["case_code"].startswith("DEMO-")]
        assert len(demo_cases) == 3  # 重複載入不會變 6


def test_clear_never_touches_real_data(tmp_path):
    with _client(tmp_path) as client:
        # 一筆真資料（無 DEMO- 標記）
        client.post("/api/cases", json={"case_code": "REAL-001", "title": "真的案件"})
        client.post("/api/dev-console/demo-data/load")
        client.post("/api/dev-console/demo-data/clear")
        codes = [c["case_code"] for c in client.get("/api/cases").json()["data"]]
        assert "REAL-001" in codes  # 真資料還在
        assert not any(code.startswith("DEMO-") for code in codes)  # demo 全清掉


def test_cio_cannot_load(tmp_path):
    with _client(tmp_path, login="ap01") as client:  # CIO 唯讀
        assert client.post("/api/dev-console/demo-data/load").status_code == 403


def test_handler_cannot_load(tmp_path):
    with _client(tmp_path, login="ap03") as client:  # 承辦：dev-console 前綴禁用
        assert client.post("/api/dev-console/demo-data/load").status_code == 403


def test_requires_login(tmp_path):
    with _client(tmp_path, login=None) as client:
        assert client.post("/api/dev-console/demo-data/load").status_code == 401
