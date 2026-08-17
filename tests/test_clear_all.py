"""清空業務資料（單機各自使用）：保留部門/人員/帳號/設定，清空前自動備份整個資料庫。
確認字串必須完全等於「ClearALL」（大小寫一致），不對就整個動作不執行、不留痕跡。"""
import os
from pathlib import Path

from fastapi.testclient import TestClient


def _client(tmp_path, login="admin"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "clear.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _seed(client):
    """業務資料＋要保留的部門/人員資料各建一筆。"""
    case = client.post("/api/cases", json={"case_code": "CLR-1", "title": "測試案件"}).json()["data"]
    client.post("/api/contracts", json={"contract_code": "CLRK-1", "contract_name": "測試合約", "amount": 1000})
    client.post("/api/unit-master", json={"canonical_code": "U1", "canonical_name": "測試部門"})
    client.post("/api/personnel-master", json={"name": "測試人員", "group_name": "測試組"})
    return case


def test_wrong_confirm_rejected(tmp_path):
    with _client(tmp_path) as client:
        case = _seed(client)
        r = client.post("/api/admin/clear-all", json={"confirm": "clearall"})  # 大小寫不符
        assert r.status_code == 400, r.text
        assert "ClearALL" in r.json()["detail"]
        # 沒對到就整個不執行，案件還在
        assert any(c["id"] == case["id"] for c in client.get("/api/cases").json()["data"])


def test_empty_confirm_rejected(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/admin/clear-all", json={"confirm": ""})
        assert r.status_code == 400, r.text


def test_clear_all_removes_business_keeps_org_data(tmp_path):
    with _client(tmp_path) as client:
        _seed(client)
        r = client.post("/api/admin/clear-all", json={"confirm": "ClearALL"})
        assert r.status_code == 200, r.text
        d = r.json()["data"]
        assert d["cleared_count"] > 0
        assert "cases" in d["cleared_tables"] and "contracts" in d["cleared_tables"]
        assert "personnel_master" not in d["cleared_tables"]
        assert "unit_master" not in d["cleared_tables"]

        assert client.get("/api/cases").json()["data"] == []
        assert client.get("/api/contracts").json()["data"] == []
        # 部門與人員主檔原封不動
        units = client.get("/api/unit-master").json()["data"]["masters"]
        people = client.get("/api/personnel-master").json()["data"]["masters"]
        assert any(u["canonical_code"] == "U1" for u in units)
        assert any(p["name"] == "測試人員" for p in people)


def test_clear_all_creates_backup_file(tmp_path):
    with _client(tmp_path) as client:
        _seed(client)
        r = client.post("/api/admin/clear-all", json={"confirm": "ClearALL"}).json()["data"]
        backup_path = Path(r["backup_path"])
        assert backup_path.exists()
        assert backup_path.stat().st_size > 0
        assert "clear_backups" in str(backup_path)


def test_clear_all_resets_autoincrement_only_for_cleared_tables(tmp_path):
    with _client(tmp_path) as client:
        c1 = client.post("/api/cases", json={"case_code": "CLR-A", "title": "第一筆"}).json()["data"]
        assert c1["id"] == 1
        client.post("/api/admin/clear-all", json={"confirm": "ClearALL"})
        c2 = client.post("/api/cases", json={"case_code": "CLR-B", "title": "清空後第一筆"}).json()["data"]
        assert c2["id"] == 1  # 業務資料流水號歸零，重新從 1 開始


def test_non_admin_cannot_clear_all(tmp_path):
    with _client(tmp_path, login="ap02") as client:
        _seed_ok = client.post("/api/cases", json={"case_code": "CLR-2", "title": "非admin"})
        r = client.post("/api/admin/clear-all", json={"confirm": "ClearALL"})
        assert r.status_code == 403
        # 沒被清掉
        assert any(c["case_code"] == "CLR-2" for c in client.get("/api/cases").json()["data"])


def test_clear_all_is_audited(tmp_path):
    with _client(tmp_path) as client:
        _seed(client)
        client.post("/api/admin/clear-all", json={"confirm": "ClearALL"})
        logs = client.get("/api/audit-logs", params={"table_name": "system"}).json()["data"]
        assert any(x["action"] == "clear-all" for x in logs)
