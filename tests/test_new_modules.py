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
    """請購/簽呈依案件歸屬隔離：承辦只看自己案件下的；專案依「負責人」欄位隔離
    （單一負責人只有那人看得到，「/」列多個共同負責人時名字有列到的都看得到）；
    預算不隔離（全公司共享）。"""
    with _client(tmp_path, login=None) as client:
        from app import store
        mine = store.insert_row("cases", {"case_code": "SC-MINE", "title": "m", "owner": "ap03"})
        theirs = store.insert_row("cases", {"case_code": "SC-THEIRS", "title": "t", "owner": "ap02"})
        for tbl, code_f, code in [("purchases", "purchase_code", "PO"), ("signoffs", "signoff_code", "SG")]:
            store.insert_row(tbl, {code_f: f"{code}-MINE", **({"subject": "s"} if tbl == "signoffs" else {"item_name": "i"}), "case_id": mine["id"]})
            store.insert_row(tbl, {code_f: f"{code}-THEIRS", **({"subject": "s"} if tbl == "signoffs" else {"item_name": "i"}), "case_id": theirs["id"]})
        # 專案不靠 case_id 隔離，靠「負責人」欄位：ap03 顯示名稱是「承辦」
        store.insert_row("projects", {"project_code": "PJ-MINE", "project_name": "n", "owner": "承辦"})
        store.insert_row("projects", {"project_code": "PJ-SHARED", "project_name": "n", "owner": "承辦/別人"})  # 共同負責人也看得到
        store.insert_row("projects", {"project_code": "PJ-THEIRS", "project_name": "n", "owner": "別人"})
        store.insert_row("projects", {"project_code": "PJ-NOOWNER", "project_name": "n"})  # 沒填負責人：誰都看不到
        store.insert_row("budgets", {"budget_code": "BUD-ORG"})  # 全公司預算

        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        pj = [r["project_code"] for r in client.get("/api/projects").json()["data"]]
        assert "PJ-MINE" in pj and "PJ-SHARED" in pj
        assert "PJ-THEIRS" not in pj and "PJ-NOOWNER" not in pj
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
            "item": "測試防護系統 第1期", "settle_no": "TEST-460038", "ref_no": "TEST-82483858",
            "vendor": "測試廠商甲", "period": "第1期", "billing_period": "115/6/1-115/6/30",
            "net_amount": 456998, "tax_amount": 22850, "approval_level": "處長",
            "settled_by": "郭靖", "owner": "黃蓉", "owner_email": "test@example.com",
        }).json()["data"]
        assert pay["item"] == "測試防護系統 第1期" and pay["net_amount"] == 456998 and pay["tax_amount"] == 22850
        assert pay["vendor"] == "測試廠商甲" and pay["settle_no"] == "TEST-460038"
        # CSV 匯出含新欄位（Excel out）
        csv = client.get("/api/payments.csv").text
        assert "核銷項目" in csv and "未稅金額" in csv and "營業稅" in csv and "測試廠商甲" in csv

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


def test_search_as_handler_with_matched_display_name_does_not_500(tmp_path):
    """曾經的真bug：承辦(有對應到帳號的顯示名稱)搜尋時，projects的owner-scoping SQL
    LEFT JOIN cases後兩表都有owner欄，沒加表別名前綴會被SQLite判為ambiguous column
    name直接500。用有唯一對應帳號的承辦(ap03顯示名稱「承辦」)搜尋觸發scope filter驗證修好。"""
    with _client(tmp_path) as client:
        from app import store
        store.insert_row("projects", {"project_code": "SCOPE-SEARCH", "project_name": "找我沒問題", "owner": "承辦"})
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        resp = client.get("/api/search", params={"q": "找我沒問題"})
        assert resp.status_code == 200, resp.text
        codes = {r["code"] for r in resp.json()["data"]}
        assert "SCOPE-SEARCH" in codes


def test_budget_without_case_auto_creates_case(tmp_path):
    """使用者拍板：不需要先手動建案件，建預算沒指定案件就自動生一個同名案件掛上。"""
    with _client(tmp_path) as client:
        b = client.post("/api/budgets", json={"budget_code": "X Server維護案", "amount": 2000000}).json()["data"]
        assert b["case_id"] is not None
        case = client.get("/api/cases").json()["data"]
        auto = [c for c in case if c["id"] == b["case_id"]][0]
        assert auto["title"] == "X Server維護案"


def test_project_same_name_reuses_auto_created_case(tmp_path):
    """同名的預算跟專案要合流到同一個自動案件，不是各自生出兩個案件。"""
    with _client(tmp_path) as client:
        b = client.post("/api/budgets", json={"budget_code": "X Server維護案", "amount": 2000000}).json()["data"]
        p = client.post("/api/projects", json={"project_code": "PJ-X", "project_name": "X Server維護案"}).json()["data"]
        assert p["case_id"] == b["case_id"]


def test_budget_with_explicit_case_id_not_overridden(tmp_path):
    """有明確指定案件時不要被自動生成蓋掉。"""
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"case_code": "MANUAL-1", "title": "手動案"}).json()["data"]
        b = client.post("/api/budgets", json={"budget_code": "有指定案件的預算", "case_id": case["id"]}).json()["data"]
        assert b["case_id"] == case["id"]


def test_project_import_without_case_auto_creates_case(tmp_path):
    """匯入路徑（commit_projects_import）也要吃到自動建案規則。"""
    with _client(tmp_path) as client:
        from app import store
        result = store.commit_projects_import([
            {"project_code": "IMP-PJ-1", "project_name": "匯入自動建案專案", "source": "測試組"},
        ])
        assert result["created_count"] == 1
        rows = client.get("/api/projects").json()["data"]
        row = [r for r in rows if r["project_code"] == "IMP-PJ-1"][0]
        assert row["case_id"] is not None
        cases = client.get("/api/cases").json()["data"]
        assert any(c["id"] == row["case_id"] and c["title"] == "匯入自動建案專案" for c in cases)


def test_budget_import_without_case_auto_creates_case(tmp_path):
    """匯入路徑（commit_budgets_import）也要吃到自動建案規則。"""
    with _client(tmp_path) as client:
        from app import store
        result = store.commit_budgets_import([
            {"budget_code": "匯入自動建案預算", "amount": 100},
        ])
        assert result["created_count"] == 1
        rows = client.get("/api/budgets").json()["data"]
        row = [r for r in rows if r["budget_code"] == "匯入自動建案預算"][0]
        assert row["case_id"] is not None
        cases = client.get("/api/cases").json()["data"]
        assert any(c["id"] == row["case_id"] and c["title"] == "匯入自動建案預算" for c in cases)


def test_backfill_case_links_for_existing_orphan_data(tmp_path):
    """使用者拍板：舊有（v0.9.92 之前匯入的）沒掛案件的預算/專案，也要能批次回填，不是只套新資料。"""
    with _client(tmp_path) as client:
        from app import store
        # 模擬舊資料：直接用 store.insert_row 繞過（v0.9.92 之後這條路徑本身就會自動掛，
        # 這裡刻意在插入後把 case_id 清掉，模擬「v0.9.92 上線前就存在」的孤兒資料）
        b = store.insert_row("budgets", {"budget_code": "舊孤兒預算"})
        p = store.insert_row("projects", {"project_code": "OLD-PJ", "project_name": "舊孤兒專案"})
        with store.connect() as conn:
            conn.execute("UPDATE budgets SET case_id = NULL WHERE id = ?", (b["id"],))
            conn.execute("UPDATE projects SET case_id = NULL WHERE id = ?", (p["id"],))

        status_before = client.get("/api/dev-console/backfill/status").json()["data"]
        assert status_before["case_link_missing"] >= 2

        result = client.post("/api/dev-console/backfill/run").json()["data"]
        assert result["case_links_filled"] >= 2

        budget_after = [r for r in client.get("/api/budgets").json()["data"] if r["id"] == b["id"]][0]
        project_after = [r for r in client.get("/api/projects").json()["data"] if r["id"] == p["id"]][0]
        assert budget_after["case_id"] is not None
        assert project_after["case_id"] is not None

        status_after = client.get("/api/dev-console/backfill/status").json()["data"]
        assert status_after["case_link_missing"] == 0


def test_project_owner_matched_to_account_auto_assigns_case_owner(tmp_path):
    """方案A：專案負責人若能唯一比對到一個登入帳號，自動生成的案件直接掛該帳號為負責人。"""
    with _client(tmp_path) as client:
        from app import store
        store.create_db_user("ap10", "handler", "黃蓉", "", "x")
        p = client.post("/api/projects", json={
            "project_code": "PJ-OWNER", "project_name": "EDR新專案環境建置", "owner": "令狐沖/黃蓉",
        }).json()["data"]
        case = [c for c in client.get("/api/cases").json()["data"] if c["id"] == p["case_id"]][0]
        assert case["owner"] == "ap10"


def test_project_owner_no_unique_match_leaves_case_owner_blank(tmp_path):
    """比對不到帳號、或名字對不到任何登入帳號時，不瞎猜，案件負責人留白。"""
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={
            "project_code": "PJ-NOMATCH", "project_name": "無人對應的專案", "owner": "查無此人",
        }).json()["data"]
        case = [c for c in client.get("/api/cases").json()["data"] if c["id"] == p["case_id"]][0]
        assert not case["owner"]


def test_backfill_patches_owner_for_existing_orphan_owner_case(tmp_path):
    """既有（早於本次功能）已自動建好但負責人空白的案件，只要掛的專案負責人現在能唯一比對到帳號，回填要一併補上。"""
    with _client(tmp_path) as client:
        from app import store
        # 模擬 v0.9.93 之前跑過的回填：案件已建好、掛上專案，但沒有負責人（v0.9.94 之前不會比對負責人）
        case = store.insert_row("cases", {"case_code": "EDR-OLD", "title": "EDR新專案環境建置"})
        store.insert_row("projects", {
            "project_code": "OLD-EDR-PJ", "project_name": "EDR新專案環境建置",
            "owner": "令狐沖/黃蓉", "case_id": case["id"],
        })
        store.create_db_user("ap10", "handler", "黃蓉", "", "x")

        result = client.post("/api/dev-console/backfill/run").json()["data"]
        assert result is not None

        case_after = [c for c in client.get("/api/cases").json()["data"] if c["id"] == case["id"]][0]
        assert case_after["owner"] == "ap10"
