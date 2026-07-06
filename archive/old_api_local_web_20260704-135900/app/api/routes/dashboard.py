from fastapi import APIRouter

from app.db.session import db_session


router = APIRouter()


def _summary(role: str) -> dict:
    with db_session() as conn:
        item_count = conn.execute("SELECT COUNT(*) FROM cost_contract_items").fetchone()[0]
        case_count = conn.execute("SELECT COUNT(*) FROM signing_cases").fetchone()[0]
        contract_count = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
        payment_count = conn.execute("SELECT COUNT(*) FROM payment_schedules").fetchone()[0]
        invoice_count = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
        document_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        todo_count = conn.execute("SELECT COUNT(*) FROM todos WHERE status NOT IN ('done', 'closed', 'void')").fetchone()[0]
        reminder_count = conn.execute("SELECT COUNT(*) FROM reminders WHERE status NOT IN ('done', 'closed', 'void')").fetchone()[0]
        data_quality_count = conn.execute("SELECT COUNT(*) FROM data_quality_issues WHERE status NOT IN ('done', 'closed', 'void')").fetchone()[0]
        mapping_count = conn.execute("SELECT COUNT(*) FROM field_mappings").fetchone()[0]
        active_cases = conn.execute("SELECT COUNT(*) FROM signing_cases WHERE status != 'void'").fetchone()[0]
        unfinished_cases = conn.execute(
            "SELECT COUNT(*) FROM signing_cases WHERE LOWER(status) NOT IN ('done', 'completed', 'closed', 'void')"
        ).fetchone()[0]
        total_amount = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM signing_cases").fetchone()[0]
        payment_amount = conn.execute("SELECT COALESCE(SUM(payment_amount), 0) FROM payment_schedules").fetchone()[0]
        invoice_amount = conn.execute("SELECT COALESCE(SUM(invoice_amount), 0) FROM invoices").fetchone()[0]
    return {
        "role": role,
        "cards": {
            "cost_contract_items": item_count,
            "signing_cases": case_count,
            "contracts": contract_count,
            "payment_schedules": payment_count,
            "invoices": invoice_count,
            "documents": document_count,
            "todos": todo_count,
            "reminders": reminder_count,
            "data_quality_issues": data_quality_count,
            "field_mappings": mapping_count,
            "active_cases": active_cases,
            "unfinished_cases": unfinished_cases,
            "signing_amount": total_amount,
            "payment_amount": payment_amount,
            "invoice_amount": invoice_amount,
        },
        "drilldown": {
            "level_1": "dashboard_summary",
            "level_2": "filtered_list",
            "level_3": "case_history",
            "level_4": "source_reference",
        },
    }


@router.get("/executive")
def executive_dashboard() -> dict:
    return {"ok": True, "data": _summary("executive")}


@router.get("/manager")
def manager_dashboard() -> dict:
    return {"ok": True, "data": _summary("manager")}


@router.get("/assistant")
def assistant_dashboard() -> dict:
    return {"ok": True, "data": _summary("assistant")}


@router.get("/handler")
def handler_dashboard() -> dict:
    return {"ok": True, "data": _summary("handler")}
