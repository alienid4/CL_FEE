"""需求書 §4 核准之後的生命週期：已核准 → 進行中 → (暫停) → 已結案／已取消，結案可重開。

需求書明列「已結案案件可重新開啟，但必須記錄重新開啟人、時間與原因」，所以重開一定要留紀錄。
另外核准之後的狀態都還是「核准過的錢」，CIO 的金額不能因為案件開始執行就掉一塊。
"""
import os

from fastapi.testclient import TestClient

_PW = os.environ.get("AP02_PASSWORD", "")


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "lifecycle.db")
    from app.main import create_app

    return TestClient(create_app())


def _login(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": _PW})
    assert r.status_code == 200, r.text


def _approved_case(client, title="案"):
    """建一件並走完雙人複核，回到 ap02 身分。"""
    _login(client, "ap02")
    c = client.post("/api/cases", json={"title": title}).json()["data"]
    client.post(f"/api/cases/{c['id']}/submit")
    _login(client, "ap04")
    r = client.post(f"/api/cases/{c['id']}/approve")
    assert r.status_code == 200, r.text
    _login(client, "ap02")
    return r.json()["data"]


def _act(client, case_id, action, reason=""):
    return client.post(f"/api/cases/{case_id}/status/{action}", json={"reason": reason})


def _status(client, case_id):
    return next(c for c in client.get("/api/cases").json()["data"] if c["id"] == case_id)["status"]


def test_核准後可以開始執行(tmp_path):
    with _client(tmp_path) as client:
        c = _approved_case(client)
        assert _act(client, c["id"], "start").status_code == 200
        assert _status(client, c["id"]) == "in_progress"


def test_暫停要填原因復工可回進行中(tmp_path):
    with _client(tmp_path) as client:
        c = _approved_case(client)
        _act(client, c["id"], "start")
        assert _act(client, c["id"], "pause").status_code == 422          # 沒填原因擋下
        r = _act(client, c["id"], "pause", "等廠商報價")
        assert r.status_code == 200, r.text
        assert r.json()["data"]["status_note"] == "等廠商報價"             # 為什麼停在這裡查得到
        assert _act(client, c["id"], "resume").status_code == 200
        assert _status(client, c["id"]) == "in_progress"


def test_結案後重開必須記錄重開人時間原因(tmp_path):
    """需求書 §4 明列的要求。"""
    with _client(tmp_path) as client:
        c = _approved_case(client)
        _act(client, c["id"], "start")
        assert _act(client, c["id"], "close").status_code == 200
        assert _status(client, c["id"]) == "closed"
        assert _act(client, c["id"], "reopen").status_code == 422          # 不填原因不准重開
        r = _act(client, c["id"], "reopen", "廠商追加一批設備")
        assert r.status_code == 200, r.text
        d = r.json()["data"]
        assert d["status"] == "in_progress"
        assert d["reopened_by"] == "ap02"
        assert d["reopened_at"]                                            # 有時間戳
        assert d["reopen_reason"] == "廠商追加一批設備"


def test_不合法的轉換要擋掉(tmp_path):
    with _client(tmp_path) as client:
        c = _approved_case(client)
        assert _act(client, c["id"], "close").status_code == 409     # 還沒開始就結案
        assert _act(client, c["id"], "resume").status_code == 409    # 沒暫停過談不上復工
        _act(client, c["id"], "start")
        assert _act(client, c["id"], "start").status_code == 409     # 已經在跑了


def test_取消是終點不能再動(tmp_path):
    with _client(tmp_path) as client:
        c = _approved_case(client)
        assert _act(client, c["id"], "cancel").status_code == 422             # 要填原因
        assert _act(client, c["id"], "cancel", "需求取消").status_code == 200
        assert _status(client, c["id"]) == "cancelled"
        assert _act(client, c["id"], "start").status_code == 409              # 取消後走不回去
        assert _act(client, c["id"], "reopen", "想救回來").status_code == 409  # 也不能重開


def test_取消與重開限主管承辦不能按(tmp_path):
    with _client(tmp_path) as client:
        c = _approved_case(client)
        from app import store
        store.update_row("cases", c["id"], {"owner": "ap03"})       # 掛給承辦
        _login(client, "ap03")
        assert _act(client, c["id"], "start").status_code == 200    # 執行類：承辦自己的案可以
        assert _act(client, c["id"], "close").status_code == 200
        assert _act(client, c["id"], "cancel", "x").status_code == 403   # 決策類：承辦不行
        assert _act(client, c["id"], "reopen", "x").status_code == 403


def test_承辦不能動別人的案(tmp_path):
    with _client(tmp_path) as client:
        c = _approved_case(client)                                  # owner 不是 ap03
        _login(client, "ap03")
        assert _act(client, c["id"], "start").status_code == 404     # 不在可視範圍＝視同不存在


def test_進行中與已結案的付款仍算進CIO金額(tmp_path):
    """核准之後的狀態都是『核准過的錢』；只有已取消不算。少列一個，案件一開始執行 CIO 數字就會掉。"""
    with _client(tmp_path) as client:
        import app.store as store

        c = _approved_case(client, "有付款的案")
        ct = client.post("/api/contracts", json={
            "contract_code": "LC-K", "contract_name": "約", "amount": 100_000, "case_id": c["id"]}).json()["data"]
        client.post("/api/payments", json={
            "contract_id": ct["id"], "payment_month": "2026-08", "payment_amount": 50_000})
        base = client.get("/api/reports/cio-overview").json()["data"]["funds_to_prepare"]
        assert base == 50_000

        for action, reason in [("start", ""), ("pause", "等驗收"), ("resume", ""), ("close", "")]:
            _act(client, c["id"], action, reason)
            assert client.get("/api/reports/cio-overview").json()["data"]["funds_to_prepare"] == 50_000

        _act(client, c["id"], "reopen", "追加")
        _act(client, c["id"], "cancel", "整案取消")
        assert client.get("/api/reports/cio-overview").json()["data"]["funds_to_prepare"] == 0  # 撤案就不算


def test_狀態動作寫進稽核軌跡(tmp_path):
    with _client(tmp_path) as client:
        c = _approved_case(client)
        _act(client, c["id"], "start")
        _act(client, c["id"], "close")
        _act(client, c["id"], "reopen", "追加需求")
        logs = client.get("/api/audit-logs", params={"table_name": "cases", "row_id": c["id"]}).json()["data"]
        actions = {x["action"] for x in logs}
        assert {"status_in_progress", "status_closed", "reopen"} <= actions


def test_沒有這個狀態動作要回404(tmp_path):
    with _client(tmp_path) as client:
        c = _approved_case(client)
        assert _act(client, c["id"], "explode").status_code == 404
