"""承辦(handler) 只看自己的案件：資料層權限防洩漏測試。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "scope.db")
    from app.main import create_app

    return TestClient(create_app())


def _seed(table, payload):
    from app import store

    return store.insert_row(table, payload)


def test_handler_sees_only_own_records(tmp_path):
    with _client(tmp_path) as client:
        mine = _seed("cases", {"case_code": "MINE", "title": "m", "owner": "ap03"})
        theirs = _seed("cases", {"case_code": "THEIRS", "title": "t", "owner": "ap02"})
        ct = _seed("contracts", {"contract_code": "CT", "contract_name": "x", "case_id": theirs["id"]})

        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        codes = {r["case_code"] for r in client.get("/api/cases").json()["data"]}
        assert codes == {"MINE"}                                                # 只看得到自己的
        assert client.get(f"/api/cases/{theirs['id']}/360").status_code == 404   # 別人的案件看不到
        assert client.get(f"/api/cases/{mine['id']}/360").status_code == 200     # 自己的看得到
        contract_ids = {r["id"] for r in client.get("/api/contracts").json()["data"]}
        assert ct["id"] not in contract_ids                                     # 別人案件下的合約也看不到
        assert client.get("/api/dashboard").json()["data"]["counts"]["cases"] == 1  # 儀表板只算自己的


def test_handler_created_case_is_auto_owned(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        client.post("/api/cases", json={"case_code": "AUTO", "title": "a", "owner": "someone-else"})
        cases = client.get("/api/cases").json()["data"]
        assert any(c["case_code"] == "AUTO" and c["owner"] == "ap03" for c in cases)  # 強制歸自己


def test_manager_sees_all(tmp_path):
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "A", "title": "a", "owner": "ap03"})
        _seed("cases", {"case_code": "B", "title": "b", "owner": "ap02"})
        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        codes = {r["case_code"] for r in client.get("/api/cases").json()["data"]}
        assert codes == {"A", "B"}  # 主管/助理看得到全部
