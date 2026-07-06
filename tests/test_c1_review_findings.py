"""C1 多 agent 審查確認的漏洞 → 落成測試（永久、跨工具）。

每個測試斷言「正確／安全」的行為。目前程式尚未修，故標 xfail：
- 測試 xfail（失敗）＝ 漏洞還在，已被記錄成待辦。
- 有人（Claude 或 Codex）修好後測試轉綠（xpass）＝ 修復的證據。

來源：docs/一次性開發提示詞_C1 的多 agent 審查（Workflow / review.py），2026-07。
規則見 C1 §5.1：審查發現一律落成測試才算數。
"""
import os

from fastapi.testclient import TestClient
import pytest


def client_for(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "review.db")
    from app.main import create_app

    return TestClient(create_app())


def _seed(table, payload):
    """繞過 API（避開認證議題），直接用 store 建立前置資料。"""
    from app import store

    return store.insert_row(table, payload)


def test_hardcoded_shared_password_should_not_work(tmp_path):
    # 切片 C 已修：per-user 雜湊密碼。舊的共用寫死密碼現在登不進去。
    with client_for(tmp_path) as client:
        r = client.post("/api/auth/login", json={"username": "ap01", "password": "1qaz@WSX"})
        assert r.status_code == 401  # 寫死密碼不該能登入


def test_forged_cookie_should_not_impersonate_cio(tmp_path):
    # 切片 A 已修：簽章 session。此測試現為正式綠燈守衛。
    with client_for(tmp_path) as client:
        client.cookies.set("ai_fee_user", "ap01")  # 沒登入，直接偽造 cookie
        r = client.get("/api/auth/me")
        assert r.status_code == 401  # 偽造 cookie 不該通過認證


def test_unauthenticated_write_should_be_rejected(tmp_path):
    # 切片 A 已修：/api/* 認證 middleware。此測試現為正式綠燈守衛。
    with client_for(tmp_path) as client:
        r = client.post("/api/cases", json={"case_code": "C1", "title": "x"})
        assert r.status_code in (401, 403)  # 未登入不該能新增資料


def test_unauthenticated_dev_console_should_be_rejected(tmp_path):
    # 切片 A 已修：middleware 一併護住 dev-console。此測試現為正式綠燈守衛。
    with client_for(tmp_path) as client:
        r = client.post("/api/dev-console/run", json={"command_id": "fast_ci", "dry_run": True})
        assert r.status_code in (401, 403)  # 未登入不該能觸發主機腳本


def test_patch_can_clear_nullable_fk(tmp_path):
    # 切片 E 已修：可為空外鍵可顯式清成 NULL。
    with client_for(tmp_path) as client:
        client.post("/api/auth/login", json={"username": "ap01", "password": "T3st!Pass"})
        case = _seed("cases", {"case_code": "K1", "title": "case"})
        contract = _seed("contracts", {"contract_code": "CT1", "contract_name": "c", "case_id": case["id"]})
        r = client.patch(f"/api/contracts/{contract['id']}", json={"case_id": None})
        assert r.status_code == 200
        assert r.json()["data"]["case_id"] is None  # 應能解除關聯（清 NULL）


def test_delete_contract_with_payments_should_not_silently_orphan(tmp_path):
    # 切片 E 已修：有子列時硬刪被擋（409），不再靜默孤立。
    with client_for(tmp_path) as client:
        client.post("/api/auth/login", json={"username": "ap01", "password": "T3st!Pass"})
        case = _seed("cases", {"case_code": "K2", "title": "case"})
        contract = _seed("contracts", {"contract_code": "CT2", "contract_name": "c", "case_id": case["id"]})
        _seed("payments", {"contract_id": contract["id"], "payment_month": "2026-01", "payment_amount": 100})
        r = client.delete(f"/api/contracts/{contract['id']}")
        assert r.status_code != 204  # 有子列時不該靜默硬刪、孤立 payment


def test_audit_log_records_real_actor(tmp_path):
    # 切片 D 已修：per-request 綁定操作者。稽核記錄真實登入者。
    with client_for(tmp_path) as client:
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        client.post("/api/cases", json={"case_code": "K3", "title": "case"})
        logs = client.get("/api/audit-logs", params={"limit": 5}).json()["data"]
        actors = [row.get("actor") for row in logs]
        assert "ap03" in actors  # 稽核應記錄實際操作者，而非 local-dev
