from fastapi import APIRouter

from app.api.routes import (
    audit_logs,
    budget_lines,
    contracts,
    cost_contract_items,
    dashboard,
    data_quality_issues,
    documents,
    field_mappings,
    health,
    import_batches,
    invoices,
    payment_schedules,
    reminders,
    search,
    signing_cases,
    system_features,
    todos,
)


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
api_router.include_router(cost_contract_items.router, prefix="/api/cost-contract-items", tags=["cost-contract-items"])
api_router.include_router(signing_cases.router, prefix="/api/signing-cases", tags=["signing-cases"])
api_router.include_router(contracts.router, prefix="/api/contracts", tags=["contracts"])
api_router.include_router(budget_lines.router, prefix="/api/budget-lines", tags=["budget-lines"])
api_router.include_router(payment_schedules.router, prefix="/api/payment-schedules", tags=["payment-schedules"])
api_router.include_router(invoices.router, prefix="/api/invoices", tags=["invoices"])
api_router.include_router(documents.router, prefix="/api/documents", tags=["documents"])
api_router.include_router(import_batches.router, prefix="/api/import-batches", tags=["import-batches"])
api_router.include_router(field_mappings.router, prefix="/api/field-mappings", tags=["field-mappings"])
api_router.include_router(todos.router, prefix="/api/todos", tags=["todos"])
api_router.include_router(reminders.router, prefix="/api/reminders", tags=["reminders"])
api_router.include_router(data_quality_issues.router, prefix="/api/data-quality-issues", tags=["data-quality-issues"])
api_router.include_router(audit_logs.router, prefix="/api/audit-logs", tags=["audit-logs"])
api_router.include_router(search.router, prefix="/api/search", tags=["search"])
api_router.include_router(system_features.router, prefix="/api/system", tags=["system-features"])
