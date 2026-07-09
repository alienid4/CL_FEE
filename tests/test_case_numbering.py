"""系統編號：案件領年度流水號（同年遞增、跨年歸零），作業年度預設，四位尾碼＝案件身分證。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "num.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_case_seq_per_year(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/working-year?year=2026")
        a = client.post("/api/cases", json={"case_code": "A", "title": "Mail Server 維護"}).json()["data"]
        b = client.post("/api/cases", json={"case_code": "B", "title": "中華電信付款"}).json()["data"]
        c = client.post("/api/cases", json={"case_code": "C", "title": "明年案", "fiscal_year": "2027"}).json()["data"]
        d = client.post("/api/cases", json={"case_code": "D", "title": "又一案"}).json()["data"]
        assert (a["fiscal_year"], a["seq"]) == ("2026", 1)
        assert (b["fiscal_year"], b["seq"]) == ("2026", 2)
        assert (c["fiscal_year"], c["seq"]) == ("2027", 1)  # 跨年歸零
        assert (d["fiscal_year"], d["seq"]) == ("2026", 3)


def test_working_year_default_and_set(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/working-year?year=2027")
        assert client.get("/api/working-year").json()["data"]["working_year"] == "2027"
        # 不填 fiscal_year → 用作業年度
        cs = client.post("/api/cases", json={"case_code": "X", "title": "x"}).json()["data"]
        assert cs["fiscal_year"] == "2027"


def test_working_year_rejects_bad(tmp_path):
    with _client(tmp_path) as client:
        assert client.post("/api/working-year?year=abc").status_code == 400
        assert client.post("/api/working-year?year=26").status_code == 400


def test_working_year_set_blocked_for_handler(tmp_path):
    with _client(tmp_path, login="ap03") as client:
        assert client.post("/api/working-year?year=2027").status_code == 403
