import json
import os

from fastapi.testclient import TestClient
import pytest


def client_for(tmp_path, login=True):
    os.environ["SQLITE_PATH"] = str(tmp_path / "fresh.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        # 預設以主管/助理(ap02)登入——可讀可寫，適合大多數 CRUD 測試
        client.post("/api/auth/login", json={"username": "ap02", "password": "T3st!Pass"})
    return client


def test_local_mock_login_accounts(tmp_path):
    with client_for(tmp_path, login=False) as client:
        assert client.get("/api/auth/me").status_code == 401

        failed = client.post("/api/auth/login", json={"username": "ap01", "password": "bad"})
        assert failed.status_code == 401

        logged_in = client.post("/api/auth/login", json={"username": "ap01", "password": "T3st!Pass"})
        assert logged_in.status_code == 200
        cio = logged_in.json()["data"]
        assert cio["username"] == "ap01"
        assert cio["role_name"] == "CIO"
        assert cio["role_code"] == "cio"
        assert "budget" in cio["allowed_modules"]
        assert cio["allowed_actions"] == ["read"]  # CIO 唯讀（只看重點數據）

        current = client.get("/api/auth/me")
        assert current.status_code == 200
        assert current.json()["data"]["username"] == "ap01"

        for username, role_name, role_code in [
            ("ap02", "主管/助理", "manager_assistant"),
            ("ap03", "承辦", "handler"),
        ]:
            response = client.post(
                "/api/auth/login",
                json={"username": username, "password": "T3st!Pass"},
            )
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["role_name"] == role_name
            assert data["role_code"] == role_code
            assert "cases-module" in data["allowed_modules"]
            if username == "ap03":
                assert "budget" not in data["allowed_modules"]
                assert "signoff" not in data["allowed_modules"]
                assert "contracts-module" not in data["allowed_modules"]
                assert "preflight" not in data["allowed_actions"]

        assert client.post("/api/auth/logout").status_code == 200
        assert client.get("/api/auth/me").status_code == 401


def test_cio_is_read_only_and_handler_can_write(tmp_path):
    with client_for(tmp_path, login=False) as client:
        client.post("/api/auth/login", json={"username": "ap01", "password": "T3st!Pass"})
        assert client.get("/api/cases").status_code == 200  # CIO 可看
        assert client.post("/api/cases", json={"case_code": "CIO-X", "title": "x"}).status_code == 403  # 不能寫
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        assert client.post("/api/cases", json={"case_code": "H-Y", "title": "y"}).status_code == 201  # 承辦可寫


def test_health_openapi_and_web(tmp_path):
    with client_for(tmp_path) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["version"] == "0.2.0-fresh"

        openapi = client.get("/openapi.json")
        assert openapi.status_code == 200
        paths = openapi.json()["paths"]
        assert "/api/cases" in paths
        assert "/api/contracts" in paths
        assert "/api/payments" in paths
        assert "/api/documents/{document_id}/disable" in paths
        assert "post" in paths["/api/documents/{document_id}/disable"]
        assert "/api/audit-logs" in paths
        assert "/api/cmdb" in paths
        assert "/api/import-batches" in paths
        assert "/api/import-batches/{batch_id}/rows" in paths
        assert "/api/import-batches/{batch_id}/mapping-preview" in paths
        assert "/api/import-batches/{batch_id}/confirm-preflight" in paths
        assert "/api/import-batches/{batch_id}/confirm" in paths
        assert "/api/import-mapping-draft" in paths
        assert "/api/dev-console/status" in paths
        assert "/api/dev-console/run" in paths
        assert "/api/auth/login" in paths
        assert "/api/auth/me" in paths
        assert "/api/auth/logout" in paths

        home = client.get("/")
        assert home.status_code == 200
        assert 'id="login-form"' in home.text
        assert 'id="app-shell" class="app-shell" hidden' in home.text
        assert "ap01：CIO" in home.text
        assert "ap02：主管/助理" in home.text
        assert "ap03：承辦" in home.text
        assert "八項控管看板" not in home.text
        assert "主管角度" not in home.text
        assert "更新時間：" not in home.text
        assert "重新整理" not in home.text
        assert "主管儀表板" in home.text
        assert 'data-case-tab="list"' in home.text
        assert 'data-case-panel="matrix"' in home.text
        assert "處理優先矩陣" in home.text
        assert "線性進度圖" in home.text
        assert "待確認項目" in home.text
        assert 'id="cases-module"' in home.text
        assert 'id="budget"' in home.text
        assert 'id="projects"' in home.text
        assert 'id="signoff"' in home.text
        assert 'id="contracts-module"' in home.text
        assert 'id="purchases"' in home.text
        assert 'id="payments-module"' in home.text
        assert 'id="data-review"' in home.text
        assert "年度預算編列" in home.text
        assert "PROJ-2026-0001" in home.text
        assert "SIGN-2026-0001" in home.text
        assert "CON-2026-0001" in home.text
        assert "PR-2025-0001" in home.text
        assert "PAY-2025-0001" in home.text
        assert "正式寫入封鎖" in home.text
        assert "來源舉證鏈" in home.text
        assert "需處理案件（待辦）" in home.text  # 假面板已換成真待辦
        assert "來自真實案件" in home.text
        assert 'id="todo-list"' in home.text  # 由 /api/todo 動態載入
        assert "月度支出彙總" in home.text  # 真月度支出面板
        assert 'id="monthly-spending-body"' in home.text
        assert "EVID-2026-0001" in home.text
        assert "檢視角色" not in home.text
        assert "使用者：" not in home.text
        assert 'name="viewport" content="width=1500' in home.text
        assert 'id="contract-form"' in home.text
        assert 'id="payment-form"' in home.text
        assert 'id="document-form"' in home.text
        assert 'id="contracts"' in home.text
        assert 'id="payments"' in home.text
        assert 'id="documents"' in home.text
        assert '<option value="disabled">已停用</option>' in home.text
        for forbidden_ui_text in ["Contract code", "Amount", "Draft", "Reviewing", "Disabled", "檢視角色", "使用者："]:
            assert forbidden_ui_text not in home.text

        dev_console = client.get("/dev-console")
        assert dev_console.status_code == 200
        assert "Development Control Panel" in dev_console.text
        assert "/static/dev-console.js" in dev_console.text

        script = client.get("/static/app.js")
        assert script.status_code == 200
        assert "/api/auth/login" in script.text
        assert "/api/auth/me" in script.text
        assert "/api/auth/logout" in script.text
        assert "applyRoleVisibility" in script.text
        assert "allowed_modules" in script.text
        assert 'querySelector("#refresh")' not in script.text
        assert 'method: id ? "PATCH" : "POST"' in script.text
        assert "/disable" in script.text
        assert 'method: "DELETE"' in script.text
        assert 'api: "/api/contracts"' in script.text
        assert 'api: "/api/payments"' in script.text
        assert 'api: "/api/documents"' in script.text
        assert "startResourceEdit" in script.text
        assert "handleResourceAction" in script.text
        assert "getAttribute(`data-${config.idAttr}`)" in script.text
        assert 'data-resource-id="${item.id}"' in script.text
        assert 'button.getAttribute("data-resource-id") || row?.getAttribute(`data-${config.idAttr}`)' in script.text
        assert "await startResourceEdit(type, id)" in script.text
        assert "await loadResource(type)" in script.text
        assert "案件 ${escapeHtml(valueOrDash(item.case_id))} / 合約 ${escapeHtml(valueOrDash(item.contract_id))}" in script.text
        assert 'class="mini-row" data-${config.idAttr}="${item.id}"' in script.text
        assert "data-source-row-id" in script.text
        assert "對應版本 ${escapeHtml(mappingVersion)}" in script.text
        assert "來源列 #" in script.text
        assert "正式寫入前檢核" in script.text
        assert "檢視角色" not in script.text
        assert "使用者：" not in script.text
        assert 'window.scrollTo({ top: 0, left: 0, behavior: "instant" });' in script.text

        console_script = client.get("/static/dev-console.js")
        assert console_script.status_code == 200
        assert "/api/dev-console/status" in console_script.text
        assert "/api/dev-console/run" in console_script.text

        styles = client.get("/static/styles.css")
        assert styles.status_code == 200
        assert "main {\n  align-content: start;\n  align-items: start;" in styles.text
        assert ".module-workspace {\n  align-content: start;\n  align-items: start;" in styles.text
        assert ".note-list li" in styles.text


def test_dev_console_status_and_allowlisted_dry_run(tmp_path):
    with client_for(tmp_path) as client:
        status_response = client.get("/api/dev-console/status")
        assert status_response.status_code == 200
        payload = status_response.json()["data"]
        assert payload["version"] == "v2.1-local-control-panel-mvp"
        assert payload["prompt_pack"].endswith("v2.1")
        assert payload["safety"]["command_mode"] == "allowlist"
        assert payload["safety"]["production_data"] == "blocked"
        command_ids = {command["command_id"] for command in payload["commands"]}
        assert {"fast_ci", "local_ci", "deep_security", "profile", "runtime_fast", "audit_summary"} <= command_ids

        dry_run = client.post(
            "/api/dev-console/run",
            json={"command_id": "profile", "dry_run": True},
        )
        assert dry_run.status_code == 200
        data = dry_run.json()["data"]
        assert data["dry_run"] is True
        assert data["command_id"] == "profile"
        assert "scripts\\detect_project_profile.ps1" in data["args"]

        blocked = client.post(
            "/api/dev-console/run",
            json={"command_id": "not_allowed", "dry_run": True},
        )
        assert blocked.status_code == 404


def test_case_contract_payment_document_flow(tmp_path):
    with client_for(tmp_path) as client:
        case = client.post(
            "/api/cases",
            json={
                "case_code": "CASE-001",
                "title": "Network maintenance review",
                "owner": "IT",
                "amount": 300000,
            },
        )
        assert case.status_code == 201
        case_id = case.json()["data"]["id"]

        contract = client.post(
            "/api/contracts",
            json={
                "contract_code": "CON-001",
                "contract_name": "Network maintenance contract",
                "vendor_name": "Example Vendor",
                "amount": 300000,
                "case_id": case_id,
            },
        )
        assert contract.status_code == 201
        contract_id = contract.json()["data"]["id"]

        payment = client.post(
            "/api/payments",
            json={
                "contract_id": contract_id,
                "payment_month": "2026-07",
                "payment_amount": 100000,
                "invoice_status": "not_received",
            },
        )
        assert payment.status_code == 201

        document = client.post(
            "/api/documents",
            json={
                "case_id": case_id,
                "contract_id": contract_id,
                "file_name": "contract.pdf",
                "document_type": "contract",
            },
        )
        assert document.status_code == 201

        dashboard = client.get("/api/dashboard").json()["data"]
        assert dashboard["counts"] == {"cases": 1, "contracts": 1, "payments": 1, "documents": 1}
        assert dashboard["contract_amount"] == 300000

        detail = client.get(f"/api/cases/{case_id}/360").json()["data"]
        assert detail["case"]["case_code"] == "CASE-001"
        assert detail["totals"]["payment_amount"] == 100000
        assert detail["totals"]["document_count"] == 1

        results = client.get("/api/search", params={"q": "Network"}).json()["data"]
        assert {row["type"] for row in results} >= {"case", "contract"}


def test_cmdb_placeholder_is_explicitly_reserved(tmp_path):
    with client_for(tmp_path) as client:
        payload = client.get("/api/cmdb").json()["data"]
        assert payload["status"] == "reserved"
        assert "cmdb_ci_id" in payload["reserved_fields"]


def test_update_disable_and_delete_lifecycle(tmp_path):
    with client_for(tmp_path) as client:
        case_id = client.post(
            "/api/cases",
            json={"case_code": "CASE-LIFE", "title": "Lifecycle case"},
        ).json()["data"]["id"]

        updated_case = client.patch(
            f"/api/cases/{case_id}",
            json={"owner": "Finance", "status": "reviewing", "risk_level": "high"},
        )
        assert updated_case.status_code == 200
        assert updated_case.json()["data"]["owner"] == "Finance"
        assert updated_case.json()["data"]["risk_level"] == "high"

        disabled_case = client.post(f"/api/cases/{case_id}/disable")
        assert disabled_case.status_code == 200
        assert disabled_case.json()["data"]["status"] == "disabled"

        contract_id = client.post(
            "/api/contracts",
            json={
                "contract_code": "CON-LIFE",
                "contract_name": "Lifecycle contract",
                "case_id": case_id,
            },
        ).json()["data"]["id"]
        updated_contract = client.patch(
            f"/api/contracts/{contract_id}",
            json={"vendor_name": "Lifecycle Vendor", "amount": 7500},
        )
        assert updated_contract.status_code == 200
        assert updated_contract.json()["data"]["vendor_name"] == "Lifecycle Vendor"

        disabled_contract = client.post(f"/api/contracts/{contract_id}/disable")
        assert disabled_contract.status_code == 200
        assert disabled_contract.json()["data"]["status"] == "disabled"

        payment_id = client.post(
            "/api/payments",
            json={
                "contract_id": contract_id,
                "payment_month": "2026-08",
                "payment_amount": 5000,
            },
        ).json()["data"]["id"]
        updated_payment = client.patch(
            f"/api/payments/{payment_id}",
            json={"invoice_status": "received", "payment_amount": 6000},
        )
        assert updated_payment.status_code == 200
        assert updated_payment.json()["data"]["invoice_status"] == "received"

        disabled_payment = client.post(f"/api/payments/{payment_id}/disable")
        assert disabled_payment.status_code == 200
        assert disabled_payment.json()["data"]["status"] == "disabled"

        document_id = client.post(
            "/api/documents",
            json={
                "case_id": case_id,
                "contract_id": contract_id,
                "file_name": "lifecycle.pdf",
            },
        ).json()["data"]["id"]
        updated_document = client.patch(
            f"/api/documents/{document_id}",
            json={"document_type": "invoice", "source_note": "Uploaded by test"},
        )
        assert updated_document.status_code == 200
        assert updated_document.json()["data"]["document_type"] == "invoice"

        disabled_document = client.post(f"/api/documents/{document_id}/disable")
        assert disabled_document.status_code == 200
        assert disabled_document.json()["data"]["status"] == "disabled"

        paid = client.patch(f"/api/payments/{payment_id}", json={"status": "closed"})
        assert paid.status_code == 200
        assert paid.json()["data"]["status"] == "closed"

        assert client.delete(f"/api/documents/{document_id}").status_code == 204
        assert client.delete(f"/api/documents/{document_id}").status_code == 404

        assert client.delete(f"/api/payments/{payment_id}").status_code == 204
        assert client.delete(f"/api/contracts/{contract_id}").status_code == 204
        assert client.delete(f"/api/cases/{case_id}").status_code == 204

        audit_logs = client.get("/api/audit-logs", params={"limit": 100}).json()["data"]
        actions_by_table = {
            table: {row["action"] for row in audit_logs if row["table_name"] == table}
            for table in ("cases", "contracts", "payments", "documents")
        }
        for table, actions in actions_by_table.items():
            assert {"create", "update", "disable", "delete"} <= actions, table

        case_create = client.get(
            "/api/audit-logs",
            params={"table_name": "cases", "row_id": case_id, "action": "create"},
        ).json()["data"][0]
        assert case_create["actor"] == "ap02"  # 稽核記錄真實操作者（測試以 ap02 操作）
        assert case_create["before_json"] is None
        assert json.loads(case_create["after_json"])["case_code"] == "CASE-LIFE"

        document_disable = client.get(
            "/api/audit-logs",
            params={"table_name": "documents", "row_id": document_id, "action": "disable"},
        ).json()["data"][0]
        assert json.loads(document_disable["before_json"])["status"] == "active"
        assert json.loads(document_disable["after_json"])["status"] == "disabled"

        payment_delete = client.get(
            "/api/audit-logs",
            params={"table_name": "payments", "row_id": payment_id, "action": "delete"},
        ).json()["data"][0]
        assert json.loads(payment_delete["before_json"])["status"] == "closed"
        assert payment_delete["after_json"] is None


def audit_count(client, **params):
    return len(client.get("/api/audit-logs", params={"limit": 500, **params}).json()["data"])


@pytest.mark.parametrize(
    ("path", "payload", "patch_path", "legal_status"),
    [
        (
            "/api/cases",
            {"case_code": "CASE-STATUS", "title": "Status case"},
            "/api/cases/{id}",
            "approved",
        ),
        (
            "/api/contracts",
            {"contract_code": "CON-STATUS", "contract_name": "Status contract"},
            "/api/contracts/{id}",
            "reviewing",
        ),
        (
            "/api/payments",
            {"contract_id": 1, "payment_month": "2026-09", "payment_amount": 1000},
            "/api/payments/{id}",
            "scheduled",
        ),
        (
            "/api/documents",
            {"file_name": "status.pdf"},
            "/api/documents/{id}",
            "archived",
        ),
    ],
)
def test_status_dictionary_rejects_invalid_status_and_preserves_audit(
    tmp_path,
    path,
    payload,
    patch_path,
    legal_status,
):
    with client_for(tmp_path) as client:
        before_invalid_create = audit_count(client)
        invalid_create = client.post(path, json={**payload, "status": "not-a-real-status"})
        assert invalid_create.status_code == 422
        assert "Invalid" in invalid_create.json()["detail"]
        assert audit_count(client) == before_invalid_create

        created = client.post(path, json={**payload, "status": legal_status})
        assert created.status_code == 201
        created_data = created.json()["data"]
        row_id = created_data["id"]
        assert created_data["status"] == legal_status
        assert audit_count(client, row_id=row_id, action="create") == 1

        before_invalid_update = audit_count(client, row_id=row_id)
        invalid_update = client.patch(patch_path.format(id=row_id), json={"status": "not-a-real-status"})
        assert invalid_update.status_code == 422
        assert "Invalid" in invalid_update.json()["detail"]
        assert audit_count(client, row_id=row_id) == before_invalid_update
        assert audit_count(client, row_id=row_id, action="update") == 0

        disabled = client.post(f"{path}/{row_id}/disable")
        assert disabled.status_code == 200
        assert disabled.json()["data"]["status"] == "disabled"
        assert audit_count(client, row_id=row_id, action="disable") == 1

        after_disable = client.get(
            "/api/audit-logs",
            params={"table_name": path.rsplit("/", 1)[-1], "row_id": row_id, "action": "disable"},
        ).json()["data"][0]
        assert json.loads(after_disable["after_json"])["status"] == "disabled"


def test_payment_invoice_status_dictionary_rejects_invalid_value(tmp_path):
    with client_for(tmp_path) as client:
        before = audit_count(client)
        created = client.post(
            "/api/payments",
            json={
                "contract_id": 1,
                "payment_month": "2026-10",
                "payment_amount": 1200,
                "invoice_status": "missing-paper",
            },
        )
        assert created.status_code == 422
        assert "Invalid payments.invoice_status" in created.json()["detail"]
        assert audit_count(client) == before


def test_import_batch_stages_rows_without_touching_formal_tables(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        assert before_dashboard["counts"] == {"cases": 0, "contracts": 0, "payments": 0, "documents": 0}

        batch_response = client.post("/api/import-batches", json={"source_name": "budget-upload.csv"})
        assert batch_response.status_code == 201
        batch = batch_response.json()["data"]
        assert batch["source_name"] == "budget-upload.csv"
        assert batch["status"] == "created"

        rows_payload = {
            "rows": [
                {"case_code": "CASE-IMPORT-001", "title": "Only staged"},
                {"contract_code": "CON-IMPORT-001", "amount": "12000"},
            ]
        }
        staged_response = client.post(f"/api/import-batches/{batch['id']}/rows", json=rows_payload)
        assert staged_response.status_code == 201
        staged_rows = staged_response.json()["data"]
        assert [row["row_number"] for row in staged_rows] == [1, 2]
        assert {row["status"] for row in staged_rows} == {"staged"}
        assert staged_rows[0]["error_message"] is None
        assert json.loads(staged_rows[0]["raw_json"])["case_code"] == "CASE-IMPORT-001"

        after_dashboard = client.get("/api/dashboard").json()["data"]
        assert after_dashboard["counts"] == before_dashboard["counts"]

        listed_batches = client.get("/api/import-batches").json()["data"]
        assert listed_batches[0]["id"] == batch["id"]

        batch_detail = client.get(f"/api/import-batches/{batch['id']}").json()["data"]
        assert batch_detail["batch"]["id"] == batch["id"]
        assert len(batch_detail["rows"]) == 2

        listed_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        assert [row["id"] for row in listed_rows] == [row["id"] for row in staged_rows]

        audit_actions = {
            row["action"]
            for row in client.get(
                "/api/audit-logs",
                params={"table_name": "import_batches", "row_id": batch["id"]},
            ).json()["data"]
        }
        assert {"create", "stage_rows"} <= audit_actions


def test_import_mapping_preview_is_read_only_and_keeps_unmapped_fields(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        before_audit_count = audit_count(client)
        batch = client.post("/api/import-batches", json={"source_name": "mapping-draft.xlsx"}).json()["data"]
        rows_payload = {
            "rows": [
                {
                    "case_code": "CASE-MAP-001",
                    "title": "Mapping preview only",
                    "amount": "12000",
                    "payment_month": "2026-07",
                    "payment_amount": "3000",
                    "contract_id": "CON-REF-001",
                    "file_name": "contract.pdf",
                    "free_text_note": "must remain visible",
                },
                {
                    "合約編號": "CON-MAP-001",
                    "合約金額": "90000",
                    "PDF類型": "contract",
                    "contract_name": "Mapped contract",
                    "filename": "contract-alias.pdf",
                    "unknown_column": "not mapped",
                },
            ]
        }
        staged = client.post(f"/api/import-batches/{batch['id']}/rows", json=rows_payload)
        assert staged.status_code == 201
        after_stage_dashboard = client.get("/api/dashboard").json()["data"]
        assert after_stage_dashboard["counts"] == before_dashboard["counts"]

        preview_response = client.get(f"/api/import-batches/{batch['id']}/mapping-preview")
        assert preview_response.status_code == 200
        preview = preview_response.json()["data"]
        assert preview["batch"]["id"] == batch["id"]
        assert preview["row_count"] == 2

        first_row = preview["rows"][0]
        candidates = {(item["source_field"], item["target_table"], item["target_field"]): item for item in first_row["candidates"]}
        assert candidates[("case_code", "cases", "case_code")]["requires_confirmation"] is False
        assert candidates[("title", "cases", "title")]["requires_confirmation"] is False
        for key in [
            ("amount", "cases", "amount"),
            ("payment_month", "payments", "payment_month"),
            ("payment_amount", "payments", "payment_amount"),
            ("contract_id", "payments", "contract_id"),
            ("file_name", "documents", "file_name"),
        ]:
            assert candidates[key]["requires_confirmation"] is True
        assert first_row["unmapped_fields"] == [
            {"source_field": "free_text_note", "value": "must remain visible"}
        ]

        second_row = preview["rows"][1]
        assert {
            (item["source_field"], item["target_table"], item["target_field"], item["requires_confirmation"])
            for item in second_row["candidates"]
        } >= {
            ("合約編號", "contracts", "contract_code", False),
            ("合約金額", "contracts", "amount", True),
            ("PDF類型", "documents", "document_type", True),
        }
        assert second_row["unmapped_fields"] == [{"source_field": "unknown_column", "value": "not mapped"}]

        after_preview_dashboard = client.get("/api/dashboard").json()["data"]
        assert after_preview_dashboard["counts"] == before_dashboard["counts"]
        assert audit_count(client) == before_audit_count + 2


def test_import_mapping_draft_catalog_is_read_only(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        before_audit_count = audit_count(client)

        response = client.get("/api/import-mapping-draft")
        assert response.status_code == 200
        catalog = response.json()["data"]

        assert catalog["field_count"] >= 10
        assert catalog["requires_confirmation_count"] >= 1
        expected_target_tables = {
            "cases": 1,
            "contracts": 1,
            "payments": 1,
            "documents": 1,
        }
        for table, minimum_count in expected_target_tables.items():
            assert catalog["target_tables"][table] >= minimum_count
        fields = {(item["source_field"], item["target_table"], item["target_field"]): item for item in catalog["fields"]}
        assert fields[("case_code", "cases", "case_code")]["requires_confirmation"] is False
        assert fields[("payment_amount", "payments", "payment_amount")]["requires_confirmation"] is True
        assert "案件編號" in fields[("case_code", "cases", "case_code")]["aliases"]

        after_dashboard = client.get("/api/dashboard").json()["data"]
        assert after_dashboard["counts"] == before_dashboard["counts"]
        assert audit_count(client) == before_audit_count


def test_import_mapping_preview_returns_validation_warnings(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "warnings.xlsx"}).json()["data"]
        rows_payload = {
            "rows": [
                {
                    "case_code": "CASE-DUP",
                    "amount": "abc",
                    "payment_month": "202607",
                    "payment_amount": "12,000",
                },
                {
                    "case_code": "CASE-DUP",
                    "title": "Duplicate case",
                    "payment_month": "2026-13",
                    "payment_amount": "0",
                },
            ]
        }
        staged = client.post(f"/api/import-batches/{batch['id']}/rows", json=rows_payload)
        assert staged.status_code == 201

        before_preview_audit_count = audit_count(client)
        preview_response = client.get(f"/api/import-batches/{batch['id']}/mapping-preview")
        assert preview_response.status_code == 200
        preview = preview_response.json()["data"]
        warnings = [
            warning
            for row in preview["rows"]
            for warning in row["warnings"]
        ]

        summary = preview["summary"]
        assert summary["warning_count"] >= 1
        assert summary["error_count"] >= 1
        expected_warning_counts = {
            "missing_required": 1,
            "invalid_amount": 1,
            "invalid_month": 1,
            "duplicate_in_batch": 1,
        }
        for code, minimum_count in expected_warning_counts.items():
            assert summary["warning_by_code"][code] >= minimum_count
        assert {warning["code"] for warning in warnings} >= {
            "missing_required",
            "invalid_amount",
            "invalid_month",
            "duplicate_in_batch",
        }
        assert warnings[0].keys() >= {
            "code",
            "severity",
            "message",
            "source_field",
            "target_table",
            "target_field",
            "row_number",
        }
        assert any(
            warning["code"] == "duplicate_in_batch"
            and warning["source_field"] == "case_code"
            and warning["related_row_numbers"]
            for warning in warnings
        )
        assert not any(
            warning["code"] == "invalid_amount"
            and warning["source_field"] == "payment_amount"
            and warning.get("value") == "12,000"
            for warning in warnings
        )

        after_preview_dashboard = client.get("/api/dashboard").json()["data"]
        assert after_preview_dashboard["counts"] == before_dashboard["counts"]
        assert audit_count(client) == before_preview_audit_count


def test_import_confirm_cases_dry_run_is_read_only_and_returns_plan(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-confirm.csv"}).json()["data"]
        staged = client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-CONFIRM-001",
                        "title": "Dry-run case",
                        "owner": "Ops",
                        "amount": "12000",
                    }
                ]
            },
        )
        assert staged.status_code == 201
        before_confirm_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["dry_run"] is True
        assert data["target_tables"] == ["cases"]
        assert data["summary"]["planned_create_count"] == 1
        assert data["plan"]["cases"] == [
            {
                "action": "create",
                "target_table": "cases",
                "row_number": 1,
                "source_row_id": staged.json()["data"][0]["id"],
                "record": {
                    "case_code": "CASE-CONFIRM-001",
                    "title": "Dry-run case",
                    "owner": "Ops",
                    "amount": "12000",
                },
            }
        ]
        assert client.get("/api/dashboard").json()["data"]["counts"] == before_dashboard["counts"]
        assert client.get("/api/cases").json()["data"] == []
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_cases_dry_run_preserves_plan_source_chain_for_multiple_rows(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-confirm-source-chain.csv"}).json()["data"]
        staged = client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-CONFIRM-SOURCE-001",
                        "title": "First dry-run source",
                        "owner": "Ops",
                        "amount": "12000",
                    },
                    {
                        "case_code": "CASE-CONFIRM-SOURCE-002",
                        "title": "Second dry-run source",
                        "owner": "Finance",
                        "amount": "22000",
                    },
                ]
            },
        )
        assert staged.status_code == 201
        staged_rows = staged.json()["data"]
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_confirm_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"},
                    {"row_number": 2, "target_table": "cases", "target_field": "amount"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        planned_cases = data["plan"]["cases"]

        assert data["summary"]["planned_create_count"] == 2
        assert [case["row_number"] for case in planned_cases] == [1, 2]
        assert [case["source_row_id"] for case in planned_cases] == [
            staged_rows[0]["id"],
            staged_rows[1]["id"],
        ]
        assert all(case["action"] == "create" and case["target_table"] == "cases" for case in planned_cases)
        assert [case["record"]["case_code"] for case in planned_cases] == [
            "CASE-CONFIRM-SOURCE-001",
            "CASE-CONFIRM-SOURCE-002",
        ]
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_cases_dry_run_accepted_warnings_do_not_change_plan(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-confirm-accepted-warning-plan.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-CONFIRM-ACCEPTED-PLAN",
                        "title": "Accepted warning dry-run plan",
                        "owner": "Ops",
                        "amount": "12000",
                    }
                ]
            },
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_confirm_audit_count = audit_count(client)
        confirmed_fields = [
            {"row_number": 1, "target_table": "cases", "target_field": "amount"}
        ]

        baseline = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={"dry_run": True, "target_tables": ["cases"], "confirmed_fields": confirmed_fields},
        )
        accepted = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "accepted_warning_codes": ["unknown_policy_code"],
                "confirmed_fields": confirmed_fields,
            },
        )

        assert baseline.status_code == 200
        assert accepted.status_code == 200
        assert accepted.json()["data"] == baseline.json()["data"]
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_cases_dry_run_duplicate_confirmations_do_not_change_plan(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-confirm-duplicate-confirmations.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-DUPLICATE-CONFIRMATION",
                        "title": "Duplicate confirmation dry-run",
                        "owner": "Ops",
                        "amount": "12000",
                    }
                ]
            },
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_confirm_audit_count = audit_count(client)
        confirmed_field = {"row_number": 1, "target_table": "cases", "target_field": "amount"}

        single_response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={"dry_run": True, "target_tables": ["cases"], "confirmed_fields": [confirmed_field]},
        )
        duplicate_response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "confirmed_fields": [confirmed_field, confirmed_field],
            },
        )

        assert single_response.status_code == 200
        assert duplicate_response.status_code == 200
        assert duplicate_response.json()["data"] == single_response.json()["data"]
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_formal_write_stays_blocked_for_clean_case_batch(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-formal-blocked.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-FORMAL-BLOCKED-001",
                        "title": "Formal write remains blocked",
                        "owner": "Ops",
                        "amount": "12000",
                    }
                ]
            },
        )
        before_confirm_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={
                "dry_run": False,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
                ],
            },
        )

        assert response.status_code == 400
        assert "dry_run=true" in response.json()["detail"]
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_formal_write_stays_blocked_for_multi_row_case_batch(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-formal-multi-blocked.csv"}).json()["data"]
        staged = client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-FORMAL-MULTI-BLOCKED-001",
                        "title": "Formal multi write blocked one",
                        "owner": "Ops",
                        "amount": "12000",
                    },
                    {
                        "case_code": "CASE-FORMAL-MULTI-BLOCKED-002",
                        "title": "Formal multi write blocked two",
                        "owner": "Finance",
                        "amount": "22000",
                    },
                ]
            },
        )
        assert staged.status_code == 201
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_confirm_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={
                "dry_run": False,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"},
                    {"row_number": 2, "target_table": "cases", "target_field": "amount"},
                ],
            },
        )

        assert response.status_code == 400
        assert "dry_run=true" in response.json()["detail"]
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_preflight_is_read_only_and_reports_blocking_gates(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-preflight.csv"}).json()["data"]
        staged = client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-PREFLIGHT-001",
                        "title": "Preflight case",
                        "amount": "12000",
                    }
                ]
            },
        )
        assert staged.status_code == 201
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_preflight_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={
                "dry_run": False,
                "target_tables": ["cases"],
                "accepted_warning_codes": ["invalid_amount"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        gates = {gate["code"]: gate for gate in data["gates"]}

        assert data["mode"] == "preflight"
        assert data["dry_run_supported"] is True
        assert data["formal_write_allowed"] is False
        assert data["target_tables"] == ["cases"]
        assert data["mapping_version"] == "draft-v1"
        assert data["next_allowed_action"] == "run_cases_dry_run"
        assert data["freshness"]["strategy"] == "server_preview_fingerprint"
        assert data["freshness"]["mapping_version"] == "draft-v1"
        assert data["freshness"]["server_preview_rerun"] is True
        assert len(data["freshness"]["fingerprint"]) == 64
        assert data["accepted_warning_policy"] == {
            "status": "disabled",
            "allowed_warning_codes": [],
            "non_bypassable_gates": [
                "preview_errors",
                "duplicate_in_batch",
                "existing_case_code",
                "requires_confirmation",
                "source_chain_contract",
                "stale_preview_guard",
            ],
            "reason": "No formal allowlist policy exists yet; accepted_warning_codes cannot enable writes or bypass safety gates.",
        }
        assert data["preview"]["batch"]["id"] == batch["id"]
        assert gates["formal_write_disabled"]["status"] == "blocked"
        assert gates["source_chain_contract"]["status"] == "blocked"
        assert gates["stale_preview_guard"]["status"] == "blocked"
        assert gates["accepted_warning_codes_policy"]["status"] == "blocked"
        assert gates["accepted_warning_codes_policy"]["evidence"]["accepted_warning_codes"] == ["invalid_amount"]
        assert gates["preview_errors"]["status"] == "pass"
        assert gates["requires_confirmation"]["status"] == "pass"
        assert {"batch_id", "import_row_id", "row_number", "mapping_version", "actor"} <= set(
            data["source_chain_requirements"]
        )
        assert data["summary"]["blocked_gate_count"] >= 4
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_preflight_audit_count


def test_import_confirm_preflight_source_chain_requirements_are_stable(tmp_path):
    with client_for(tmp_path) as client:
        created = client.post(
            "/api/cases",
            json={"case_code": "CASE-SOURCE-CHAIN-EXISTS", "title": "Existing source-chain case"},
        )
        assert created.status_code == 201
        expected_requirements = [
            "batch_id",
            "import_row_id",
            "row_number",
            "source_fields",
            "target_fields",
            "mapping_version",
            "actor",
            "server_preview_rerun",
        ]
        clean_batch = client.post("/api/import-batches", json={"source_name": "cases-source-chain-clean.csv"}).json()["data"]
        conflict_batch = client.post("/api/import-batches", json={"source_name": "cases-source-chain-conflict.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{clean_batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-SOURCE-CHAIN-CLEAN", "title": "Clean source chain", "amount": "12000"}]},
        )
        client.post(
            f"/api/import-batches/{conflict_batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-SOURCE-CHAIN-EXISTS", "title": "Conflict source chain", "amount": "12000"}]},
        )
        before_clean_rows = client.get(f"/api/import-batches/{clean_batch['id']}/rows").json()["data"]
        before_conflict_rows = client.get(f"/api/import-batches/{conflict_batch['id']}/rows").json()["data"]
        before_preflight_audit_count = audit_count(client)

        clean = client.post(
            f"/api/import-batches/{clean_batch['id']}/confirm-preflight",
            json={
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
                ],
            },
        )
        conflict = client.post(
            f"/api/import-batches/{conflict_batch['id']}/confirm-preflight",
            json={
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
                ],
            },
        )

        assert clean.status_code == 200
        assert conflict.status_code == 200
        clean_data = clean.json()["data"]
        conflict_data = conflict.json()["data"]
        assert clean_data["source_chain_requirements"] == expected_requirements
        assert conflict_data["source_chain_requirements"] == expected_requirements
        assert clean_data["summary"]["blocked_gate_count"] == sum(
            1 for gate in clean_data["gates"] if gate["status"] == "blocked"
        )
        assert conflict_data["summary"]["blocked_gate_count"] == sum(
            1 for gate in conflict_data["gates"] if gate["status"] == "blocked"
        )
        assert {gate["code"]: gate["status"] for gate in clean_data["gates"]}["source_chain_contract"] == "blocked"
        assert {gate["code"]: gate["status"] for gate in conflict_data["gates"]}["source_chain_contract"] == "blocked"
        assert conflict_data["summary"]["existing_case_conflict_count"] == 1
        assert client.get(f"/api/import-batches/{clean_batch['id']}/rows").json()["data"] == before_clean_rows
        assert client.get(f"/api/import-batches/{conflict_batch['id']}/rows").json()["data"] == before_conflict_rows
        assert audit_count(client) == before_preflight_audit_count


def test_import_confirm_preflight_fingerprint_is_stable_and_changes_with_rows(tmp_path):
    with client_for(tmp_path) as client:
        batch = client.post("/api/import-batches", json={"source_name": "cases-fingerprint.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-FINGERPRINT-001",
                        "title": "Fingerprint case",
                        "amount": "12000",
                    }
                ]
            },
        )
        before_preflight_audit_count = audit_count(client)

        first = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
                ],
            },
        ).json()["data"]["freshness"]["fingerprint"]
        second = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
                ],
            },
        ).json()["data"]["freshness"]["fingerprint"]

        assert first == second
        assert audit_count(client) == before_preflight_audit_count

        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-FINGERPRINT-002", "title": "Changed batch"}]},
        )
        changed = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
                ],
            },
        ).json()["data"]["freshness"]["fingerprint"]

        assert changed != first


def test_import_confirm_preflight_accepted_warnings_do_not_change_gate_statuses(tmp_path):
    with client_for(tmp_path) as client:
        batch = client.post("/api/import-batches", json={"source_name": "cases-preflight-accepted.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-PREFLIGHT-ACCEPTED",
                        "title": "Accepted warnings stay blocked",
                        "amount": "12000",
                    }
                ]
            },
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_preflight_audit_count = audit_count(client)
        confirmed_fields = [
            {"row_number": 1, "target_table": "cases", "target_field": "amount"}
        ]

        baseline = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={"target_tables": ["cases"], "confirmed_fields": confirmed_fields},
        )
        accepted = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={
                "target_tables": ["cases"],
                "accepted_warning_codes": [
                    "duplicate_in_batch",
                    "preview_errors",
                    "requires_confirmation",
                    "source_chain_contract",
                ],
                "confirmed_fields": confirmed_fields,
            },
        )

        assert baseline.status_code == 200
        assert accepted.status_code == 200
        baseline_data = baseline.json()["data"]
        accepted_data = accepted.json()["data"]
        baseline_gate_statuses = {
            gate["code"]: gate["status"]
            for gate in baseline_data["gates"]
        }
        accepted_gate_statuses = {
            gate["code"]: gate["status"]
            for gate in accepted_data["gates"]
        }
        accepted_gates = {
            gate["code"]: gate
            for gate in accepted_data["gates"]
        }

        assert accepted_data["formal_write_allowed"] is False
        assert baseline_gate_statuses == accepted_gate_statuses
        assert accepted_gates["accepted_warning_codes_policy"]["status"] == "blocked"
        assert accepted_gates["accepted_warning_codes_policy"]["evidence"]["accepted_warning_codes"] == [
            "duplicate_in_batch",
            "preview_errors",
            "requires_confirmation",
            "source_chain_contract",
        ]
        assert accepted_data["accepted_warning_policy"]["status"] == "disabled"
        assert accepted_data["accepted_warning_policy"]["allowed_warning_codes"] == []
        assert accepted_data["freshness"] == baseline_data["freshness"]
        assert accepted_data["preview"] == baseline_data["preview"]
        assert accepted_data["summary"]["blocked_gate_count"] == baseline_data["summary"]["blocked_gate_count"]
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_preflight_audit_count
        assert client.get("/api/cases").json()["data"] == []


def test_import_confirm_preflight_unknown_accepted_warnings_do_not_bypass_gates(tmp_path):
    with client_for(tmp_path) as client:
        batch = client.post("/api/import-batches", json={"source_name": "cases-preflight-unknown-accepted.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-PREFLIGHT-UNKNOWN-ACCEPTED",
                        "title": "Unknown accepted warning stays blocked",
                        "amount": "12000",
                    }
                ]
            },
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_preflight_audit_count = audit_count(client)
        confirmed_fields = [
            {"row_number": 1, "target_table": "cases", "target_field": "amount"}
        ]

        baseline = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={"target_tables": ["cases"], "confirmed_fields": confirmed_fields},
        )
        unknown_accepted = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={
                "target_tables": ["cases"],
                "accepted_warning_codes": ["unknown_policy_code"],
                "confirmed_fields": confirmed_fields,
            },
        )

        assert baseline.status_code == 200
        assert unknown_accepted.status_code == 200
        baseline_data = baseline.json()["data"]
        unknown_data = unknown_accepted.json()["data"]
        unknown_gates = {gate["code"]: gate for gate in unknown_data["gates"]}
        assert unknown_data["formal_write_allowed"] is False
        assert {
            gate["code"]: gate["status"]
            for gate in unknown_data["gates"]
        } == {
            gate["code"]: gate["status"]
            for gate in baseline_data["gates"]
        }
        assert unknown_gates["accepted_warning_codes_policy"]["status"] == "blocked"
        assert unknown_gates["accepted_warning_codes_policy"]["evidence"]["accepted_warning_codes"] == [
            "unknown_policy_code"
        ]
        assert unknown_data["accepted_warning_policy"]["status"] == "disabled"
        assert unknown_data["accepted_warning_policy"]["allowed_warning_codes"] == []
        assert unknown_data["freshness"] == baseline_data["freshness"]
        assert unknown_data["preview"] == baseline_data["preview"]
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_preflight_audit_count
        assert client.get("/api/cases").json()["data"] == []


def test_import_confirm_preflight_duplicate_confirmations_do_not_change_gate_report(tmp_path):
    with client_for(tmp_path) as client:
        batch = client.post("/api/import-batches", json={"source_name": "cases-preflight-duplicate-confirmations.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-PREFLIGHT-DUPLICATE-CONFIRMATION",
                        "title": "Duplicate confirmation preflight",
                        "amount": "12000",
                    }
                ]
            },
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_preflight_audit_count = audit_count(client)
        confirmed_field = {"row_number": 1, "target_table": "cases", "target_field": "amount"}

        single_response = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={"target_tables": ["cases"], "confirmed_fields": [confirmed_field]},
        )
        duplicate_response = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={
                "target_tables": ["cases"],
                "confirmed_fields": [confirmed_field, confirmed_field],
            },
        )

        assert single_response.status_code == 200
        assert duplicate_response.status_code == 200
        assert duplicate_response.json()["data"] == single_response.json()["data"]
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_preflight_audit_count
        assert client.get("/api/cases").json()["data"] == []
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_preflight_dry_run_flag_does_not_change_gate_statuses(tmp_path):
    with client_for(tmp_path) as client:
        batch = client.post("/api/import-batches", json={"source_name": "cases-preflight-dry-run-flag.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {
                        "case_code": "CASE-PREFLIGHT-DRY-RUN-FLAG",
                        "title": "Preflight ignores write flag",
                        "amount": "12000",
                    }
                ]
            },
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_preflight_audit_count = audit_count(client)
        confirmed_fields = [
            {"row_number": 1, "target_table": "cases", "target_field": "amount"}
        ]

        dry_run_preflight = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={"dry_run": True, "target_tables": ["cases"], "confirmed_fields": confirmed_fields},
        )
        write_flag_preflight = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={"dry_run": False, "target_tables": ["cases"], "confirmed_fields": confirmed_fields},
        )

        assert dry_run_preflight.status_code == 200
        assert write_flag_preflight.status_code == 200
        dry_run_data = dry_run_preflight.json()["data"]
        write_flag_data = write_flag_preflight.json()["data"]
        assert dry_run_data["formal_write_allowed"] is False
        assert write_flag_data["formal_write_allowed"] is False
        assert dry_run_data["dry_run_supported"] is True
        assert write_flag_data["dry_run_supported"] is True
        assert {
            gate["code"]: gate["status"]
            for gate in write_flag_data["gates"]
        } == {
            gate["code"]: gate["status"]
            for gate in dry_run_data["gates"]
        }
        assert write_flag_data["freshness"] == dry_run_data["freshness"]
        assert write_flag_data["preview"] == dry_run_data["preview"]
        assert write_flag_data["summary"]["blocked_gate_count"] == dry_run_data["summary"]["blocked_gate_count"]
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_preflight_audit_count
        assert client.get("/api/cases").json()["data"] == []


def test_import_confirm_preflight_reports_validation_conflicts_without_writing(tmp_path):
    with client_for(tmp_path) as client:
        created = client.post(
            "/api/cases",
            json={"case_code": "CASE-PREFLIGHT-EXISTS", "title": "Existing case"},
        )
        assert created.status_code == 201
        before_dashboard = client.get("/api/dashboard").json()["data"]
        before_preflight_audit_count = audit_count(client)

        batch = client.post("/api/import-batches", json={"source_name": "cases-preflight-blocked.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {"case_code": "CASE-PREFLIGHT-EXISTS", "amount": "abc"},
                    {"case_code": "CASE-PREFLIGHT-EXISTS", "title": "Duplicate row", "amount": "300"},
                ]
            },
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        after_stage_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={"dry_run": True, "target_tables": ["cases"], "confirmed_fields": []},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        gates = {gate["code"]: gate for gate in data["gates"]}

        assert data["formal_write_allowed"] is False
        assert gates["preview_errors"]["status"] == "blocked"
        assert gates["duplicate_in_batch"]["status"] == "blocked"
        assert gates["existing_case_code"]["status"] == "blocked"
        assert gates["requires_confirmation"]["status"] == "blocked"
        assert gates["accepted_warning_codes_policy"]["status"] == "blocked"
        assert gates["accepted_warning_codes_policy"]["evidence"]["accepted_warning_codes"] == []
        assert data["summary"]["existing_case_conflict_count"] == 2
        assert data["summary"]["missing_confirmation_count"] == 2
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert len(client.get("/api/cases").json()["data"]) == 1
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == after_stage_audit_count
        assert audit_count(client) == before_preflight_audit_count + 2
        assert audit_count(client, table_name="cases", action="create") == 1


def test_import_confirm_cases_dry_run_blocks_preview_errors(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-errors.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-BAD-AMOUNT", "title": "Bad amount", "amount": "abc"}]},
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_confirm_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
                ],
            },
        )

        assert response.status_code == 422
        assert "mapping preview contains error warnings" in response.json()["detail"]
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_cases_dry_run_requires_explicit_confirmation(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-confirm-required.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-NEEDS-CONFIRM", "title": "Needs confirm", "amount": "900"}]},
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_confirm_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={"dry_run": True, "target_tables": ["cases"], "confirmed_fields": []},
        )

        assert response.status_code == 422
        assert "requires_confirmation fields" in response.json()["detail"]
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_cases_dry_run_rejects_cross_table_confirmation_fields(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-cross-table-confirmation.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-CROSS-TABLE-CONFIRM", "title": "Cross table confirm", "amount": "900"}]},
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_confirm_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "contracts", "target_field": "amount"}
                ],
            },
        )

        assert response.status_code == 422
        assert "requires_confirmation fields" in response.json()["detail"]
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_cases_dry_run_rejects_wrong_target_field_confirmation(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-wrong-field-confirmation.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-WRONG-FIELD-CONFIRM", "title": "Wrong field confirm", "amount": "900"}]},
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_confirm_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "title"}
                ],
            },
        )

        assert response.status_code == 422
        assert "requires_confirmation fields" in response.json()["detail"]
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_cases_dry_run_rejects_wrong_row_confirmation(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-wrong-row-confirmation.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {"case_code": "CASE-WRONG-ROW-CONFIRM-1", "title": "Wrong row one", "amount": "900"},
                    {"case_code": "CASE-WRONG-ROW-CONFIRM-2", "title": "Wrong row two", "amount": "1200"},
                ]
            },
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_confirm_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 2, "target_table": "cases", "target_field": "amount"}
                ],
            },
        )

        assert response.status_code == 422
        assert "requires_confirmation fields" in response.json()["detail"]
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_preflight_rejects_cross_table_confirmation_fields(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-preflight-cross-table-confirmation.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-PREFLIGHT-CROSS-TABLE", "title": "Cross table preflight", "amount": "900"}]},
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_preflight_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "contracts", "target_field": "amount"}
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        gates = {gate["code"]: gate for gate in data["gates"]}
        assert data["formal_write_allowed"] is False
        assert gates["requires_confirmation"]["status"] == "blocked"
        assert gates["requires_confirmation"]["evidence"]["missing"] == [
            {
                "row_number": 1,
                "target_table": "cases",
                "target_field": "amount",
                "source_field": "amount",
            }
        ]
        assert data["summary"]["missing_confirmation_count"] == 1
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_preflight_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_preflight_rejects_wrong_target_field_confirmation(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-preflight-wrong-field-confirmation.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-PREFLIGHT-WRONG-FIELD", "title": "Wrong field preflight", "amount": "900"}]},
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_preflight_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "title"}
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        gates = {gate["code"]: gate for gate in data["gates"]}
        assert data["formal_write_allowed"] is False
        assert gates["requires_confirmation"]["status"] == "blocked"
        assert gates["requires_confirmation"]["evidence"]["missing"] == [
            {
                "row_number": 1,
                "target_table": "cases",
                "target_field": "amount",
                "source_field": "amount",
            }
        ]
        assert data["summary"]["missing_confirmation_count"] == 1
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_preflight_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_preflight_rejects_wrong_row_confirmation(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-preflight-wrong-row-confirmation.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {"case_code": "CASE-PREFLIGHT-WRONG-ROW-1", "title": "Wrong row one", "amount": "900"},
                    {"case_code": "CASE-PREFLIGHT-WRONG-ROW-2", "title": "Wrong row two", "amount": "1200"},
                ]
            },
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_preflight_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "confirmed_fields": [
                    {"row_number": 2, "target_table": "cases", "target_field": "amount"}
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        gates = {gate["code"]: gate for gate in data["gates"]}
        assert data["formal_write_allowed"] is False
        assert gates["requires_confirmation"]["status"] == "blocked"
        assert gates["requires_confirmation"]["evidence"]["missing"] == [
            {
                "row_number": 1,
                "target_table": "cases",
                "target_field": "amount",
                "source_field": "amount",
            }
        ]
        assert data["summary"]["missing_confirmation_count"] == 1
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_preflight_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_cases_dry_run_blocks_duplicate_batch_without_mutation(tmp_path):
    with client_for(tmp_path) as client:
        before_dashboard = client.get("/api/dashboard").json()["data"]
        batch = client.post("/api/import-batches", json={"source_name": "cases-duplicate-confirm.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={
                "rows": [
                    {"case_code": "CASE-DUP-CONFIRM", "title": "Duplicate one"},
                    {"case_code": "CASE-DUP-CONFIRM", "title": "Duplicate two"},
                ]
            },
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_confirm_audit_count = audit_count(client)

        response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={"dry_run": True, "target_tables": ["cases"], "confirmed_fields": []},
        )

        assert response.status_code == 409
        assert "duplicate cases.case_code" in response.json()["detail"]
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_confirm_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


def test_import_confirm_accepted_warning_codes_do_not_bypass_error_or_confirmation_gates(tmp_path):
    with client_for(tmp_path) as client:
        error_batch = client.post("/api/import-batches", json={"source_name": "accepted-warning-errors.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{error_batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-ACCEPTED-ERROR", "title": "Bad amount", "amount": "abc"}]},
        )
        before_error_audit_count = audit_count(client)

        error_response = client.post(
            f"/api/import-batches/{error_batch['id']}/confirm",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "accepted_warning_codes": ["invalid_amount"],
                "confirmed_fields": [
                    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
                ],
            },
        )

        assert error_response.status_code == 422
        assert "mapping preview contains error warnings" in error_response.json()["detail"]
        assert audit_count(client) == before_error_audit_count

        confirmation_batch = client.post(
            "/api/import-batches",
            json={"source_name": "accepted-warning-confirmation.csv"},
        ).json()["data"]
        client.post(
            f"/api/import-batches/{confirmation_batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-ACCEPTED-CONFIRM", "title": "Needs confirm", "amount": "900"}]},
        )
        before_confirmation_audit_count = audit_count(client)

        confirmation_response = client.post(
            f"/api/import-batches/{confirmation_batch['id']}/confirm",
            json={
                "dry_run": True,
                "target_tables": ["cases"],
                "accepted_warning_codes": ["requires_confirmation"],
                "confirmed_fields": [],
            },
        )

        assert confirmation_response.status_code == 422
        assert "requires_confirmation fields" in confirmation_response.json()["detail"]
        assert audit_count(client) == before_confirmation_audit_count
        assert client.get("/api/cases").json()["data"] == []


def test_import_confirm_cases_dry_run_blocks_existing_case_code_replay(tmp_path):
    with client_for(tmp_path) as client:
        created = client.post(
            "/api/cases",
            json={"case_code": "CASE-EXISTS", "title": "Already exists"},
        )
        assert created.status_code == 201
        before_dashboard = client.get("/api/dashboard").json()["data"]
        before_confirm_audit_count = audit_count(client)

        batch = client.post("/api/import-batches", json={"source_name": "case-replay.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-EXISTS", "title": "Replay should block"}]},
        )
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        after_stage_audit_count = audit_count(client)

        first_response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={"dry_run": True, "target_tables": ["cases"], "confirmed_fields": []},
        )
        second_response = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={"dry_run": False, "target_tables": ["cases"], "confirmed_fields": []},
        )

        assert first_response.status_code == 409
        assert "case_code already exists" in first_response.json()["detail"]
        assert second_response.status_code == 400
        assert "dry_run=true" in second_response.json()["detail"]
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert len(client.get("/api/cases").json()["data"]) == 1
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == after_stage_audit_count
        assert audit_count(client) == before_confirm_audit_count + 2
        assert audit_count(client, table_name="cases", action="create") == 1


def test_import_confirm_rejects_unsupported_modes_and_target_tables(tmp_path):
    with client_for(tmp_path) as client:
        batch = client.post("/api/import-batches", json={"source_name": "unsupported-confirm.csv"}).json()["data"]
        client.post(
            f"/api/import-batches/{batch['id']}/rows",
            json={"rows": [{"case_code": "CASE-UNSUPPORTED", "title": "Unsupported target"}]},
        )
        before_dashboard = client.get("/api/dashboard").json()["data"]
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        before_error_audit_count = audit_count(client)

        unsupported_table = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={"dry_run": True, "target_tables": ["contracts"], "confirmed_fields": []},
        )
        assert unsupported_table.status_code == 400
        assert 'target_tables=["cases"]' in unsupported_table.json()["detail"]

        unsupported_preflight_table = client.post(
            f"/api/import-batches/{batch['id']}/confirm-preflight",
            json={"dry_run": True, "target_tables": ["contracts"], "confirmed_fields": []},
        )
        assert unsupported_preflight_table.status_code == 400
        assert 'target_tables=["cases"]' in unsupported_preflight_table.json()["detail"]

        formal_confirm = client.post(
            f"/api/import-batches/{batch['id']}/confirm",
            json={"dry_run": False, "target_tables": ["cases"], "confirmed_fields": []},
        )
        assert formal_confirm.status_code == 400
        assert "dry_run=true" in formal_confirm.json()["detail"]
        assert client.get("/api/dashboard").json()["data"] == before_dashboard
        assert client.get("/api/cases").json()["data"] == []
        assert client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"] == before_rows
        assert audit_count(client) == before_error_audit_count
        assert audit_count(client, table_name="cases", action="create") == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"rows": []},
        {"rows": {"case_code": "not-a-list"}},
        {"rows": ["not-an-object"]},
    ],
)
def test_import_rows_rejects_invalid_payloads(tmp_path, payload):
    with client_for(tmp_path) as client:
        batch = client.post("/api/import-batches", json={"source_name": "bad-input.csv"}).json()["data"]
        before_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]

        response = client.post(f"/api/import-batches/{batch['id']}/rows", json=payload)
        assert response.status_code == 422

        after_rows = client.get(f"/api/import-batches/{batch['id']}/rows").json()["data"]
        assert after_rows == before_rows
