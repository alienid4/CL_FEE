"""單位管理 Step 2：合併／分開／解除，及對撞名清單與單位彙總的影響。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "unitmerge.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _seed(tmp_path):
    """1152：法二處(預算600) vs 法人業務二處(人數) 同單位；1014：永和(300) vs 信義(500) 不同單位。"""
    from app import store

    with store.connect() as conn:
        conn.execute("INSERT INTO unit_headcounts (unit_code,unit_name,headcount) VALUES ('1152','法人業務二處',3)")
        conn.execute("INSERT INTO budgets (budget_code,amount) VALUES ('B1',1000)")
        b1 = conn.execute("SELECT id FROM budgets WHERE budget_code='B1'").fetchone()["id"]
        conn.execute("INSERT INTO budget_allocations (budget_id,seq,unit_code,unit_name,amount) VALUES (?,1,'1152','法二處',600)", (b1,))
        conn.execute("INSERT INTO budget_allocations (budget_id,seq,unit_code,unit_name,amount) VALUES (?,2,'1014','永和分公司',300)", (b1,))
        conn.execute("INSERT INTO budgets (budget_code,amount) VALUES ('B2',500)")
        b2 = conn.execute("SELECT id FROM budgets WHERE budget_code='B2'").fetchone()["id"]
        conn.execute("INSERT INTO budget_allocations (budget_id,seq,unit_code,unit_name,amount) VALUES (?,1,'1014','信義分公司',500)", (b2,))


def test_merge_clears_conflict_and_sums_rollup(tmp_path):
    with _client(tmp_path) as client:
        _seed(tmp_path)
        before = client.get("/api/unit-conflicts").json()["data"]["summary"]
        assert before["code_conflicts"] == 2

        # 合併 1152：以「法人業務二處」為準
        r = client.post("/api/unit-merge", json={
            "variants": [{"unit_code": "1152", "unit_name": "法二處"}, {"unit_code": "1152", "unit_name": "法人業務二處"}],
            "canonical_code": "1152", "canonical_name": "法人業務二處"})
        assert r.status_code == 200 and r.json()["data"]["merged"] == 2

        after = client.get("/api/unit-conflicts").json()["data"]["summary"]
        assert after["code_conflicts"] == 1  # 只剩 1014
        assert after["resolved_groups"] == 1

        units = {u["unit_name"]: u for u in client.get("/api/budget-units").json()["data"]["units"]}
        assert "法二處" not in units  # 已認到主單位
        assert units["法人業務二處"]["total_amount"] == 600


def test_split_keeps_units_separate_and_resolves(tmp_path):
    with _client(tmp_path) as client:
        _seed(tmp_path)
        client.post("/api/unit-split", json={
            "variants": [{"unit_code": "1014", "unit_name": "永和分公司"}, {"unit_code": "1014", "unit_name": "信義分公司"}]})
        # 1014 不再是待確認（已裁決），且兩者分開加總
        conf = client.get("/api/unit-conflicts").json()["data"]
        assert all(c["unit_code"] != "1014" for c in conf["code_conflicts"])
        units = {u["unit_name"]: u for u in client.get("/api/budget-units").json()["data"]["units"]}
        assert units["永和分公司"]["total_amount"] == 300
        assert units["信義分公司"]["total_amount"] == 500


def test_unlink_restores_conflict(tmp_path):
    with _client(tmp_path) as client:
        _seed(tmp_path)
        client.post("/api/unit-merge", json={
            "variants": [{"unit_code": "1152", "unit_name": "法二處"}, {"unit_code": "1152", "unit_name": "法人業務二處"}],
            "canonical_code": "1152", "canonical_name": "法人業務二處"})
        master = client.get("/api/unit-master").json()["data"]["masters"]
        alias_id = master[0]["aliases"][0]["id"]
        client.post(f"/api/unit-alias/{alias_id}/unlink")
        # 解除一個別名後，1152 又變回待確認（因為有變體未裁決）
        conf = client.get("/api/unit-conflicts").json()["data"]
        assert any(c["unit_code"] == "1152" for c in conf["code_conflicts"])


def test_merge_blocked_for_handler(tmp_path):
    with _client(tmp_path, login="ap03") as client:
        r = client.post("/api/unit-merge", json={
            "variants": [{"unit_code": "1", "unit_name": "A"}], "canonical_code": "1", "canonical_name": "A"})
        assert r.status_code == 403
