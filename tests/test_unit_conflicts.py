"""單位管理 Step 1：撞名偵測。同代號多名／同名多代號要被揪出，乾淨資料回空。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "unitconf.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _seed_conflict(tmp_path):
    """代號 8101 在人數表叫「資訊管理處」、在預算分攤叫「資訊架構部」——就是使用者遇到的實況。"""
    from app import store

    with store.connect() as conn:
        conn.execute("INSERT INTO unit_headcounts (unit_code, unit_name, headcount) VALUES ('8101','資訊管理處',5)")
        conn.execute("INSERT INTO budgets (budget_code, amount) VALUES ('B-UC1', 1000)")
        bid = conn.execute("SELECT id FROM budgets WHERE budget_code='B-UC1'").fetchone()["id"]
        conn.execute(
            "INSERT INTO budget_allocations (budget_id, seq, unit_code, unit_name, amount) "
            "VALUES (?, 1, '8101', '資訊架構部', 500)",
            (bid,),
        )


def test_detects_same_code_multiple_names(tmp_path):
    with _client(tmp_path) as client:
        _seed_conflict(tmp_path)
        data = client.get("/api/unit-conflicts").json()["data"]
        codes = {c["unit_code"] for c in data["code_conflicts"]}
        assert "8101" in codes
        conf = next(c for c in data["code_conflicts"] if c["unit_code"] == "8101")
        names = {v["unit_name"] for v in conf["variants"]}
        assert names == {"資訊管理處", "資訊架構部"}
        assert data["summary"]["code_conflicts"] >= 1


def test_detects_same_name_multiple_codes(tmp_path):
    from app import store

    with _client(tmp_path) as client:
        with store.connect() as conn:
            conn.execute("INSERT INTO unit_headcounts (unit_code, unit_name, headcount) VALUES ('8101','資訊管理處',5)")
            conn.execute("INSERT INTO unit_headcounts (unit_code, unit_name, headcount) VALUES ('8201','資訊管理處',3)")
        data = client.get("/api/unit-conflicts").json()["data"]
        names = {c["unit_name"] for c in data["name_conflicts"]}
        assert "資訊管理處" in names


def test_clean_data_reports_no_conflict(tmp_path):
    from app import store

    with _client(tmp_path) as client:
        with store.connect() as conn:
            conn.execute("INSERT INTO unit_headcounts (unit_code, unit_name, headcount) VALUES ('8101','資訊管理處',5)")
            conn.execute("INSERT INTO unit_headcounts (unit_code, unit_name, headcount) VALUES ('8201','資本市場處',3)")
        data = client.get("/api/unit-conflicts").json()["data"]
        assert data["summary"]["code_conflicts"] == 0
        assert data["summary"]["name_conflicts"] == 0
