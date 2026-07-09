"""名稱歸納：廠商/案件/專案名相近歸納，合併/分開/復原/還原，及解析。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "name.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _seed(tmp_path):
    from app import store

    with store.connect() as conn:
        conn.execute("INSERT INTO contracts (contract_code,contract_name,vendor_name) VALUES ('K1','A','中華電信')")
        conn.execute("INSERT INTO purchases (purchase_code,item_name,vendor_name) VALUES ('P1','x','中華電')")
        conn.execute("INSERT INTO payments (contract_id,payment_month,payment_amount,vendor) VALUES (1,'2026-08',100,'中華電信')")


def test_values_and_merge(tmp_path):
    with _client(tmp_path) as client:
        _seed(tmp_path)
        vals = {v["name"]: v for v in client.get("/api/name-values?kind=vendor").json()["data"]["values"]}
        assert vals["中華電信"]["count"] == 2 and vals["中華電"]["count"] == 1
        assert vals["中華電信"]["canonical"] is None

        r = client.post("/api/name-merge", json={"kind": "vendor", "names": ["中華電信", "中華電"],
                                                 "canonical_name": "中華電信股份有限公司", "reason": "同廠商簡寫"})
        assert r.status_code == 200 and r.json()["data"]["merged"] == 2
        vals2 = {v["name"]: v for v in client.get("/api/name-values?kind=vendor").json()["data"]["values"]}
        assert vals2["中華電"]["canonical"] == "中華電信股份有限公司"


def test_merge_requires_reason(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/name-merge", json={"kind": "vendor", "names": ["A", "B"], "canonical_name": "A", "reason": " "})
        assert r.status_code == 400


def test_undo_and_reset(tmp_path):
    with _client(tmp_path) as client:
        _seed(tmp_path)
        d = client.post("/api/name-merge", json={"kind": "vendor", "names": ["中華電信", "中華電"],
                                                 "canonical_name": "中華電信", "reason": "x"}).json()["data"]
        client.post(f"/api/name-decisions/{d['decision_id']}/undo")
        vals = {v["name"]: v for v in client.get("/api/name-values?kind=vendor").json()["data"]["values"]}
        assert vals["中華電"]["canonical"] is None  # 復原後回未歸納

        client.post("/api/name-merge", json={"kind": "vendor", "names": ["中華電信", "中華電"], "canonical_name": "中華電信", "reason": "y"})
        rst = client.post("/api/name-reset?kind=vendor").json()["data"]
        assert rst["removed_masters"] >= 1


def test_name_kinds_isolated(tmp_path):
    with _client(tmp_path) as client:
        from app import store
        with store.connect() as conn:
            conn.execute("INSERT INTO cases (case_code,title) VALUES ('C1','郵件主機維護')")
            conn.execute("INSERT INTO projects (project_code,project_name) VALUES ('PR1','資安專案')")
        assert any(v["name"] == "郵件主機維護" for v in client.get("/api/name-values?kind=case").json()["data"]["values"])
        assert any(v["name"] == "資安專案" for v in client.get("/api/name-values?kind=project").json()["data"]["values"])


def test_blocked_for_handler(tmp_path):
    with _client(tmp_path, login="ap03") as client:
        r = client.post("/api/name-merge", json={"kind": "vendor", "names": ["A"], "canonical_name": "A", "reason": "x"})
        assert r.status_code == 403
