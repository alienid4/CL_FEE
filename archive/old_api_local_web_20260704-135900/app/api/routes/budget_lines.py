from app.api.routes.generic_crud import build_crud_router
from app.schemas.generic_records import BudgetLineCreate, BudgetLineUpdate


router = build_crud_router(
    table="budget_lines",
    entity_type="budget_line",
    create_schema=BudgetLineCreate,
    update_schema=BudgetLineUpdate,
    search_columns=["category", "item_name", "owner_group", "status"],
)
