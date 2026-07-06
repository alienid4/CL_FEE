import os

from fastapi.testclient import TestClient


def test_health_openapi_and_web_shell(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "test.db")
    from app.main import create_app

    with TestClient(create_app()) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["service"] == "fee-contract-control"
        assert health.json()["database"]["type"] == "sqlite"

        docs = client.get("/openapi.json")
        assert docs.status_code == 200
        paths = docs.json()["paths"]
        assert "/api/cost-contract-items" in paths
        assert "/api/contracts" in paths
        assert "/api/budget-lines" in paths
        assert "/api/payment-schedules" in paths
        assert "/api/documents" in paths
        assert "/api/import-batches" in paths
        assert "/api/system/case-360/{case_id}" in paths
        assert "/api/system/priority-matrix" in paths
        assert "/api/system/cmdb-integration" in paths

        home = client.get("/")
        assert home.status_code == 200
        assert "費用合約控管系統" in home.text

        script = client.get("/static/app.js")
        assert script.status_code == 200
        assert "Case 360" in script.text
        assert "/api/system/case-360" in script.text
        assert "CMDB 預留" in script.text
        assert "/api/system/cmdb-integration" in script.text


def test_create_search_and_audit_flow(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "test.db")
    from app.main import create_app

    with TestClient(create_app()) as client:
        created = client.post(
            "/api/cost-contract-items",
            json={
                "cost_item_code": "FEE-001",
                "cost_item_name": "Network maintenance",
                "vendor_name": "Example Vendor",
                "contract_amount": 120000,
            },
        )
        assert created.status_code == 201
        item_id = created.json()["data"]["id"]

        found = client.get("/api/search", params={"q": "Network"})
        assert found.status_code == 200
        assert found.json()["data"][0]["id"] == item_id

        logs = client.get("/api/audit-logs")
        assert logs.status_code == 200
        assert logs.json()["data"][0]["action"] == "create"


def test_m2_core_records_flow(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "test.db")
    from app.main import create_app

    with TestClient(create_app()) as client:
        contract = client.post(
            "/api/contracts",
            json={
                "contract_code": "CON-001",
                "contract_name": "Core network maintenance contract",
                "vendor_name": "Example Vendor",
                "amount": 500000,
            },
        )
        assert contract.status_code == 201

        budget = client.post(
            "/api/budget-lines",
            json={
                "budget_year": 2026,
                "category": "maintenance",
                "item_name": "Core network maintenance",
                "owner_group": "network",
                "budget_amount": 600000,
            },
        )
        assert budget.status_code == 201

        payment = client.post(
            "/api/payment-schedules",
            json={
                "contract_id": contract.json()["data"]["id"],
                "payment_month": "2026-01",
                "payment_amount": 250000,
                "invoice_status": "not_received",
            },
        )
        assert payment.status_code == 201

        document = client.post(
            "/api/documents",
            json={
                "contract_id": contract.json()["data"]["id"],
                "file_name": "sample-signing.pdf",
                "document_type": "signing",
                "source_note": "page 1 amount evidence",
            },
        )
        assert document.status_code == 201

        batch = client.post(
            "/api/import-batches",
            json={
                "source_file_name": "budget-source.xlsx",
                "source_type": "excel",
                "row_count": 10,
            },
        )
        assert batch.status_code == 201

        search = client.get("/api/search", params={"q": "maintenance"})
        assert search.status_code == 200
        assert any(row["result_type"] == "contract" for row in search.json()["data"])

        dashboard = client.get("/api/dashboard/manager")
        assert dashboard.status_code == 200
        assert dashboard.json()["data"]["cards"]["contracts"] == 1
        assert dashboard.json()["data"]["cards"]["payment_schedules"] == 1
        assert dashboard.json()["data"]["cards"]["documents"] == 1


def test_system_features_case_360_drilldown_and_priority(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "test.db")
    from app.main import create_app

    with TestClient(create_app()) as client:
        case = client.post(
            "/api/signing-cases",
            json={
                "case_code": "CASE-2026-0001",
                "title": "XX機房維護費",
                "category": "王小明",
                "amount": 15000000,
                "status": "pending",
            },
        ).json()["data"]
        contract = client.post(
            "/api/contracts",
            json={
                "contract_code": "CON-2026-0001",
                "contract_name": "XX機房維護合約",
                "vendor_name": "XX電信",
                "amount": 15000000,
            },
        ).json()["data"]
        assert client.post(
            "/api/payment-schedules",
            json={
                "case_id": case["id"],
                "contract_id": contract["id"],
                "payment_month": "2026-06",
                "payment_amount": 2500000,
                "invoice_status": "not_received",
                "status": "pending",
            },
        ).status_code == 201
        assert client.post(
            "/api/documents",
            json={
                "case_id": case["id"],
                "contract_id": contract["id"],
                "file_name": "signing.pdf",
                "document_type": "signing",
                "source_note": "簽呈第 1 頁金額依據",
            },
        ).status_code == 201

        case_360 = client.get(f"/api/system/case-360/{case['id']}")
        assert case_360.status_code == 200
        payload = case_360.json()["data"]
        assert payload["case"]["title"] == "XX機房維護費"
        assert payload["totals"]["payment_amount"] == 2500000
        assert any(node["step"] == "付款" for node in payload["timeline"])
        assert any(item["type"] == "document" for item in payload["evidence"])

        drilldown = client.get("/api/system/drilldown", params={"metric": "invoice_month", "month": "2026-06"})
        assert drilldown.status_code == 200
        assert drilldown.json()["data"]["rows"][0]["vendor"] == "XX電信"

        priority = client.get("/api/system/priority-matrix")
        assert priority.status_code == 200
        assert priority.json()["data"]["bubbles"][0]["case_id"] == case["id"]

        owners = client.get("/api/system/owners")
        assert owners.status_code == 200
        assert owners.json()["data"][0]["owner"] == "王小明"


def test_cmdb_integration_placeholder(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "test.db")
    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/api/system/cmdb-integration")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["phase"] == "reserved"
        assert "cmdb_ci_id" in data["reserved_fields"]
        assert "CMDB API" in data["future_sources"]
        assert "Case 360" in data["supported_targets"]


def test_payment_schedule_query_filters(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "test.db")
    from app.main import create_app

    with TestClient(create_app()) as client:
        contract_a = client.post(
            "/api/contracts",
            json={
                "contract_code": "PAY-A",
                "contract_name": "Payment query contract A",
                "amount": 100000,
            },
        ).json()["data"]
        contract_b = client.post(
            "/api/contracts",
            json={
                "contract_code": "PAY-B",
                "contract_name": "Payment query contract B",
                "amount": 200000,
            },
        ).json()["data"]

        schedules = [
            {
                "contract_id": contract_a["id"],
                "payment_month": "2026-01",
                "payment_amount": 50000,
                "invoice_status": "not_received",
                "status": "draft",
            },
            {
                "contract_id": contract_a["id"],
                "payment_month": "2026-02",
                "payment_amount": 75000,
                "invoice_status": "received",
                "status": "approved",
            },
            {
                "contract_id": contract_b["id"],
                "payment_month": "2026-03",
                "payment_amount": 125000,
                "invoice_status": "paid",
                "status": "closed",
            },
        ]
        for schedule in schedules:
            assert client.post("/api/payment-schedules", json=schedule).status_code == 201

        contract_a_rows = client.get(
            "/api/payment-schedules",
            params={"contract_id": contract_a["id"]},
        ).json()["data"]
        assert len(contract_a_rows) == 2
        assert {row["payment_month"] for row in contract_a_rows} == {"2026-01", "2026-02"}

        feb_rows = client.get(
            "/api/payment-schedules",
            params={"payment_month_from": "2026-02", "payment_month_to": "2026-03"},
        ).json()["data"]
        assert [row["payment_month"] for row in feb_rows] == ["2026-03", "2026-02"]

        paid_rows = client.get(
            "/api/payment-schedules",
            params={
                "invoice_status": "paid",
                "payment_amount_min": 100000,
                "payment_amount_max": 150000,
            },
        ).json()["data"]
        assert len(paid_rows) == 1
        assert paid_rows[0]["contract_id"] == contract_b["id"]

        limited_rows = client.get("/api/payment-schedules", params={"q": "closed", "limit": 1}).json()["data"]
        assert len(limited_rows) == 1
        assert limited_rows[0]["status"] == "closed"

        invalid_limit = client.get("/api/payment-schedules", params={"limit": 0})
        assert invalid_limit.status_code == 422
