from app.api.routes.generic_crud import build_crud_router
from app.schemas.generic_records import FieldMappingCreate, FieldMappingUpdate


router = build_crud_router(
    table="field_mappings",
    entity_type="field_mapping",
    create_schema=FieldMappingCreate,
    update_schema=FieldMappingUpdate,
    search_columns=["template_name", "source_field", "target_table", "target_field", "version", "status"],
)
