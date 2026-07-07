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


def test_handler_forbidden_from_audit_and_import(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        assert client.get("/api/audit-logs").status_code == 403          # 承辦不得看稽核
        assert client.get("/api/import-batches").status_code == 403       # 承辦不得看匯入
        assert client.post("/api/import-batches", json={"source_name": "x.csv"}).status_code == 403
        assert client.get("/api/dev-console/status").status_code == 403   # 承辦不得用 dev-console
        assert client.post("/api/dev-console/run", json={"command_id": "fast_ci", "dry_run": True}).status_code == 403
        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        assert client.get("/api/audit-logs").status_code == 200           # 主管仍可用
        assert client.get("/api/import-batches").status_code == 200


def test_handler_cannot_write_to_others_records(tmp_path):
    """越權防護：承辦不得改/作廢/刪/竊佔別人的資料（多 agent 審查抓到的洞）。"""
    with _client(tmp_path) as client:
        theirs = _seed("cases", {"case_code": "OWN-BY-2", "title": "t", "owner": "ap02"})
        their_ct = _seed("contracts", {"contract_code": "CT2", "contract_name": "c", "case_id": theirs["id"]})
        their_doc = _seed("documents", {"file_name": "d.pdf", "case_id": theirs["id"]})
        their_pay = _seed("payments", {"contract_id": their_ct["id"], "payment_month": "2026-01", "payment_amount": 100})

        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        assert client.patch(f"/api/cases/{theirs['id']}", json={"title": "hacked"}).status_code == 404   # 改別人 → 擋
        assert client.patch(f"/api/cases/{theirs['id']}", json={"owner": "ap03"}).status_code in (404, 422)  # 竊佔 owner → 擋（owner 被丟棄→空欄位）
        assert client.post(f"/api/contracts/{their_ct['id']}/disable").status_code == 404                 # 作廢別人 → 擋
        assert client.delete(f"/api/documents/{their_doc['id']}").status_code == 404                      # 刪別人文件 → 擋
        assert client.delete(f"/api/payments/{their_pay['id']}").status_code == 404                       # 刪別人付款 → 擋

        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
        got = next(c for c in client.get("/api/cases").json()["data"] if c["id"] == theirs["id"])
        assert got["title"] == "t" and got["owner"] == "ap02"  # 資料未被動


def test_handler_can_write_to_own_records(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        mine = client.post("/api/cases", json={"case_code": "MY-OWN", "title": "m"}).json()["data"]
        r = client.patch(f"/api/cases/{mine['id']}", json={"title": "updated"})
        assert r.status_code == 200 and r.json()["data"]["title"] == "updated"  # 改自己的 → 可以
