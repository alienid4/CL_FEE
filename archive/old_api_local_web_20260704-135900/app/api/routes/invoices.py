from app.api.routes.generic_crud import build_crud_router
from app.schemas.generic_records import InvoiceCreate, InvoiceUpdate


router = build_crud_router(
    table="invoices",
    entity_type="invoice",
    create_schema=InvoiceCreate,
    update_schema=InvoiceUpdate,
    search_columns=["invoice_no", "vendor_name", "invoice_month", "status", "source_file_name"],
)
