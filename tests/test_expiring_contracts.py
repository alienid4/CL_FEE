"""到期提醒 /api/reports/expiring-contracts。

合約沒人管就是自動續約或斷保，所以不是「快到期」一句話帶過，而是按剩餘天數分階段
（已過期 / 7 / 30 / 60 / 90 天），且合約到期、保固到期、維護到期三種日期各自成一列
——續了約卻忘了續保是兩件事。
"""
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


def _in(days):
    return (date.today() + timedelta(days=days)).isoformat()


def test_expiring_lists_soon_and_past_not_far(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/contracts", json={"contract_code": "C-SOON", "contract_name": "快到期", "end_date": _in(30)})
        client.post("/api/contracts", json={"contract_code": "C-PAST", "contract_name": "已過期", "end_date": _in(-10)})
        client.post("/api/contracts", json={"contract_code": "C-FAR", "contract_name": "還很久", "end_date": _in(200)})
        client.post("/api/contracts", json={"contract_code": "C-NONE", "contract_name": "沒填到期日"})
        codes = {r["contract_code"] for r in client.get("/api/reports/expiring-contracts").json()["data"]["items"]}
        assert "C-SOON" in codes      # 90 天內
        assert "C-PAST" in codes      # 已過期也要提醒
        assert "C-FAR" not in codes   # 200 天後不算
        assert "C-NONE" not in codes  # 沒到期日不算


def test_expiry_staged_buckets(tmp_path):
    """五階段各自歸位：已過期 / 7 / 30 / 60 / 90 天，互斥且加總＝總筆數。"""
    with _client(tmp_path) as client:
        for code, days in [("S-OVER", -3), ("S-7", 5), ("S-30", 20), ("S-60", 45), ("S-90", 80)]:
            client.post("/api/contracts", json={"contract_code": code, "contract_name": code, "end_date": _in(days)})
        d = client.get("/api/reports/expiring-contracts").json()["data"]
        stage_of = {x["contract_code"]: x["stage"] for x in d["items"]}
        assert stage_of == {"S-OVER": "overdue", "S-7": "d7", "S-30": "d30", "S-60": "d60", "S-90": "d90"}
        assert d["counts"] == {"overdue": 1, "d7": 1, "d30": 1, "d60": 1, "d90": 1}
        assert sum(d["counts"].values()) == d["total"] == 5


def test_boundary_days_go_to_the_tighter_bucket(tmp_path):
    """剛好 7/30/60 天：歸在較急的那一格（7 天整算「7 天內」，不是 30 天內）。"""
    with _client(tmp_path) as client:
        for code, days in [("B-7", 7), ("B-30", 30), ("B-60", 60), ("B-90", 90), ("B-91", 91)]:
            client.post("/api/contracts", json={"contract_code": code, "contract_name": code, "end_date": _in(days)})
        stage_of = {x["contract_code"]: x["stage"]
                    for x in client.get("/api/reports/expiring-contracts").json()["data"]["items"]}
        assert stage_of["B-7"] == "d7"
        assert stage_of["B-30"] == "d30"
        assert stage_of["B-60"] == "d60"
        assert stage_of["B-90"] == "d90"
        assert "B-91" not in stage_of  # 超過 90 天不列入


def test_warranty_and_maintenance_are_separate_rows(tmp_path):
    """同一份合約的合約/保固/維護到期各自一列——續了約不代表保固也續了。"""
    with _client(tmp_path) as client:
        client.post("/api/contracts", json={
            "contract_code": "W-1", "contract_name": "主機維護",
            "end_date": _in(10), "warranty_end_date": _in(-5), "maintenance_end_date": _in(80)})
        d = client.get("/api/reports/expiring-contracts").json()["data"]
        by_kind = {x["kind"]: x for x in d["items"]}
        assert set(by_kind) == {"contract", "warranty", "maintenance"}
        assert by_kind["warranty"]["stage"] == "overdue"     # 保固已過期
        assert by_kind["contract"]["stage"] == "d30"         # 合約 10 天後到期
        assert by_kind["maintenance"]["stage"] == "d90"
        assert by_kind["warranty"]["kind_label"] == "保固到期"
        assert by_kind["warranty"]["days_left"] == -5        # 負數＝已過期幾天
        assert d["total"] == 3                               # 一份合約貢獻三筆


def test_disabled_contract_not_reminded(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/contracts", json={
            "contract_code": "D-1", "contract_name": "已停用", "end_date": _in(5)}).json()["data"]
        client.post(f"/api/contracts/{r['id']}/disable")
        codes = {x["contract_code"] for x in client.get("/api/reports/expiring-contracts").json()["data"]["items"]}
        assert "D-1" not in codes


def test_cio_overview_carries_expiry_counts(tmp_path):
    """CIO 決策總覽帶到期待處理筆數（一頁看得到還有幾件沒續）。"""
    with _client(tmp_path) as client:
        client.post("/api/contracts", json={"contract_code": "X-1", "contract_name": "過期約", "end_date": _in(-2)})
        client.post("/api/contracts", json={"contract_code": "X-2", "contract_name": "快斷保", "warranty_end_date": _in(3)})
        counts = client.get("/api/reports/cio-overview").json()["data"]["expiry_counts"]
        assert counts["overdue"] == 1 and counts["d7"] == 1


def test_expiring_requires_login(tmp_path):
    with _client(tmp_path, login=None) as client:
        assert client.get("/api/reports/expiring-contracts").status_code == 401
