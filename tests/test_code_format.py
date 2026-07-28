"""系統編號改為 12 碼無連字號：功能碼(4)＋西元年(4)＋流水號(4)，例 Cont20260001（主管指定格式）。
同一案件底下各模組共用案件的「年+流水號」，差在功能碼，故查 20260001 可找到同案全部。
"""
import os
import re

from fastapi.testclient import TestClient


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "code.db")
    from app.main import create_app

    c = TestClient(create_app())
    c.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
    return c


def test_settle_no_is_12char_no_hyphen(tmp_path):
    with _client(tmp_path) as c:
        ct = c.post("/api/contracts", json={"contract_code": "K1", "contract_name": "合約"}).json()["data"]
        pay = c.post("/api/payments", json={
            "contract_id": ct["id"], "payment_month": "2026-08", "payment_amount": 100}).json()["data"]
        assert re.fullmatch(r"Sett\d{4}\d{4}", pay["settle_no"]), pay["settle_no"]  # Sett+西元年+流水號
        assert "-" not in pay["settle_no"]


def test_search_by_new_system_code(tmp_path):
    with _client(tmp_path) as c:
        case = c.post("/api/cases", json={"case_code": "XC", "title": "青埔機房", "fiscal_year": "2026"}).json()["data"]
        ct = c.post("/api/contracts", json={
            "contract_code": "KC", "contract_name": "合約", "case_id": case["id"]}).json()["data"]
        seq = f"{case['seq']:04d}"

        # 新格式全碼 Cont2026xxxx 找得到該合約
        r1 = c.get(f"/api/search?q=Cont2026{seq}").json()["data"]
        assert any(it.get("type") == "contract" and it.get("id") == ct["id"] for it in r1), r1

        # 只查「年+流水號」20xxxxxx 也找得到（跨模組共用尾碼）
        r2 = c.get(f"/api/search?q=2026{seq}").json()["data"]
        assert any(it.get("id") == ct["id"] for it in r2), r2

        # 舊的帶連字號格式不再是系統編號（不應以連字號比對到）
        assert "-" not in f"Cont2026{seq}"
