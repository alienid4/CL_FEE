"""全站搜尋依角色收斂：只回「這個角色開得起來」的型別。

CIO 只有「決策總覽」一個模組，搜到案件/合約也點不進去（會導向他看不到的模組），
列出來只是雜訊。承辦的「只看自己的案件」是另一層（store 的 owner scope），
兩層各管各的：這裡管「哪種模組」，那裡管「誰的資料」，本測試兩層都驗。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "searchscope.db")
    from app.main import create_app

    return TestClient(create_app())


def _seed(table, payload):
    from app import store

    return store.insert_row(table, payload)


def _login(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": "T3st!Pass"})
    assert r.status_code == 200, r.text


def _search(client, q):
    return client.get("/api/search", params={"q": q}).json()["data"]


def test_manager_searches_across_modules(tmp_path):
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "SRCH-1", "title": "青埔機房搬遷", "owner": "ap02"})
        _seed("contracts", {"contract_code": "SRCH-K", "contract_name": "青埔機櫃代管"})
        _login(client, "ap02")
        types = {r["type"] for r in _search(client, "青埔")}
        assert types == {"case", "contract"}   # 助理兩種模組都有 → 兩種都搜得到


def test_cio_gets_nothing_because_only_overview(tmp_path):
    """CIO 搜尋回空：他只有決策總覽，案件/合約點下去是死路。"""
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "SRCH-2", "title": "青埔機房搬遷", "owner": "ap02"})
        _seed("contracts", {"contract_code": "SRCH-K2", "contract_name": "青埔機櫃代管"})
        _login(client, "ap01")
        assert _search(client, "青埔") == []


def test_admin_gets_nothing_business_data(tmp_path):
    """系統管理員只有後台模組，不該從搜尋撈業務資料。"""
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "SRCH-3", "title": "青埔機房搬遷", "owner": "ap02"})
        _login(client, "admin")
        assert _search(client, "青埔") == []


def test_handler_search_still_scoped_to_own_cases(tmp_path):
    """承辦搜得到自己的案件，搜不到別人的——模組層放行，資料層仍照 owner 過濾。"""
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "H-MINE", "title": "青埔我的案", "owner": "ap03"})
        _seed("cases", {"case_code": "H-THEIRS", "title": "青埔別人的案", "owner": "ap02"})
        _login(client, "ap03")
        codes = {r["code"] for r in _search(client, "青埔")}
        assert codes == {"H-MINE"}


def test_handler_has_no_io_center_but_keeps_case_modules(tmp_path):
    """承辦沒有匯入中心等模組，但案件/合約/預算這些他有的照樣搜得到。"""
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "H-C", "title": "電費案", "owner": "ap03"})
        _seed("budgets", {"budget_code": "H-B", "category": "電費", "case_id": 1})
        _login(client, "ap03")
        types = {r["type"] for r in _search(client, "電費")}
        assert "case" in types and "budget" in types
