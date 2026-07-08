"""八大功能補齊：預算/專案/簽呈/請購 的 CRUD、狀態驗證、需登入。"""
import os

import pytest
from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "modules.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


MODULES = [
    ("/api/budgets", {"budget_code": "B-1", "category": "基礎建設", "unit_name": "資訊架構組", "fiscal_year": "2026", "amount": 26742000}, "budget_code", "nope"),
    ("/api/projects", {"project_code": "P-1", "project_name": "資料庫EOS案", "source": "資料架構組", "necessity": "必要", "progress": 29, "owner": "吳承翰"}, "project_code", "bogus"),
    ("/api/signoffs", {"signoff_code": "S-1", "subject": "設備採購簽呈", "applicant": "雅宋", "amount": 1200000}, "signoff_code", "bogus"),
    ("/api/purchases", {"purchase_code": "PR-1", "item_name": "IPS設備", "vendor_name": "廠商甲", "quantity": 2, "amount": 950000}, "purchase_code", "bogus"),
]


@pytest.mark.parametrize("path,payload,code_field,bad_status", MODULES)
def test_module_crud(tmp_path, path, payload, code_field, bad_status):
    with _client(tmp_path) as client:
        created = client.post(path, json=payload)
        assert created.status_code == 201, created.text
        row = created.json()["data"]
        assert row[code_field] == payload[code_field]

        listed = client.get(path).json()["data"]
        assert any(r[code_field] == payload[code_field] for r in listed)

        rid = row["id"]
        assert client.patch(f"{path}/{rid}", json={"note": "改一下"}).status_code == 200
        assert client.get(path).json()["data"][0]["note"] == "改一下"

        # 非法狀態被擋
        assert client.post(path, json={**payload, code_field: "X-BAD", "status": bad_status}).status_code == 422

        # 停用 + 刪除
        assert client.post(f"{path}/{rid}/disable").status_code == 200
        assert client.delete(f"{path}/{rid}").status_code == 204


@pytest.mark.parametrize("path,payload,code_field,bad_status", MODULES)
def test_module_requires_login(tmp_path, path, payload, code_field, bad_status):
    with _client(tmp_path, login=None) as client:
        assert client.get(path).status_code == 401
        assert client.post(path, json=payload).status_code == 401


def test_case_link_optional_and_settable(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"case_code": "LINK-1", "title": "關聯案"}).json()["data"]
        b = client.post("/api/budgets", json={"budget_code": "B-LINK", "amount": 100, "case_id": case["id"]}).json()["data"]
        assert b["case_id"] == case["id"]


def test_projects_purchases_signoffs_scoped_for_handler(tmp_path):
    """專案/請購/簽呈依案件歸屬隔離：承辦只看自己案件下的；預算不隔離。"""
    with _client(tmp_path, login=None) as client:
        from app import store
        mine = store.insert_row("cases", {"case_code": "SC-MINE", "title": "m", "owner": "ap03"})
        theirs = store.insert_row("cases", {"case_code": "SC-THEIRS", "title": "t", "owner": "ap02"})
        for tbl, code_f, code in [("projects", "project_code", "PJ"), ("purchases", "purchase_code", "PO"), ("signoffs", "signoff_code", "SG")]:
            store.insert_row(tbl, {code_f: f"{code}-MINE", **({"project_name": "n"} if tbl == "projects" else {"subject": "s"} if tbl == "signoffs" else {"item_name": "i"}), "case_id": mine["id"]})
            store.insert_row(tbl, {code_f: f"{code}-THEIRS", **({"project_name": "n"} if tbl == "projects" else {"subject": "s"} if tbl == "signoffs" else {"item_name": "i"}), "case_id": theirs["id"]})
        store.insert_row("budgets", {"budget_code": "BUD-ORG"})  # 全公司預算

        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        pj = [r["project_code"] for r in client.get("/api/projects").json()["data"]]
        assert "PJ-MINE" in pj and "PJ-THEIRS" not in pj
        po = [r["purchase_code"] for r in client.get("/api/purchases").json()["data"]]
        assert "PO-MINE" in po and "PO-THEIRS" not in po
        sg = [r["signoff_code"] for r in client.get("/api/signoffs").json()["data"]]
        assert "SG-MINE" in sg and "SG-THEIRS" not in sg
        bud = [r["budget_code"] for r in client.get("/api/budgets").json()["data"]]
        assert "BUD-ORG" in bud  # 預算不隔離，承辦也看得到


def test_fk_existence_checked(tmp_path):
    """關聯 ID 不存在要被擋（避免付款掛到不存在的合約、資料掛到不存在的案件）。"""
    with _client(tmp_path) as client:
        assert client.post("/api/payments", json={"contract_id": 9999, "payment_month": "2026-09", "payment_amount": 100}).status_code == 422
        assert client.post("/api/budgets", json={"budget_code": "B-BADFK", "case_id": 9999}).status_code == 422
        # 存在就通過
        ct = client.post("/api/contracts", json={"contract_code": "OK-CT", "contract_name": "c"}).json()["data"]
        assert client.post("/api/payments", json={"contract_id": ct["id"], "payment_month": "2026-09", "payment_amount": 100}).status_code == 201


def test_payment_project_real_fields_roundtrip(tmp_path):
    """對齊真實 Excel 欄位：付款/專案的新欄位能存、能讀、能匯出。"""
    with _client(tmp_path) as client:
        ct = client.post("/api/contracts", json={"contract_code": "K-F", "contract_name": "c"}).json()["data"]
        pay = client.post("/api/payments", json={
            "contract_id": ct["id"], "payment_month": "2026-06", "payment_amount": 479848,
            "item": "APT防護系統 第1期", "settle_no": "CS460038", "ref_no": "WU82483858",
            "vendor": "中菲電腦", "period": "第1期", "billing_period": "115/6/1-115/6/30",
            "net_amount": 456998, "tax_amount": 22850, "approval_level": "處長",
            "settled_by": "蔡維庭", "owner": "黃小姐", "owner_email": "yun@cathaysec.com.tw",
        }).json()["data"]
        assert pay["item"] == "APT防護系統 第1期" and pay["net_amount"] == 456998 and pay["tax_amount"] == 22850
        assert pay["vendor"] == "中菲電腦" and pay["settle_no"] == "CS460038"
        # CSV 匯出含新欄位（Excel out）
        csv = client.get("/api/payments.csv").text
        assert "核銷項目" in csv and "未稅金額" in csv and "營業稅" in csv and "中菲電腦" in csv

        proj = client.post("/api/projects", json={
            "project_code": "P-F", "project_name": "資料庫EOS案", "necessity": "必要",
            "level": "處級", "progress_planned": 30, "progress": 29, "rag_status": "如期執行",
            "start_date": "2026-03-01", "end_date": "2026-09-30",
        }).json()["data"]
        assert proj["level"] == "處級" and proj["progress_planned"] == 30 and proj["rag_status"] == "如期執行"
        # 起訖日必須能存能讀（供進度總表算落後；曾因 Pydantic 未列欄位被吞掉）
        assert proj["start_date"] == "2026-03-01" and proj["end_date"] == "2026-09-30"
        patched = client.patch(f"/api/projects/{proj['id']}", json={"end_date": "2026-10-31"}).json()["data"]
        assert patched["end_date"] == "2026-10-31" and patched["start_date"] == "2026-03-01"
        pcsv = client.get("/api/projects.csv").text
        assert "專案分類" in pcsv and "進度預計%" in pcsv and "燈號" in pcsv
        assert "開始日" in pcsv and "結束日" in pcsv


def test_options_include_project_level_and_rag(tmp_path):
    with _client(tmp_path) as client:
        o = client.get("/api/options").json()["data"]
        assert "公司級" in o["project_level"] and "如期執行" in o["project_rag"]
        assert "非必要" in o["project_necessity"]


def test_search_covers_new_modules(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/budgets", json={"budget_code": "SRCH-BUD", "category": "找找"})
        client.post("/api/signoffs", json={"signoff_code": "SRCH-SGN", "subject": "找找"})
        client.post("/api/purchases", json={"purchase_code": "SRCH-PO", "item_name": "找找"})
        client.post("/api/projects", json={"project_code": "SRCH-PRJ", "project_name": "找找"})
        codes = {r["code"] for r in client.get("/api/search", params={"q": "SRCH"}).json()["data"]}
        assert {"SRCH-BUD", "SRCH-SGN", "SRCH-PO", "SRCH-PRJ"} <= codes


def test_search_finds_project_by_owner(tmp_path):
    """全文搜尋要搜得到負責人（先前只搜編號/名稱/來源，搜人名找不到）。"""
    with _client(tmp_path) as client:
        client.post("/api/projects", json={"project_code": "OWN-1", "project_name": "資產治理", "owner": "吳承恩"})
        codes = {r["code"] for r in client.get("/api/search", params={"q": "吳承恩"}).json()["data"]}
        assert "OWN-1" in codes
