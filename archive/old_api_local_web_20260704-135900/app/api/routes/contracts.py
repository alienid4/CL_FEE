from app.api.routes.generic_crud import build_crud_router
from app.schemas.generic_records import ContractCreate, ContractUpdate


router = build_crud_router(
    table="contracts",
    entity_type="contract",
    create_schema=ContractCreate,
    update_schema=ContractUpdate,
    search_columns=["contract_code", "contract_name", "vendor_name", "status"],
)
