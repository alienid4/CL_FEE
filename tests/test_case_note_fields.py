"""案件新增「備註」與「下一步」欄位（獨立欄位，不塞進其他欄）。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "note.db")
    from app.main import create_app

    client = TestClient(create_app())
    client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
    return client


def test_case_carries_note_and_next_step(tmp_path):
    with _client(tmp_path) as client:
        case = client.post(
            "/api/cases",
            json={"case_code": "NB-1", "title": "電力費調整", "note": "需人工確認預算外依據", "next_step": "補來源說明"},
        ).json()["data"]
        assert case["note"] == "需人工確認預算外依據"
        assert case["next_step"] == "補來源說明"

        # 只改備註，下一步不受影響
        updated = client.patch(f"/api/cases/{case['id']}", json={"note": "已補齊依據"}).json()["data"]
        assert updated["note"] == "已補齊依據"
        assert updated["next_step"] == "補來源說明"

        # 清單也帶回這兩欄
        rows = client.get("/api/cases").json()["data"]
        row = next(r for r in rows if r["id"] == case["id"])
        assert row["note"] == "已補齊依據" and row["next_step"] == "補來源說明"


def test_case_note_defaults_empty(tmp_path):
    with _client(tmp_path) as client:
        case = client.post("/api/cases", json={"case_code": "NB-2", "title": "無備註案"}).json()["data"]
        assert case["note"] == "" and case["next_step"] == ""
