"""全生命週期整合測試：規劃專案 → 預算 → 案件(複核) → 簽呈 → 請購 → 合約 →
付款 → 文件 → CIO 下探整條控管鏈。扮演 主管(ap02)/承辦(ap03)/助理B(ap04)。"""
import os
from datetime import date

from fastapi.testclient import TestClient


def _nm():
    t = date.today()
    return f"{t.year + 1}-01" if t.month == 12 else f"{t.year}-{t.month + 1:02d}"


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "lifecycle.db")
    from app.main import create_app

    return TestClient(create_app())


def _login(c, u):
    assert c.post("/api/auth/login", json={"username": u, "password": "T3st!Pass"}).status_code == 200


def test_full_lifecycle_plan_to_payment(tmp_path):
    with _client(tmp_path) as c:
        def D(r):
            assert r.status_code in (200, 201), r.text
            return r.json()["data"]

        # 1) 主管規劃專案 + 編列預算
        _login(c, "ap02")
        proj = D(c.post("/api/projects", json={"project_code": "PRJ-1", "project_name": "內湖機房擴充", "source": "網路組", "necessity": "必要", "progress": 10, "owner": "ap03"}))
        bud = D(c.post("/api/budgets", json={"budget_code": "BUD-1", "category": "基礎建設", "unit_name": "資訊架構組", "fiscal_year": "2026", "amount": 5000000}))

        # 2) 承辦建立案件（草稿 + 預計完成日）
        _login(c, "ap03")
        case = D(c.post("/api/cases", json={"case_code": "CASE-1", "title": "機房網路擴充採購", "owner": "ap03", "amount": 4800000, "due_date": "2026-06-30"}))
        cid = case["id"]
        assert case["status"] == "draft" and case["created_by"] == "ap03"

        # 3) 專案/預算回頭關聯到案件
        _login(c, "ap02")
        D(c.patch(f"/api/projects/{proj['id']}", json={"case_id": cid}))
        D(c.patch(f"/api/budgets/{bud['id']}", json={"case_id": cid}))

        # 4) 承辦送出複核 → 5) 助理B 核准（≠ 建立者）
        _login(c, "ap03")
        assert D(c.post(f"/api/cases/{cid}/submit"))["status"] == "pending_review"
        _login(c, "ap04")
        assert D(c.post(f"/api/cases/{cid}/approve"))["status"] == "approved"

        # 6~10) 簽呈 / 請購 / 合約 / 付款 / 文件（皆關聯案件）
        _login(c, "ap02")
        D(c.post("/api/signoffs", json={"signoff_code": "SGN-1", "subject": "採購簽呈", "applicant": "ap03", "amount": 4800000, "case_id": cid, "status": "approved"}))
        D(c.post("/api/purchases", json={"purchase_code": "PO-1", "item_name": "核心交換器", "vendor_name": "廠商甲", "quantity": 2, "amount": 4800000, "case_id": cid, "status": "ordered"}))
        contract = D(c.post("/api/contracts", json={"contract_code": "CT-1", "contract_name": "建置契約", "vendor_name": "廠商甲", "amount": 4800000, "case_id": cid, "end_date": "2026-12-31"}))
        D(c.post("/api/payments", json={"contract_id": contract["id"], "payment_month": _nm(), "payment_amount": 2400000, "status": "pending"}))
        D(c.post("/api/documents", json={"file_name": "驗收單.pdf", "document_type": "approval", "case_id": cid, "contract_id": contract["id"]}))

        # 11) CIO 下探：整條控管鏈都看得到
        _login(c, "ap01")
        d = c.get(f"/api/cases/{cid}/360").json()["data"]
        assert d["budgets"] and d["projects"] and d["signoffs"] and d["purchases"]
        assert d["contracts"] and d["payments"] and d["documents"]

        # 12) CIO 決策總覽：下月應付含這筆已核准案件的付款
        ov = c.get("/api/reports/cio-overview").json()["data"]
        assert ov["next_month_total"] == 2400000
        assert any(x["case_code"] == "CASE-1" for x in ov["upcoming_next_month"])

        # 13) 已核准（完成）案件不再催辦
        rem = c.get("/api/reports/reminders").json()["data"]
        assert all(i["code"] != "CASE-1" for i in rem)


def test_lifecycle_entry_from_signoff_no_budget(tmp_path):
    """有些流程不從預算起：從簽呈起，下探有簽呈、無預算，仍正常。"""
    with _client(tmp_path) as c:
        _login(c, "ap02")
        case = c.post("/api/cases", json={"case_code": "S-CASE", "title": "從簽呈起"}).json()["data"]
        c.post("/api/signoffs", json={"signoff_code": "S-SGN", "subject": "先簽呈", "amount": 100, "case_id": case["id"]})
        d = c.get(f"/api/cases/{case['id']}/360").json()["data"]
        assert len(d["signoffs"]) == 1 and len(d["budgets"]) == 0
