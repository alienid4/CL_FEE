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


def _approve(client, case_id):
    """送審→由另一人核准（雙人複核）。核准當下才配正式流水號。"""
    client.post(f"/api/cases/{case_id}/submit")
    client.post("/api/auth/login", json={"username": "ap04", "password": "T3st!Pass"})
    r = client.post(f"/api/cases/{case_id}/approve")
    client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
    assert r.status_code == 200, r.text
    return r.json()["data"]


def test_申請階段只有暫時號(tmp_path):
    """使用者拍板 A 案：建案只配暫時號（temp_seq），正式流水號留到核准才發。"""
    with _client(tmp_path) as client:
        client.post("/api/working-year?year=2026")
        a = client.post("/api/cases", json={"case_code": "A", "title": "Mail Server 維護"}).json()["data"]
        b = client.post("/api/cases", json={"case_code": "B", "title": "中華電信付款"}).json()["data"]
        c = client.post("/api/cases", json={"case_code": "C", "title": "明年案", "fiscal_year": "2027"}).json()["data"]
        assert (a["fiscal_year"], a["temp_seq"], a["seq"]) == ("2026", 1, 0)
        assert (b["fiscal_year"], b["temp_seq"], b["seq"]) == ("2026", 2, 0)
        assert (c["fiscal_year"], c["temp_seq"], c["seq"]) == ("2027", 1, 0)  # 暫時號也是跨年歸零


def test_核准才配正式號且不跳號(tmp_path):
    """正式流水號在核准當下才配：沒過的申請不吃號，年度編號連續不跳號。"""
    with _client(tmp_path) as client:
        client.post("/api/working-year?year=2026")
        a = client.post("/api/cases", json={"case_code": "A", "title": "先申請的"}).json()["data"]
        b = client.post("/api/cases", json={"case_code": "B", "title": "後來被駁回的"}).json()["data"]
        d = client.post("/api/cases", json={"case_code": "D", "title": "再後面的"}).json()["data"]

        assert _approve(client, a["id"])["seq"] == 1
        client.post(f"/api/cases/{b['id']}/reject", json={"reason": "重複申請"})  # B 沒過
        assert _approve(client, d["id"])["seq"] == 2   # 正式號接在 1 後面，B 沒把 2 吃掉
        rejected = next(c for c in client.get("/api/cases").json()["data"] if c["id"] == b["id"])
        assert rejected["seq"] == 0 and rejected["status"] == "rejected"  # 被駁回的沒有正式號，但紀錄還在


def test_跨年度正式號各自歸零(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/working-year?year=2026")
        a = client.post("/api/cases", json={"case_code": "A", "title": "今年案"}).json()["data"]
        c = client.post("/api/cases", json={"case_code": "C", "title": "明年案", "fiscal_year": "2027"}).json()["data"]
        assert _approve(client, a["id"])["seq"] == 1
        assert _approve(client, c["id"])["seq"] == 1   # 不同年度各自從 1 起算


def test_配過正式號就不再換號(tmp_path):
    """已配過正式號的案子若日後被重新送審核准（如結案後重開），號碼不能變——外部已經引用它了。
    目前 UI 沒有「已核准再送審」的路徑，這裡直接把狀態改回待複核來驗這道防護。"""
    with _client(tmp_path) as client:
        import app.store as store

        client.post("/api/working-year?year=2026")
        a = client.post("/api/cases", json={"case_code": "A", "title": "案"}).json()["data"]
        first = _approve(client, a["id"])["seq"]
        store.update_row("cases", a["id"], {"status": "pending_review"})
        again = _approve(client, a["id"])["seq"]
        assert first == again == 1


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
