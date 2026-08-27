"""示範資料裡的 Migration Case Key 演練（AC-07）：載入時預算/專案/合約三筆名稱刻意都不同，
只靠同一把示範用的案件關聯鍵接回同一個案件；一鍵清空要能連這個案件跟新增的示範專案一起清乾淨。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "demomig.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_示範資料載入後預算專案合約靠同一把key接到同一個案件(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/dev-console/demo-data/load")

        cases = client.get("/api/cases").json()["data"]
        mig_case = next(c for c in cases if c["case_code"] == "DEMO-C-MIG")

        budgets = client.get("/api/budgets").json()["data"]
        mig_budget = next(b for b in budgets if b["budget_code"] == "DEMO-BUD-MIG")

        projects = client.get("/api/projects").json()["data"]
        mig_project = next(p for p in projects if p["project_code"] == "DEMO-PRJ-MIG")

        contracts = client.get("/api/contracts").json()["data"]
        mig_contract = next(k for k in contracts if k["external_code"] == "DEMO-K-MIG")

        # 名稱完全不同，但全都掛回同一個案件——證明是靠 Key 接的，不是靠同名巧合
        assert mig_budget["case_id"] == mig_case["id"]
        assert mig_project["case_id"] == mig_case["id"]
        assert mig_contract["case_id"] == mig_case["id"]
        assert mig_budget["category"] != mig_project["project_name"] != mig_contract["contract_name"]


def test_清空示範資料連migration示範案件與專案一起清乾淨(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/dev-console/demo-data/load")
        client.post("/api/dev-console/demo-data/clear")

        assert not any(c["case_code"] == "DEMO-C-MIG" for c in client.get("/api/cases").json()["data"])
        assert not any(b["budget_code"] == "DEMO-BUD-MIG" for b in client.get("/api/budgets").json()["data"])
        assert not any(p["project_code"] == "DEMO-PRJ-MIG" for p in client.get("/api/projects").json()["data"])
        assert not any(k["external_code"] == "DEMO-K-MIG" for k in client.get("/api/contracts").json()["data"])


def test_重複載入不會長出重複的migration示範案件(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/dev-console/demo-data/load")
        client.post("/api/dev-console/demo-data/load")

        cases = [c for c in client.get("/api/cases").json()["data"] if c["case_code"] == "DEMO-C-MIG"]
        assert len(cases) == 1
