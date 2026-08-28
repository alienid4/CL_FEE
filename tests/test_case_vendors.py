"""同一 Case 已填過的廠商，跨模組能查出來當建議選項（助理第三次回饋 §6）。
只回清單供前端當 datalist 建議，不自動決定用哪一筆、也不強制覆寫既有欄位。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "vendors.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_vendor_from_contract_shows_up(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"case_code": "VD-1", "title": "廠商測試"}).json()["data"]
        client.post("/api/contracts", json={
            "contract_code": "VDK-1", "contract_name": "合約", "vendor_name": "中華電信",
            "case_id": case["id"]})
        vendors = client.get(f"/api/cases/{case['id']}/vendors").json()["data"]
        assert vendors == ["中華電信"]


def test_vendors_from_multiple_modules_deduplicated(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"case_code": "VD-2", "title": "多模組廠商"}).json()["data"]
        client.post("/api/contracts", json={
            "contract_code": "VDK-2", "contract_name": "合約", "vendor_name": "中華電信",
            "case_id": case["id"]})
        client.post("/api/purchases", json={
            "purchase_code": "VDP-2", "item_name": "品項", "vendor_name": "中華電信",
            "case_id": case["id"]})
        client.post("/api/purchases", json={
            "purchase_code": "VDP-2b", "item_name": "品項二", "vendor_name": "資拓宏宇",
            "case_id": case["id"]})
        vendors = client.get(f"/api/cases/{case['id']}/vendors").json()["data"]
        assert set(vendors) == {"中華電信", "資拓宏宇"}
        assert len(vendors) == 2  # 中華電信在兩張表都出現，不重複列


def test_no_vendors_yet_returns_empty_list(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"case_code": "VD-3", "title": "還沒有廠商"}).json()["data"]
        assert client.get(f"/api/cases/{case['id']}/vendors").json()["data"] == []


def test_other_case_vendors_not_mixed_in(tmp_path):
    with _client(tmp_path) as client:
        case1 = client.post("/api/cases", json={"case_code": "VD-4A", "title": "案A"}).json()["data"]
        case2 = client.post("/api/cases", json={"case_code": "VD-4B", "title": "案B"}).json()["data"]
        client.post("/api/contracts", json={
            "contract_code": "VDK-4", "contract_name": "合約", "vendor_name": "只屬於案A",
            "case_id": case1["id"]})
        assert client.get(f"/api/cases/{case2['id']}/vendors").json()["data"] == []


def test_全域廠商清單含名稱歸納正規名且去重(tmp_path):
    """使用者 2026-08-28：廠商自由輸入導致同一家被打成多種寫法，「廠商別合約金額」報表會被
    拆開而且看不出來。新案申請當下沒有 case_id，只給「同案廠商」等於清單是空的，所以要有全域清單。"""
    with _client(tmp_path) as client:
        c = client.post("/api/cases", json={"title": "廠商清單測試案"}).json()["data"]
        client.post("/api/contracts", json={"contract_name": "約一", "vendor_name": "台灣IBM", "case_id": c["id"]})
        client.post("/api/contracts", json={"contract_name": "約二", "vendor_name": "台灣IBM"})   # 同名只出現一次
        client.post("/api/projects", json={"project_name": "專案一", "vendor_name": "神坊資訊"})

        vendors = client.get("/api/vendors").json()["data"]
        assert vendors.count("台灣IBM") == 1          # 去重
        assert "神坊資訊" in vendors                   # 跨模組都收
        assert all(v.strip() for v in vendors)         # 不會混進空字串


def test_全域廠商清單在沒有任何資料時回空陣列(tmp_path):
    with _client(tmp_path) as client:
        assert client.get("/api/vendors").json()["data"] == []
