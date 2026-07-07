"""新功能：月度支出彙總 /api/reports/monthly-spending。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "ms.db")
    from app.main import create_app

    return TestClient(create_app())


def _login(client, user):
    client.post("/api/auth/login", json={"username": user, "password": "T3st!Pass"})


def _seed(table, payload):
    from app import store

    return store.insert_row(table, payload)


def test_monthly_spending_groups_by_month(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap02")  # 主管，看全部、可寫
        case = client.post("/api/cases", json={"case_code": "MS", "title": "m"}).json()["data"]
        ct = client.post(
            "/api/contracts",
            json={"contract_code": "MSC", "contract_name": "c", "case_id": case["id"]},
        ).json()["data"]
        for month, amount, status in [
            ("2026-01", 100, "closed"),
            ("2026-01", 50, "pending"),
            ("2026-02", 200, "pending"),
        ]:
            client.post(
                "/api/payments",
                json={"contract_id": ct["id"], "payment_month": month, "payment_amount": amount, "status": status},
            )
        rows = client.get("/api/reports/monthly-spending").json()["data"]
        by_month = {r["month"]: r for r in rows}
        assert by_month["2026-01"]["total"] == 150
        assert by_month["2026-01"]["paid"] == 100
        assert by_month["2026-01"]["pending"] == 50
        assert by_month["2026-01"]["count"] == 2
        assert by_month["2026-02"]["total"] == 200
        # 依月份新到舊排序
        assert [r["month"] for r in rows][:2] == ["2026-02", "2026-01"]


def test_monthly_spending_requires_login(tmp_path):
    with _client(tmp_path) as client:
        assert client.get("/api/reports/monthly-spending").status_code == 401


def test_monthly_spending_scoped_for_handler(tmp_path):
    with _client(tmp_path) as client:
        their_case = _seed("cases", {"case_code": "OTHER", "title": "o", "owner": "ap02"})
        their_ct = _seed("contracts", {"contract_code": "OCT", "contract_name": "c", "case_id": their_case["id"]})
        _seed("payments", {"contract_id": their_ct["id"], "payment_month": "2026-03", "payment_amount": 999})
        my_case = _seed("cases", {"case_code": "MINE", "title": "m", "owner": "ap03"})
        my_ct = _seed("contracts", {"contract_code": "MCT", "contract_name": "c", "case_id": my_case["id"]})
        _seed("payments", {"contract_id": my_ct["id"], "payment_month": "2026-03", "payment_amount": 10})

        _login(client, "ap03")  # 承辦只看自己的
        rows = client.get("/api/reports/monthly-spending").json()["data"]
        march = next((r for r in rows if r["month"] == "2026-03"), None)
        assert march is not None and march["total"] == 10  # 不含別人的 999
