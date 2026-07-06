from app.api.routes.generic_crud import build_crud_router
from app.schemas.generic_records import ReminderCreate, ReminderUpdate


router = build_crud_router(
    table="reminders",
    entity_type="reminder",
    create_schema=ReminderCreate,
    update_schema=ReminderUpdate,
    search_columns=["entity_type", "reminder_type", "target_user", "target_role", "frequency", "status"],
)
