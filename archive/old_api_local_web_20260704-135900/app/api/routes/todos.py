from app.api.routes.generic_crud import build_crud_router
from app.schemas.generic_records import TodoCreate, TodoUpdate


router = build_crud_router(
    table="todos",
    entity_type="todo",
    create_schema=TodoCreate,
    update_schema=TodoUpdate,
    search_columns=["title", "owner_user", "owner_department", "priority", "task_type", "status"],
)
