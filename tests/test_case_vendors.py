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
