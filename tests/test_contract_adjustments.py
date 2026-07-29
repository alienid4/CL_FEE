"""§10 合約費用調整（原始案例：中華電信板橋機櫃電力費調整）。

同一份合約中途改金額（機櫃增減、電費調價）不是新合約，也不能把 contracts.amount 直接蓋掉——
蓋掉就答不出「什麼時候、為什麼、從多少調到多少、誰調的」。本測試涵蓋：
  - 調整後合約金額變成新值，歷史留在 contract_adjustments
  - 差額由系統算（前端只給調整後金額，不給舊值，避免算錯）
  - 多次調整的累計增減與最初金額
  - 同額不記錄、合約不存在要擋
  - 調整會寫進稽核軌跡
"""
import os

from fastapi.testclient import TestClient


def _setup(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "adj.db")
    from app.main import create_app

    client = TestClient(create_app())
    client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
    return client


def _contract(client, code, amount):
    r = client.post("/api/contracts", json={"contract_code": code, "contract_name": "機櫃代管", "amount": amount})
    assert r.status_code == 201, r.text
    return r.json()["data"]


def test_adjustment_updates_amount_and_keeps_history(tmp_path):
    """電費調漲：合約金額變新值，但「原本多少、為什麼調」查得到。"""
    with _setup(tmp_path) as client:
        ct = _contract(client, "ADJ-1", 120_000)
        r = client.post(f"/api/contracts/{ct['id']}/adjustments", json={
            "new_amount": 138_000, "effective_date": "2026-09-01", "reason": "機櫃增加 2 台"})
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        assert d["count"] == 1
        assert d["original_amount"] == 120_000
        assert d["total_delta"] == 18_000
        item = d["items"][0]
        assert item["old_amount"] == 120_000 and item["new_amount"] == 138_000
        assert item["delta"] == 18_000                      # 差額由系統算
        assert item["reason"] == "機櫃增加 2 台"
        assert item["created_by"] == "ap02"                 # 誰調的
        # 合約金額本身已是調整後的現值
        assert client.get("/api/contracts").json()["data"][0]["amount"] == 138_000


def test_multiple_adjustments_accumulate(tmp_path):
    """調兩次：最初金額固定不變，累計增減是兩次的和；調降也算得對。"""
    with _setup(tmp_path) as client:
        ct = _contract(client, "ADJ-2", 100_000)
        client.post(f"/api/contracts/{ct['id']}/adjustments", json={
            "new_amount": 130_000, "effective_date": "2026-03-01", "reason": "電價調漲"})
        client.post(f"/api/contracts/{ct['id']}/adjustments", json={
            "new_amount": 115_000, "effective_date": "2026-09-01", "reason": "退租 1 櫃"})
        d = client.get(f"/api/contracts/{ct['id']}/adjustments").json()["data"]
        assert d["count"] == 2
        assert d["original_amount"] == 100_000   # 最初金額不會被後續調整蓋掉
        assert d["total_delta"] == 15_000        # +30000 然後 -15000
        assert d["items"][0]["effective_date"] == "2026-09-01"  # 新的在前
        assert d["items"][0]["delta"] == -15_000


def test_same_amount_is_rejected(tmp_path):
    """調成一樣的金額＝沒有東西要記，擋下來免得留一堆空紀錄。"""
    with _setup(tmp_path) as client:
        ct = _contract(client, "ADJ-3", 50_000)
        r = client.post(f"/api/contracts/{ct['id']}/adjustments", json={"new_amount": 50_000})
        assert r.status_code == 400, r.text


def test_unknown_contract_rejected(tmp_path):
    with _setup(tmp_path) as client:
        r = client.post("/api/contracts/99999/adjustments", json={"new_amount": 1000})
        assert r.status_code == 400, r.text


def test_no_adjustment_returns_empty_summary(tmp_path):
    with _setup(tmp_path) as client:
        ct = _contract(client, "ADJ-4", 80_000)
        d = client.get(f"/api/contracts/{ct['id']}/adjustments").json()["data"]
        assert d == {"count": 0, "original_amount": None, "total_delta": 0.0, "items": []}


def test_adjustment_is_audited(tmp_path):
    """金額被改要留稽核軌跡（誰在什麼時候把合約金額改掉）。"""
    with _setup(tmp_path) as client:
        ct = _contract(client, "ADJ-5", 200_000)
        client.post(f"/api/contracts/{ct['id']}/adjustments", json={"new_amount": 250_000, "reason": "加購"})
        logs = client.get("/api/audit-logs", params={"table_name": "contracts", "row_id": ct["id"]}).json()["data"]
        assert any(x["action"] == "update" for x in logs)


def test_adjustment_makes_schedule_mismatch_visible(tmp_path):
    """調整後付款排程會跟新金額對不上——這個差額要看得出來，才知道要補排程。"""
    with _setup(tmp_path) as client:
        import app.store as store

        ct = _contract(client, "ADJ-6", 120_000)
        store.generate_payment_schedules(ct["id"], "installment", 12)  # 每期 1 萬，合計 12 萬
        client.post(f"/api/contracts/{ct['id']}/adjustments", json={
            "new_amount": 138_000, "reason": "機櫃增加 2 台"})
        res = client.get(f"/api/contracts/{ct['id']}/payment-schedules").json()["data"]
        planned = res["summary"]["planned"]
        assert planned == 120_000                                    # 排程還是舊的
        assert client.get("/api/contracts").json()["data"][0]["amount"] == 138_000
        assert planned != 138_000                                    # 前端據此顯示「對不上」提醒
