"""Excel 匯入正式寫入的安全閘門：驗證/交易/冪等/來源舉證/稽核。"""
import json
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "imp.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _stage(client, rows):
    batch = client.post("/api/import-batches", json={"source_name": "cases.csv"}).json()["data"]
    client.post(f"/api/import-batches/{batch['id']}/rows", json={"rows": rows})
    return batch["id"]


def _write(client, batch_id, confirmed_fields):
    return client.post(
        f"/api/import-batches/{batch_id}/confirm",
        json={"dry_run": False, "target_tables": ["cases"], "confirmed_fields": confirmed_fields},
    )


def test_formal_write_creates_and_records_provenance(tmp_path):
    with _client(tmp_path) as client:
        bid = _stage(client, [
            {"case_code": "IMP-1", "title": "匯入案一", "owner": "Ops", "amount": "1000"},
            {"case_code": "IMP-2", "title": "匯入案二", "owner": "Fin", "amount": "2000"},
        ])
        confirmed = [
            {"row_number": 1, "target_table": "cases", "target_field": "amount"},
            {"row_number": 2, "target_table": "cases", "target_field": "amount"},
        ]
        r = _write(client, bid, confirmed)
        assert r.status_code == 200 and r.json()["data"]["created_count"] == 2
        rows = client.get("/api/cases").json()["data"]
        codes = {c["case_code"] for c in rows}
        assert {"IMP-1", "IMP-2"} <= codes
        # Excel 來源勾稽：每筆案件記了來源檔＋原始列號（清單 📎 用）
        by_code = {c["case_code"]: c for c in rows}
        assert by_code["IMP-1"]["source_file"] == "cases.csv"
        assert by_code["IMP-1"]["source_row"] == 1
        assert by_code["IMP-2"]["source_row"] == 2
        # 稽核有 import 動作，且記了批次來源
        logs = client.get("/api/audit-logs", params={"table_name": "cases", "action": "import"}).json()["data"]
        assert len(logs) == 2
        after = json.loads(logs[0]["after_json"])
        assert after["import_batch_id"] == bid and "import_row_number" in after


def test_formal_write_is_idempotent(tmp_path):
    with _client(tmp_path) as client:
        bid = _stage(client, [{"case_code": "IMP-DUP", "title": "重跑", "amount": "500"}])
        confirmed = [{"row_number": 1, "target_table": "cases", "target_field": "amount"}]
        assert _write(client, bid, confirmed).json()["data"]["created_count"] == 1
        second = _write(client, bid, confirmed).json()["data"]
        assert second["created_count"] == 0 and second["skipped_count"] == 1  # 冪等：不重複
        assert len([c for c in client.get("/api/cases").json()["data"] if c["case_code"] == "IMP-DUP"]) == 1


def test_formal_write_blocked_when_amount_not_confirmed(tmp_path):
    with _client(tmp_path) as client:
        bid = _stage(client, [{"case_code": "IMP-NC", "title": "未確認金額", "amount": "9999"}])
        r = _write(client, bid, [])  # 金額需人工確認卻未確認 → 擋
        assert r.status_code == 422
        assert client.get("/api/cases").json()["data"] == []  # 完全沒寫


def test_formal_write_blocked_for_handler(tmp_path):
    with _client(tmp_path, login="ap03") as client:  # 承辦被 import 前綴擋
        assert client.post("/api/import-batches", json={"source_name": "x.csv"}).status_code == 403
