"""新案申請改版（助理回饋 2026-07-29）。

申請表單從六步砍成四步：① 案件（必填）② 專案 ③ 合約 ④ 費用；預算/簽呈/付款移出。
案件欄位換成：組別、負責人、預算內/外、費用or資本支出、預算名目、案件來源、案件說明。
案件編號改由系統產生（承辦不必填），金額保留人工填（使用者拍板，與助理刪除清單不同）。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "apply.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_案件編號留空由系統產生(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/cases", json={"title": "沒填編號的案"})
        assert r.status_code == 201, r.text
        c = r.json()["data"]
        assert c["case_code"].startswith("TMP")           # 系統配的暫時號
        assert c["case_code"].endswith(f"{c['temp_seq']:04d}")
        assert c["seq"] == 0                              # 正式號要等核准
        # 主管 2026-08-03 交代：系統配的號只能是英數，不得含 - _ 與中文
        from app.store import is_system_code_valid
        assert is_system_code_valid(c["case_code"]), c["case_code"]


def test_自己填的案件編號仍然沿用(tmp_path):
    """匯入既有資料時會帶真編號，不能被系統號蓋掉。"""
    with _client(tmp_path) as client:
        c = client.post("/api/cases", json={"case_code": "REAL-001", "title": "有編號"}).json()["data"]
        assert c["case_code"] == "REAL-001"


def test_案件申請欄位存得進讀得出(tmp_path):
    with _client(tmp_path) as client:
        c = client.post("/api/cases", json={
            "title": "APT 防護採購", "group_name": "資安組", "owner": "王志明",
            "budget_type": "in_budget", "expense_kind": "capex", "budget_item": "B-2026-001",
            "source": "資安或稽核追蹤", "description": "汰換既有防護系統", "amount": 2_635_840,
        }).json()["data"]
        assert c["group_name"] == "資安組"
        assert c["budget_type"] == "in_budget"
        assert c["expense_kind"] == "capex"
        assert c["budget_item"] == "B-2026-001"
        assert c["source"] == "資安或稽核追蹤"
        assert c["description"] == "汰換既有防護系統"
        assert c["amount"] == 2_635_840        # 金額保留人工填（使用者拍板）


def test_預算內外與費用性質只收合法值(tmp_path):
    with _client(tmp_path) as client:
        c = client.post("/api/cases", json={"title": "驗證用"}).json()["data"]
        assert client.patch(f"/api/cases/{c['id']}", json={"budget_type": "亂填"}).status_code == 422
        assert client.patch(f"/api/cases/{c['id']}", json={"expense_kind": "亂填"}).status_code == 422
        assert client.patch(f"/api/cases/{c['id']}", json={"budget_type": "out_budget"}).status_code == 200


def test_新案申請四步一次送出(tmp_path):
    """案件＋專案＋合約＋費用一次建立，全部掛上新案。"""
    with _client(tmp_path) as client:
        r = client.post("/api/case-wizard", json={
            "case": {"title": "機房冷氣汰換", "group_name": "主機組", "owner": "陳怡君",
                     "budget_type": "out_budget", "expense_kind": "expense",
                     "budget_item": "臨時維修", "source": "主管關注",
                     "description": "冷氣老舊需汰換", "amount": 800_000},
            "project": {"project_name": "機房冷氣汰換專案", "level": "部級",
                        "vendor_name": "某冷氣行", "cross_company": "否"},
            "contract": {"contract_code": "W-K1", "contract_name": "冷氣汰換合約", "amount": 600_000},
            "purchase": {"purchase_code": "W-E1", "item_name": "臨時維修費", "amount": 200_000},
        })
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        case_id = d["case"]["id"]
        assert d["project"]["case_id"] == case_id
        assert d["contract"]["case_id"] == case_id
        assert d["purchase"]["case_id"] == case_id
        assert d["project"]["owner"] == "陳怡君"      # 專案負責人預設沿用案件負責人
        assert d["project"]["cross_company"] == "否"
        assert d["budget"] is None and d["signoff"] is None and d["payment"] is None


def test_專案負責人可自行指定不被案件蓋掉(tmp_path):
    with _client(tmp_path) as client:
        d = client.post("/api/case-wizard", json={
            "case": {"title": "案", "owner": "王志明"},
            "project": {"project_name": "專案", "owner": "林建宏"},
        }).json()["data"]
        assert d["project"]["owner"] == "林建宏"


def test_申請失敗整批回滾(tmp_path):
    """合約編號撞號 → 案件與專案都不留下（單一交易）。"""
    with _client(tmp_path) as client:
        client.post("/api/contracts", json={"contract_code": "DUP-K", "contract_name": "先存在的"})
        before = len(client.get("/api/cases").json()["data"])
        r = client.post("/api/case-wizard", json={
            "case": {"title": "會失敗的案"},
            "project": {"project_name": "不該留下的專案"},
            "contract": {"contract_code": "DUP-K", "contract_name": "撞號"},
        })
        assert r.status_code == 422, r.text
        assert len(client.get("/api/cases").json()["data"]) == before
        assert "不該留下的專案" not in [p["project_name"] for p in client.get("/api/projects").json()["data"]]


def test_專案帶跨子公司與廠商欄位(tmp_path):
    """需求書 §6：專案主檔要有廠商與「是否跨子公司合作」（金控合作案是主管關注條件）。"""
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={
            "project_code": "P-X", "project_name": "集團聯合採購",
            "vendor_name": "中華電信", "cross_company": "是"}).json()["data"]
        assert p["vendor_name"] == "中華電信" and p["cross_company"] == "是"
