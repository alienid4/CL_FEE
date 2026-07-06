from app.api.routes.generic_crud import build_crud_router
from app.schemas.generic_records import DataQualityIssueCreate, DataQualityIssueUpdate


router = build_crud_router(
    table="data_quality_issues",
    entity_type="data_quality_issue",
    create_schema=DataQualityIssueCreate,
    update_schema=DataQualityIssueUpdate,
    search_columns=["entity_type", "severity", "rule_code", "message", "source_file_name", "status"],
)
