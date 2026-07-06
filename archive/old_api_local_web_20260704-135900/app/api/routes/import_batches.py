from app.api.routes.generic_crud import build_crud_router
from app.schemas.generic_records import ImportBatchCreate, ImportBatchUpdate


router = build_crud_router(
    table="import_batches",
    entity_type="import_batch",
    create_schema=ImportBatchCreate,
    update_schema=ImportBatchUpdate,
    search_columns=["source_file_name", "source_type", "status"],
)
