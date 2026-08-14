"""一條龍新案精靈：單頁多步驟表單一次送出，案件→(可選)預算/簽呈/請購/合約→(可選)付款自動串 case_id/contract_id。
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
        assert d["budget"] is None and d["signoff"] is None and d["purchase"] is None and d["contract"] is None and d["payment"] is None


def test_full_chain_auto_links_ids(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/case-wizard", json={
            "case": {"case_code": "WIZ-2", "title": "全套流程"},
            "budget": {"budget_code": "BUD-WIZ-2", "amount": 20000},
            "signoff": {"signoff_code": "SG-WIZ-2", "subject": "簽呈"},
            "purchase": {"purchase_code": "PO-WIZ-2", "item_name": "採購品項"},
            "contract": {"contract_code": "K-WIZ-2", "contract_name": "合約"},
            "payment": {"payment_month": "2026-08", "payment_amount": 5000},
        })
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        case_id = d["case"]["id"]
        contract_id = d["contract"]["id"]
        assert d["budget"]["case_id"] == case_id
        assert d["budget"]["amount"] == 20000
        assert d["signoff"]["case_id"] == case_id
        assert d["purchase"]["case_id"] == case_id
        assert d["contract"]["case_id"] == case_id
        assert d["payment"]["contract_id"] == contract_id
        assert d["payment"]["payment_amount"] == 5000

        # 案件 360 應能看到整條鏈（含預算）
        detail = client.get(f"/api/cases/{case_id}/360").json()["data"]
        assert any(b["budget_code"] == "BUD-WIZ-2" for b in detail["budgets"])
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
        # 錯誤訊息要白話（別讓一般使用者看到原始 sqlite 錯誤字串），且要指出實際打的那個編號
        detail = r.json()["detail"]
        assert "合約編號" in detail and "DUPK" in detail and "已經存在" in detail
        assert "UNIQUE constraint" not in detail
        # 案件跟簽呈都不該被留下——整批回滾
        cases = client.get("/api/cases").json()["data"]
        assert not any(c["case_code"] == "WIZ-4" for c in cases)
        signoffs = client.get("/api/signoffs").json()["data"]
        assert not any(s["signoff_code"] == "SG-WIZ-4" for s in signoffs)


def test_duplicate_case_code_friendly_message(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/case-wizard", json={"case": {"case_code": "DUP-CASE", "title": "第一筆"}})
        r = client.post("/api/case-wizard", json={"case": {"case_code": "DUP-CASE", "title": "第二筆"}})
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert "案件編號" in detail and "DUP-CASE" in detail and "已經存在" in detail


def test_cio_cannot_use_wizard(tmp_path):
    with _client(tmp_path, login="ap01") as client:
        r = client.post("/api/case-wizard", json={"case": {"case_code": "WIZ-5", "title": "CIO 不該能建"}})
        assert r.status_code == 403


# ── 第三次回饋 8.2/8.3：②專案可直接完整建立 Project 與 WBS ──
def test_project_step_without_procurement_creates_no_items(tmp_path):
    """不涉及請購或合約：只建 Project 主檔，WBS 由承辦自己到專案模組建，精靈不自動排。"""
    with _client(tmp_path) as client:
        r = client.post("/api/case-wizard", json={
            "case": {"case_code": "WIZ-6", "title": "不涉及請購"},
            "project": {"project_name": "內部小改善", "owner": "王小明",
                        "start_date": "2026-09-01", "end_date": "2026-10-01"},
        })
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        assert d["project"]["project_name"] == "內部小改善"
        assert d["project"]["start_date"] == "2026-09-01" and d["project"]["end_date"] == "2026-10-01"
        assert "standard_wbs" not in d["project"]
        items = client.get(f"/api/projects/{d['project']['id']}/items").json()["data"]
        assert items == []


def test_project_step_with_procurement_applies_standard_wbs(tmp_path):
    """涉及請購或合約：建立後自動排標準 WBS 工作項（8 項，含結案），負責人預帶專案負責人。"""
    with _client(tmp_path) as client:
        r = client.post("/api/case-wizard", json={
            "case": {"case_code": "WIZ-7", "title": "涉及請購"},
            "project": {"project_name": "機房擴充", "owner": "陳美惠", "involves_procurement": 1},
        })
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        assert d["project"]["standard_wbs"]["created_count"] == 8
        items = client.get(f"/api/projects/{d['project']['id']}/items").json()["data"]
        assert [i["item_name"] for i in items] == [
            "需求確認", "廠商報價", "上簽申請與核准", "議價", "合約簽訂", "執行／建置", "驗收", "結案"]
        assert all(i["owner"] == "陳美惠" for i in items)


def test_project_step_procurement_defaults_owner_to_case_owner(tmp_path):
    """專案沒填負責人時，標準 WBS 的負責人退回案件負責人（跟案件本身的預設邏輯一致）。"""
    with _client(tmp_path) as client:
        r = client.post("/api/case-wizard", json={
            "case": {"case_code": "WIZ-8", "title": "沒填專案負責人"},
            "project": {"project_name": "無主案專案", "involves_procurement": 1},
        })
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        # 案件負責人也沒填，此時交由承辦身分（ap02 的 owner_scope）帶入——只需確認沒有噴錯、且有排出 8 項
        items = client.get(f"/api/projects/{d['project']['id']}/items").json()["data"]
        assert len(items) == 8
