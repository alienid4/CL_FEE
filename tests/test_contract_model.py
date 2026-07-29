"""合約模型補齊：起始日 / 合約類型 / 保固維護到期 / 續約-增購-整併來源。

原本 contracts 只有到期日，沒有起始日、類型，也記不住「這份約是續哪一份」，
主管要回答「這個維護約續幾年了、保固到哪天」只能翻紙本。本測試涵蓋：
  - 新欄位存得進、讀得出、CSV 匯出帶得到
  - 續約/增購/整併：指向來源合約，來源不存在要擋
  - 自己不能是自己的來源、也不能繞成一個圈（否則續約鏈追不完）
  - 續約鏈 lineage 由近而遠列出舊約
  - Case 360 的合約帶得出來源合約編號
"""
import os

import pytest
from fastapi.testclient import TestClient


def _setup(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "ctmodel.db")
    from app.main import create_app

    client = TestClient(create_app())
    client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
    return client


def _contract(client, code, **kw):
    r = client.post("/api/contracts", json={"contract_code": code, "contract_name": kw.pop("name", "合約"), **kw})
    assert r.status_code == 201, r.text
    return r.json()["data"]


def test_new_contract_fields_round_trip(tmp_path):
    with _setup(tmp_path) as client:
        ct = _contract(
            client, "CM-1", name="主機維護約", amount=600_000,
            contract_type="維護", start_date="2026-08-01", end_date="2027-07-31",
            warranty_end_date="2027-10-31", maintenance_end_date="2027-07-31",
        )
        assert ct["start_date"] == "2026-08-01"
        assert ct["contract_type"] == "維護"
        assert ct["warranty_end_date"] == "2027-10-31"      # 保固可以晚於合約到期日
        assert ct["maintenance_end_date"] == "2027-07-31"
        # 改起始日：PATCH 也要吃得下新欄位
        r = client.patch(f"/api/contracts/{ct['id']}", json={"start_date": "2026-09-01"})
        assert r.status_code == 200, r.text
        assert r.json()["data"]["start_date"] == "2026-09-01"


def test_renewal_points_to_previous_contract(tmp_path):
    """續約：新約指向舊約，Case 360 要看得到來源合約編號。"""
    with _setup(tmp_path) as client:
        case = client.post("/api/cases", json={"case_code": "CM-CASE", "title": "維護續約"}).json()["data"]
        client.post(f"/api/cases/{case['id']}/submit")
        client.post("/api/auth/login", json={"username": "ap04", "password": "T3st!Pass"})
        client.post(f"/api/cases/{case['id']}/approve")
        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})

        old = _contract(client, "CM-2025", name="維護約 2025", amount=500_000, case_id=case["id"])
        new = _contract(client, "CM-2026", name="維護約 2026", amount=550_000, case_id=case["id"],
                        parent_contract_id=old["id"], relation_type="renew")
        assert new["parent_contract_id"] == old["id"]
        assert new["relation_type"] == "renew"

        rows = {c["contract_code"]: c for c in client.get(f"/api/cases/{case['id']}/360").json()["data"]["contracts"]}
        assert rows["CM-2026"]["parent_contract_code"] == "CM-2025"  # 追溯鏈標得出「續約自 CM-2025」
        assert rows["CM-2025"]["parent_contract_code"] == ""         # 最早那份沒有來源


def test_lineage_lists_previous_contracts_newest_first(tmp_path):
    """續約鏈：2026 續 2025、2025 續 2024 → 查 2026 拿得到 [2025, 2024]（由近而遠）。"""
    with _setup(tmp_path) as client:
        c24 = _contract(client, "L-2024", amount=100)
        c25 = _contract(client, "L-2025", amount=200, parent_contract_id=c24["id"], relation_type="renew")
        c26 = _contract(client, "L-2026", amount=300, parent_contract_id=c25["id"], relation_type="renew")

        chain = client.get(f"/api/contracts/{c26['id']}/lineage").json()["data"]["lineage"]
        assert [x["contract_code"] for x in chain] == ["L-2025", "L-2024"]
        assert client.get(f"/api/contracts/{c24['id']}/lineage").json()["data"]["lineage"] == []


def test_unknown_parent_contract_rejected(tmp_path):
    """來源合約不存在 → 擋下（避免指到空的舊約，續約鏈斷掉）。"""
    with _setup(tmp_path) as client:
        r = client.post("/api/contracts", json={
            "contract_code": "CM-BAD", "contract_name": "亂指", "parent_contract_id": 99999, "relation_type": "renew"})
        assert r.status_code == 422, r.text
        assert "來源合約" in r.json()["detail"]


def test_contract_cannot_be_its_own_parent(tmp_path):
    """自己不能是自己的來源，否則續約鏈永遠追不完。"""
    with _setup(tmp_path) as client:
        ct = _contract(client, "CM-SELF", amount=100)
        r = client.patch(f"/api/contracts/{ct['id']}", json={"parent_contract_id": ct["id"]})
        assert r.status_code == 422, r.text
        assert "自己" in r.json()["detail"]


def test_contract_parent_cycle_rejected(tmp_path):
    """A 續 B、B 又續 A 這種圈要擋掉。"""
    with _setup(tmp_path) as client:
        a = _contract(client, "CY-A", amount=100)
        b = _contract(client, "CY-B", amount=100, parent_contract_id=a["id"], relation_type="renew")
        r = client.patch(f"/api/contracts/{a['id']}", json={"parent_contract_id": b["id"]})
        assert r.status_code == 422, r.text
        assert "圈" in r.json()["detail"]


def test_relation_type_value_is_validated(tmp_path):
    with _setup(tmp_path) as client:
        ct = _contract(client, "CM-REL", amount=100)
        r = client.patch(f"/api/contracts/{ct['id']}", json={"relation_type": "亂填"})
        assert r.status_code == 422, r.text


def test_contract_type_option_available(tmp_path):
    """合約類型走後台可維護的選項清單（跟預算類別同一套機制）。"""
    with _setup(tmp_path) as client:
        types = client.get("/api/options").json()["data"]["contract_type"]
        assert "維護" in types and "採購" in types


def test_csv_export_includes_new_columns(tmp_path):
    with _setup(tmp_path) as client:
        _contract(client, "CM-CSV", name="匯出用", amount=100, contract_type="租賃",
                  start_date="2026-01-01", warranty_end_date="2027-01-01")
        text = client.get("/api/contracts.csv").text
        assert "合約類型" in text and "起始日" in text and "保固到期" in text
        assert "租賃" in text and "2027-01-01" in text
