from fastapi import APIRouter

from app.db.session import db_session
from app.repositories.sqlite_repository import rows_to_dicts


router = APIRouter()


@router.get("")
def search(q: str, limit: int = 50) -> dict:
    like = f"%{q}%"
    with db_session() as conn:
        items = conn.execute(
            """
            SELECT 'cost_contract_item' AS result_type, id, cost_item_name AS title, vendor_name AS subtitle, status
            FROM cost_contract_items
            WHERE cost_item_name LIKE ? OR vendor_name LIKE ? OR cost_item_code LIKE ?
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()
        cases = conn.execute(
            """
            SELECT 'signing_case' AS result_type, id, title, category AS subtitle, status
            FROM signing_cases
            WHERE title LIKE ? OR category LIKE ? OR case_code LIKE ? OR vendor_name LIKE ?
               OR owner_department LIKE ? OR owner_user LIKE ? OR source_file_name LIKE ?
               OR cmdb_ci_id LIKE ? OR cmdb_system_name LIKE ? OR cmdb_service_name LIKE ?
            LIMIT ?
            """,
            (like, like, like, like, like, like, like, like, like, like, limit),
        ).fetchall()
        contracts = conn.execute(
            """
            SELECT 'contract' AS result_type, id, contract_name AS title, vendor_name AS subtitle, status
            FROM contracts
            WHERE contract_name LIKE ? OR vendor_name LIKE ? OR contract_code LIKE ?
               OR signing_case_id LIKE ? OR procurement_no LIKE ? OR cmdb_ci_id LIKE ?
               OR cmdb_system_name LIKE ? OR cmdb_service_name LIKE ?
            LIMIT ?
            """,
            (like, like, like, like, like, like, like, like, limit),
        ).fetchall()
        payments = conn.execute(
            """
            SELECT 'payment' AS result_type, id, payment_month AS title, vendor_name AS subtitle, status
            FROM payment_schedules
            WHERE payment_month LIKE ? OR invoice_status LIKE ? OR payment_phase LIKE ?
               OR payment_condition LIKE ? OR vendor_name LIKE ? OR source_file_name LIKE ?
            LIMIT ?
            """,
            (like, like, like, like, like, like, limit),
        ).fetchall()
        invoices = conn.execute(
            """
            SELECT 'invoice' AS result_type, id, COALESCE(invoice_no, invoice_month, '發票') AS title,
                   vendor_name AS subtitle, status
            FROM invoices
            WHERE invoice_no LIKE ? OR vendor_name LIKE ? OR invoice_month LIKE ? OR source_file_name LIKE ?
            LIMIT ?
            """,
            (like, like, like, like, limit),
        ).fetchall()
        documents = conn.execute(
            """
            SELECT 'document' AS result_type, id, file_name AS title, document_type AS subtitle, parse_status AS status
            FROM documents
            WHERE file_name LIKE ? OR document_type LIKE ? OR source_note LIKE ? OR evidence_text LIKE ?
            LIMIT ?
            """,
            (like, like, like, like, limit),
        ).fetchall()
        todos = conn.execute(
            """
            SELECT 'todo' AS result_type, id, title, owner_user AS subtitle, status
            FROM todos
            WHERE title LIKE ? OR owner_user LIKE ? OR owner_department LIKE ? OR task_type LIKE ?
            LIMIT ?
            """,
            (like, like, like, like, limit),
        ).fetchall()
        issues = conn.execute(
            """
            SELECT 'data_quality_issue' AS result_type, id, rule_code AS title, message AS subtitle, status
            FROM data_quality_issues
            WHERE rule_code LIKE ? OR message LIKE ? OR source_file_name LIKE ? OR original_value LIKE ?
            LIMIT ?
            """,
            (like, like, like, like, limit),
        ).fetchall()
    return {
        "ok": True,
        "data": (
            rows_to_dicts(items)
            + rows_to_dicts(cases)
            + rows_to_dicts(contracts)
            + rows_to_dicts(payments)
            + rows_to_dicts(invoices)
            + rows_to_dicts(documents)
            + rows_to_dicts(todos)
            + rows_to_dicts(issues)
        ),
    }
