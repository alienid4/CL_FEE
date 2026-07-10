"""一條龍新案精靈：單頁多步驟表單一次送出，案件→(可選)簽呈/請購/合約→(可選)付款自動串 case_id/contract_id。
單一交易：任一步驟失敗，前面已建的一併回滾，不留半成品。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "wizard.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_case_only_minimal_submission(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/case-wizard", json={"case": {"case_code": "WIZ-1", "title": "只建案件"}})
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        assert d["case"]["case_code"] == "WIZ-1"
        assert d["signoff"] is None and d["purchase"] is None and d["contract"] is None and d["payment"] is None


def test_full_chain_auto_links_ids(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/case-wizard", json={
            "case": {"case_code": "WIZ-2", "title": "全套流程"},
            "signoff": {"signoff_code": "SG-WIZ-2", "subject": "簽呈"},
            "purchase": {"purchase_code": "PO-WIZ-2", "item_name": "採購品項"},
            "contract": {"contract_code": "K-WIZ-2", "contract_name": "合約"},
            "payment": {"payment_month": "2026-08", "payment_amount": 5000},
        })
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        case_id = d["case"]["id"]
        contract_id = d["contract"]["id"]
        assert d["signoff"]["case_id"] == case_id
        assert d["purchase"]["case_id"] == case_id
        assert d["contract"]["case_id"] == case_id
        assert d["payment"]["contract_id"] == contract_id
        assert d["payment"]["payment_amount"] == 5000

        # 案件 360 應能看到整條鏈
        detail = client.get(f"/api/cases/{case_id}/360").json()["data"]
        assert any(s["signoff_code"] == "SG-WIZ-2" for s in detail["signoffs"])
        assert any(p["purchase_code"] == "PO-WIZ-2" for p in detail["purchases"])
        assert len(detail["contracts"]) == 1


def test_payment_without_contract_rejected(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/case-wizard", json={
            "case": {"case_code": "WIZ-3", "title": "只填付款沒填合約"},
            "payment": {"payment_month": "2026-08", "payment_amount": 100},
        })
        assert r.status_code == 422
        # pydantic model_validator 的 422 detail 是結構化陣列（FastAPI 慣例），非純字串
        assert "合約" in r.json()["detail"][0]["msg"]
        # 驗證擋在最外層：案件本身也沒建立（連帶回滾整個請求，不留半成品）
        cases = client.get("/api/cases").json()["data"]
        assert not any(c["case_code"] == "WIZ-3" for c in cases)


def test_duplicate_contract_code_rolls_back_everything(tmp_path):
    with _client(tmp_path) as client:
        # 先建一個佔用 contract_code 的合約
        client.post("/api/contracts", json={"contract_code": "DUPK", "contract_name": "既有合約"})
        r = client.post("/api/case-wizard", json={
            "case": {"case_code": "WIZ-4", "title": "撞號測試"},
            "signoff": {"signoff_code": "SG-WIZ-4", "subject": "簽呈"},
            "contract": {"contract_code": "DUPK", "contract_name": "撞號合約"},
        })
        assert r.status_code == 422
        # 案件跟簽呈都不該被留下——整批回滾
        cases = client.get("/api/cases").json()["data"]
        assert not any(c["case_code"] == "WIZ-4" for c in cases)
        signoffs = client.get("/api/signoffs").json()["data"]
        assert not any(s["signoff_code"] == "SG-WIZ-4" for s in signoffs)


def test_cio_cannot_use_wizard(tmp_path):
    with _client(tmp_path, login="ap01") as client:
        r = client.post("/api/case-wizard", json={"case": {"case_code": "WIZ-5", "title": "CIO 不該能建"}})
        assert r.status_code == 403
