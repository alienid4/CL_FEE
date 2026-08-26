"""第四輪回饋 AC-01：不得建立無 Case 歸屬的子模組資料。
沿用既有 budgets/projects 的「案件自動生成」做法（使用者拍板：不強迫先選案件，
系統自己用這筆的名稱配一個同名案件）延伸到 contracts/purchases/expense_masters，
不新增一道強制選案件的關卡、也不允許真正的孤兒資料。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "auto_case.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_contract_without_case_id_gets_auto_case(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/contracts", json={"contract_code": "AC-K1", "contract_name": "自動配案合約"})
        assert r.status_code == 201, r.text
        d = r.json()["data"]
        assert d["case_id"] is not None
        case = client.get("/api/cases").json()["data"]
        assert any(c["id"] == d["case_id"] and c["title"] == "自動配案合約" for c in case)


def test_purchase_without_case_id_gets_auto_case(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/purchases", json={"purchase_code": "AC-P1", "item_name": "自動配案費用"})
        assert r.status_code == 201, r.text
        assert r.json()["data"]["case_id"] is not None


def test_expense_master_without_case_id_gets_auto_case(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/expenses", json={
            "expense_name": "自動配案費用主檔", "total_amount": 1000, "modes": "periodic",
            "signoff_none_reason": "測試用，無簽呈"})
        assert r.status_code == 201, r.text
        assert r.json()["data"]["case_id"] is not None


def test_explicit_case_id_is_respected_not_overridden(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"case_code": "AC-C1", "title": "既有案件"}).json()["data"]
        r = client.post("/api/contracts", json={
            "contract_code": "AC-K2", "contract_name": "掛既有案件", "case_id": case["id"]})
        assert r.json()["data"]["case_id"] == case["id"]
        # 沒有多生出一個同名案件
        cases = client.get("/api/cases").json()["data"]
        assert sum(1 for c in cases if c["title"] == "既有案件") == 1


def test_two_contracts_with_same_name_share_one_auto_case(tmp_path):
    """名稱完全相同才視為同一案（不做模糊比對），同名兩筆掛同一個自動配案，不是各生一個。"""
    with _client(tmp_path) as client:
        r1 = client.post("/api/contracts", json={"contract_code": "AC-K3", "contract_name": "重複名稱案"})
        r2 = client.post("/api/purchases", json={"purchase_code": "AC-P3", "item_name": "重複名稱案"})
        assert r1.json()["data"]["case_id"] == r2.json()["data"]["case_id"]
