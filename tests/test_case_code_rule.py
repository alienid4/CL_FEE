"""編號規則（主管 2026-08-03）：系統自己配的號只能是英數，不得含連字號、底線與中文。
外部帶進來的編號（Excel 匯入的舊案號）不在此限——那是別人的號，改掉就對不回原始檔。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "code.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_清理計畫先列出會改哪些不會改哪些(tmp_path):
    with _client(tmp_path) as client:
        import app.store as store

        client.post("/api/working-year?year=2026")
        # 舊格式暫時號（早期系統配的）
        old_tmp = client.post("/api/cases", json={"case_code": "TMP-20260099", "title": "舊格式暫時號"}).json()["data"]
        # 中文編號（早期建預算時系統拿名稱當編號留下的）
        zh = client.post("/api/cases", json={"case_code": "資訊安全設備", "title": "中文編號"}).json()["data"]
        # Excel 匯入帶進來的原始編號 → 不能動
        imported = client.post("/api/cases", json={"case_code": "MIS-2024-001", "title": "匯入的"}).json()["data"]
        store.update_row("cases", imported["id"], {"source_file": "舊系統匯出.xlsx"})

        plan = client.get("/api/dev-console/case-codes/plan").json()["data"]
        moves = {c["from"]: c["to"] for c in plan["changes"]}
        assert moves["TMP-20260099"] == "TMP20260099"        # 只拿掉連字號，號碼本身不變
        assert moves["資訊安全設備"].startswith("TMP2026")     # 中文的重配一個暫時號
        assert "MIS-2024-001" not in moves                   # 匯入的原始編號不動
        assert plan["kept"][0]["id"] == imported["id"]
        assert plan["change_count"] == 2 and plan["kept_count"] == 1
        # 只是計畫，還沒真的改
        after = {c["id"]: c["case_code"] for c in client.get("/api/cases").json()["data"]}
        assert after[old_tmp["id"]] == "TMP-20260099" and after[zh["id"]] == "資訊安全設備"


def test_執行換號並留稽核且可重跑(tmp_path):
    with _client(tmp_path) as client:
        from app.store import is_system_code_valid

        client.post("/api/working-year?year=2026")
        a = client.post("/api/cases", json={"case_code": "TMP-20260099", "title": "舊格式"}).json()["data"]

        r = client.post("/api/dev-console/case-codes/fix").json()["data"]
        assert r["changed"] == 1
        codes = {c["id"]: c["case_code"] for c in client.get("/api/cases").json()["data"]}
        assert codes[a["id"]] == "TMP20260099"
        assert all(is_system_code_valid(v) for v in codes.values())

        logs = client.get("/api/audit-logs", params={"table_name": "cases", "action": "recode"}).json()["data"]
        assert len(logs) == 1                                 # 換號留得住紀錄

        assert client.post("/api/dev-console/case-codes/fix").json()["data"]["changed"] == 0  # 冪等


def test_換號撞到既有編號會往後掛(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/working-year?year=2026")
        client.post("/api/cases", json={"case_code": "TMP20260099", "title": "已經是新格式"})
        client.post("/api/cases", json={"case_code": "TMP-20260099", "title": "舊格式撞號"})

        client.post("/api/dev-console/case-codes/fix")
        codes = sorted(c["case_code"] for c in client.get("/api/cases").json()["data"])
        assert codes == ["TMP20260099", "TMP20260099A02"]     # 不覆蓋既有，往後掛且仍是純英數
