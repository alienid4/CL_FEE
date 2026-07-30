"""批次審核／批次狀態動作。

第一次上線會有幾十筆匯入資料要一起處理（實際案例：87 筆），一筆一筆按不現實。
刻意不做成單一交易：一筆失敗（最常見是「不能核准自己建立的案件」）不該讓其他幾十筆
一起回滾，而是逐筆處理並回報每一筆結果。
"""
import os

from fastapi.testclient import TestClient

_PW = os.environ.get("AP02_PASSWORD", "")


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "batch.db")
    from app.main import create_app

    return TestClient(create_app())


def _login(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": _PW})
    assert r.status_code == 200, r.text


def _cases(client, n, prefix="B"):
    return [client.post("/api/cases", json={"title": f"{prefix}-{i}"}).json()["data"] for i in range(n)]


def _batch(client, action, ids, reason=""):
    return client.post(f"/api/case-batch/{action}", json={"ids": ids, "reason": reason})


def _status_of(client, cid):
    return next(c for c in client.get("/api/cases").json()["data"] if c["id"] == cid)["status"]


def test_批次送審(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap02")
        rows = _cases(client, 5)
        ids = [c["id"] for c in rows]
        r = _batch(client, "submit", ids)
        assert r.status_code == 200, r.text
        d = r.json()["data"]
        assert d["done_count"] == 5 and d["failed_count"] == 0
        assert all(_status_of(client, i) == "pending_review" for i in ids)


def test_批次核准由另一人執行(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap02")
        ids = [c["id"] for c in _cases(client, 4)]
        _batch(client, "submit", ids)
        _login(client, "ap04")                       # 換人核准（雙人複核）
        d = _batch(client, "approve", ids).json()["data"]
        assert d["done_count"] == 4 and d["failed_count"] == 0
        assert all(_status_of(client, i) == "approved" for i in ids)


def test_自己建的案批次核准會被逐筆擋下並回報原因(tmp_path):
    """整批不會因為其中幾筆不能核就全部回滾——這是刻意的。"""
    with _client(tmp_path) as client:
        _login(client, "ap02")
        mine = [c["id"] for c in _cases(client, 2, "MINE")]
        _batch(client, "submit", mine)
        _login(client, "ap04")
        others = [c["id"] for c in _cases(client, 3, "OTHER")]
        _batch(client, "submit", others)
        # ap04 一次選了「ap02 建的 2 筆」＋「自己建的 3 筆」
        d = _batch(client, "approve", mine + others).json()["data"]
        assert d["done_count"] == 2                  # 別人建的過了
        assert d["failed_count"] == 3                # 自己建的沒過
        assert all("自己" in f["reason"] for f in d["failed"])
        assert all(_status_of(client, i) == "approved" for i in mine)
        assert all(_status_of(client, i) == "pending_review" for i in others)


def test_批次退件要帶原因(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap02")
        ids = [c["id"] for c in _cases(client, 3)]
        _batch(client, "submit", ids)
        _login(client, "ap04")
        assert _batch(client, "return", ids).json()["data"]["failed_count"] == 3   # 沒填原因全失敗
        d = _batch(client, "return", ids, "附件不齊").json()["data"]
        assert d["done_count"] == 3
        rows = {c["id"]: c for c in client.get("/api/cases").json()["data"]}
        assert all(rows[i]["review_note"] == "附件不齊" for i in ids)


def test_批次狀態動作(tmp_path):
    """核准後的生命週期也能批次推：一起開始執行、一起結案。"""
    with _client(tmp_path) as client:
        _login(client, "ap02")
        ids = [c["id"] for c in _cases(client, 3)]
        _batch(client, "submit", ids)
        _login(client, "ap04")
        _batch(client, "approve", ids)
        assert _batch(client, "start", ids).json()["data"]["done_count"] == 3
        assert all(_status_of(client, i) == "in_progress" for i in ids)
        assert _batch(client, "close", ids).json()["data"]["done_count"] == 3
        assert all(_status_of(client, i) == "closed" for i in ids)


def test_承辦不能批次審核(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap02")
        ids = [c["id"] for c in _cases(client, 2)]
        _batch(client, "submit", ids)
        _login(client, "ap03")
        assert _batch(client, "approve", ids).status_code == 403
        assert _batch(client, "reject", ids, "x").status_code == 403


def test_不存在的動作與空清單(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap02")
        ids = [c["id"] for c in _cases(client, 1)]
        assert _batch(client, "explode", ids).status_code == 404
        assert client.post("/api/case-batch/submit", json={"ids": []}).status_code == 422


def test_一次上限500筆(tmp_path):
    """防手滑，也避免這個端點變成大量寫入的入口。"""
    with _client(tmp_path) as client:
        _login(client, "ap02")
        assert client.post("/api/case-batch/submit", json={"ids": list(range(1, 502))}).status_code == 422


def test_找不到的案件只讓那一筆失敗(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap02")
        ids = [c["id"] for c in _cases(client, 2)]
        d = _batch(client, "submit", ids + [99999]).json()["data"]
        assert d["done_count"] == 2 and d["failed_count"] == 1
        assert d["failed"][0]["id"] == 99999
