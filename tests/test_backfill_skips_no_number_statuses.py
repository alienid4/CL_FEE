"""補號不能補到「不該佔正式號」的案件。

backfill 是 v0.46 時代寫的：當時所有案件在建立當下就配號，沒有「暫時號」概念，
所以它原本只排除 disabled。2026-07-30 實測發現它會把剛被駁回的案件也配上正式號——
那個號從此永遠沒有有效案件對應，就是永久跳號，正好違反 A 案「沒過的申請不吃正式號」。
"""
import os

from fastapi.testclient import TestClient

_PW = os.environ.get("AP02_PASSWORD", "")


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "backfill.db")
    from app.main import create_app

    return TestClient(create_app())


def _login(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": _PW})
    assert r.status_code == 200, r.text


def _case(client, title):
    return client.post("/api/cases", json={"title": title}).json()["data"]


def _rows(client):
    return {c["title"]: c for c in client.get("/api/cases").json()["data"]}


def test_駁回與併案不補號其餘補號(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap02")
        keep = _case(client, "既有資料")          # 匯入來的那種：草稿、缺號 → 要補
        rej = _case(client, "被駁回的")
        mrg = _case(client, "被併走的")
        target = _case(client, "併入目標")
        for c in (rej, mrg):
            client.post(f"/api/cases/{c['id']}/submit")
        _login(client, "ap04")
        client.post(f"/api/cases/{rej['id']}/reject", json={"reason": "不予立案"})
        client.post(f"/api/cases/{mrg['id']}/merge", json={"target_case_id": target["id"]})

        _login(client, "admin")
        st = client.get("/api/dev-console/backfill/status").json()["data"]
        assert st["skipped_by_status"].get("rejected") == 1
        assert st["skipped_by_status"].get("merged") == 1
        client.post("/api/dev-console/backfill/run")

        _login(client, "ap02")
        rows = _rows(client)
        assert rows["既有資料"]["seq"] > 0        # 缺號的既有資料補到號
        assert rows["被駁回的"]["seq"] == 0       # 駁回的不能佔號
        assert rows["被併走的"]["seq"] == 0       # 併走的也不該有號


def test_補號狀態會按狀態分組讓人先看清楚(tmp_path):
    """按下去之前要知道會動到哪些狀態——混著等審核的新申請時，那是不同的事。"""
    with _client(tmp_path) as client:
        _login(client, "ap02")
        _case(client, "草稿一")
        _case(client, "草稿二")
        pend = _case(client, "待複核的")
        client.post(f"/api/cases/{pend['id']}/submit")

        _login(client, "admin")
        st = client.get("/api/dev-console/backfill/status").json()["data"]
        assert st["cases_by_status"].get("draft") == 2
        assert st["cases_by_status"].get("pending_review") == 1
        assert st["cases_missing"] == 3


def test_已核准的案件不會被重新配號(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap02")
        c = _case(client, "已核准的")
        client.post(f"/api/cases/{c['id']}/submit")
        _login(client, "ap04")
        seq = client.post(f"/api/cases/{c['id']}/approve").json()["data"]["seq"]
        assert seq > 0
        _login(client, "admin")
        client.post("/api/dev-console/backfill/run")
        _login(client, "ap02")
        assert _rows(client)["已核准的"]["seq"] == seq     # 號碼不變，外部已經引用它了
