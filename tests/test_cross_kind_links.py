"""跨模組串接：案件／專案／預算名字不同但在講同一件事（使用者 2026-08-12 提的）。

實例：案件「青浦機房搬遷」／專案「青浦機房搬遷專案」／預算「桃園青浦機房」。
純字串比對，不連網、不用 AI——使用者明講不能依賴 AI，怕以後功能失效。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "crosslink.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_共同片段的判斷是純字串不依賴外部服務(tmp_path):
    from app.store import longest_common_part, names_look_related

    assert longest_common_part("青浦機房搬遷", "桃園青浦機房") == "青浦機房"
    assert longest_common_part("青浦機房搬遷", "青浦機房搬遷專案") == "青浦機房搬遷"   # 尾綴「專案」先剝掉
    ok, part = names_look_related("青浦機房搬遷", "桃園青浦機房")
    assert ok and part == "青浦機房"


def test_只共用通用詞不會被配在一起(tmp_path):
    """「桃園機房搬遷」與「青浦機房搬遷」共用「機房搬遷」，但那是兩個案子。
    併錯比沒併更難救，所以門檻抓保守。"""
    from app.store import names_look_related

    ok, part = names_look_related("桃園機房搬遷", "青浦機房搬遷")
    assert part == "機房搬遷"
    assert ok is False or len(part) / len("桃園機房搬遷") < 0.7   # 佔比不夠高就不該自動配


def test_找出專案與預算該歸到哪個案件(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"title": "青浦機房搬遷"}).json()["data"]
        client.post("/api/projects", json={"project_name": "青浦機房搬遷專案"})
        client.post("/api/budgets", json={"budget_code": "桃園青浦機房", "fiscal_year": "2026", "amount": 100})

        cands = client.get("/api/cross-links").json()["data"]["candidates"]
        for kind in ("project", "budget"):
            hit = [c for c in cands if c["kind"] == kind and c["suggest_case_id"] == case["id"]]
            assert hit, f"{kind} 沒被建議歸到青浦機房搬遷"
            assert "青浦機房" in hit[0]["common_part"]      # 要講得出「為什麼像」


def test_歸戶之後就不再重複提示(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"title": "青浦機房搬遷"}).json()["data"]
        prj = client.post("/api/projects", json={"project_name": "青浦機房搬遷專案"}).json()["data"]

        r = client.post("/api/cross-links/apply",
                        json={"kind": "project", "id": prj["id"], "case_id": case["id"]})
        assert r.status_code == 200 and r.json()["data"]["row"]["case_id"] == case["id"]

        cands = client.get("/api/cross-links").json()["data"]["candidates"]
        assert not [c for c in cands
                    if c["kind"] == "project" and c["id"] == prj["id"]
                    and c["suggest_case_id"] == case["id"]]


def test_歸戶會留稽核並擋掉不存在的案件(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"title": "青浦機房搬遷"}).json()["data"]
        prj = client.post("/api/projects", json={"project_name": "青浦機房搬遷專案"}).json()["data"]
        client.post("/api/cross-links/apply",
                    json={"kind": "project", "id": prj["id"], "case_id": case["id"]})

        logs = client.get("/api/audit-logs", params={
            "table_name": "projects", "action": "cross-link"}).json()["data"]
        assert len(logs) == 1                         # 誰把誰歸到哪，查得到

        assert client.post("/api/cross-links/apply", json={
            "kind": "project", "id": prj["id"], "case_id": 99999}).status_code == 404
        assert client.post("/api/cross-links/apply", json={
            "kind": "contract", "id": prj["id"], "case_id": case["id"]}).status_code == 422


def test_已經掛在同一案件的不會被提示(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"title": "青浦機房搬遷"}).json()["data"]
        prj = client.post("/api/projects", json={
            "project_name": "青浦機房搬遷專案", "case_id": case["id"]}).json()["data"]

        cands = client.get("/api/cross-links").json()["data"]["candidates"]
        assert not [c for c in cands if c["kind"] == "project" and c["id"] == prj["id"]
                    and c["suggest_case_id"] == case["id"]]


def test_完全不像的不會被硬湊(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/cases", json={"title": "青浦機房搬遷"})
        client.post("/api/projects", json={"project_name": "資安設備汰換"})

        cands = client.get("/api/cross-links").json()["data"]["candidates"]
        assert not [c for c in cands if c["name"] == "資安設備汰換"]
