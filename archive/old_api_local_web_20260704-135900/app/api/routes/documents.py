from app.api.routes.generic_crud import build_crud_router
from app.schemas.generic_records import DocumentCreate, DocumentUpdate


router = build_crud_router(
    table="documents",
    entity_type="document",
    create_schema=DocumentCreate,
    update_schema=DocumentUpdate,
    search_columns=["file_name", "document_type", "parse_status", "source_note"],
)
