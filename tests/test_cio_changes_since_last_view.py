"""CIO「自上次查看以來」變動提醒：以 audit_logs 為準；查看即視為已讀，下次只顯示這之後的變動。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "cio_changes.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_first_visit_has_no_changes(tmp_path):
    with _client(tmp_path) as client:
        d = client.get("/api/reports/cio-changes-since-last-view").json()["data"]
        assert d["first_visit"] is True
        assert d["changes"] == []
        assert d["total_count"] == 0


def test_second_visit_shows_changes_made_in_between(tmp_path):
    with _client(tmp_path) as client:
        # 第一次查看：標記已讀，之後才發生的變動才算數
        client.get("/api/reports/cio-changes-since-last-view")

        client.post("/api/cases", json={"case_code": "CHG-1", "title": "變動測試案"})
        client.post("/api/cases", json={"case_code": "CHG-2", "title": "變動測試案2"})

        d = client.get("/api/reports/cio-changes-since-last-view").json()["data"]
        assert d["first_visit"] is False
        cases_create = next((c for c in d["changes"] if c["table"] == "cases" and c["action"] == "create"), None)
        assert cases_create is not None
        assert cases_create["count"] == 2
        assert cases_create["table_label"] == "案件"
        assert cases_create["action_label"] == "新增"
        assert d["total_count"] >= 2


def test_third_visit_only_sees_changes_since_second(tmp_path):
    with _client(tmp_path) as client:
        client.get("/api/reports/cio-changes-since-last-view")
        client.post("/api/cases", json={"case_code": "OLD-1", "title": "舊變動"})
        client.get("/api/reports/cio-changes-since-last-view")  # 第二次查看：OLD-1 已讀
        d = client.get("/api/reports/cio-changes-since-last-view").json()["data"]
        # 第三次查看：兩次查看之間沒有新變動
        assert d["changes"] == []
        assert d["total_count"] == 0


def test_per_actor_independent_baseline(tmp_path):
    with _client(tmp_path, login="ap01") as client:
        client.get("/api/reports/cio-changes-since-last-view")
        client.post("/api/cases", json={"case_code": "INDEP-1", "title": "獨立基準測試"})
        # 換一個帳號，第一次查看應各自獨立（自己的 first_visit）
        client.post("/api/auth/login", json={"username": "admin", "password": "T3st!Pass"})
        d_admin = client.get("/api/reports/cio-changes-since-last-view").json()["data"]
        assert d_admin["first_visit"] is True
