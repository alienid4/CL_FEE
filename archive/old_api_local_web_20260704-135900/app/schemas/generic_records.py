from pydantic import BaseModel, Field


class ContractCreate(BaseModel):
    case_id: int | None = None
    contract_code: str | None = None
    contract_name: str = Field(min_length=1)
    vendor_name: str | None = None
    amount: float = 0
    start_date: str | None = None
    end_date: str | None = None
    signing_case_id: str | None = None
    procurement_no: str | None = None
    owner_department: str | None = None
    owner_user: str | None = None
    permission_scope: str = "department"
    cmdb_ci_id: str | None = None
    cmdb_ci_name: str | None = None
    cmdb_system_name: str | None = None
    cmdb_service_name: str | None = None
    cmdb_owner_department: str | None = None
    cmdb_environment: str | None = None
    cmdb_import_batch_id: str | None = None
    cmdb_last_synced_at: str | None = None
    cmdb_match_status: str = "reserved"
    cmdb_evidence_note: str | None = None
    status: str = "draft"


class ContractUpdate(BaseModel):
    case_id: int | None = None
    contract_code: str | None = None
    contract_name: str | None = None
    vendor_name: str | None = None
    amount: float | None = None
    start_date: str | None = None
    end_date: str | None = None
    signing_case_id: str | None = None
    procurement_no: str | None = None
    owner_department: str | None = None
    owner_user: str | None = None
    permission_scope: str | None = None
    cmdb_ci_id: str | None = None
    cmdb_ci_name: str | None = None
    cmdb_system_name: str | None = None
    cmdb_service_name: str | None = None
    cmdb_owner_department: str | None = None
    cmdb_environment: str | None = None
    cmdb_import_batch_id: str | None = None
    cmdb_last_synced_at: str | None = None
    cmdb_match_status: str | None = None
    cmdb_evidence_note: str | None = None
    status: str | None = None


class BudgetLineCreate(BaseModel):
    budget_year: int
    category: str | None = None
    item_name: str = Field(min_length=1)
    owner_group: str | None = None
    budget_amount: float = 0
    status: str = "draft"


class BudgetLineUpdate(BaseModel):
    budget_year: int | None = None
    category: str | None = None
    item_name: str | None = None
    owner_group: str | None = None
    budget_amount: float | None = None
    status: str | None = None


class PaymentScheduleCreate(BaseModel):
    case_id: int | None = None
    contract_id: int | None = None
    payment_phase: str | None = None
    planned_payment_date: str | None = None
    actual_payment_date: str | None = None
    payment_month: str | None = None
    payment_amount: float = 0
    payment_condition: str | None = None
    invoice_status: str = "not_received"
    vendor_name: str | None = None
    source_file_name: str | None = None
    source_sheet: str | None = None
    source_row: int | None = None
    source_column: str | None = None
    source_value: str | None = None
    status: str = "draft"


class PaymentScheduleUpdate(BaseModel):
    case_id: int | None = None
    contract_id: int | None = None
    payment_phase: str | None = None
    planned_payment_date: str | None = None
    actual_payment_date: str | None = None
    payment_month: str | None = None
    payment_amount: float | None = None
    payment_condition: str | None = None
    invoice_status: str | None = None
    vendor_name: str | None = None
    source_file_name: str | None = None
    source_sheet: str | None = None
    source_row: int | None = None
    source_column: str | None = None
    source_value: str | None = None
    status: str | None = None


class InvoiceCreate(BaseModel):
    case_id: int | None = None
    contract_id: int | None = None
    payment_id: int | None = None
    invoice_no: str | None = None
    vendor_name: str | None = None
    invoice_date: str | None = None
    invoice_month: str | None = None
    invoice_amount: float = 0
    tax_amount: float = 0
    received_date: str | None = None
    status: str = "pending"
    source_file_name: str | None = None
    source_sheet: str | None = None
    source_row: int | None = None
    source_column: str | None = None
    source_value: str | None = None


class InvoiceUpdate(BaseModel):
    case_id: int | None = None
    contract_id: int | None = None
    payment_id: int | None = None
    invoice_no: str | None = None
    vendor_name: str | None = None
    invoice_date: str | None = None
    invoice_month: str | None = None
    invoice_amount: float | None = None
    tax_amount: float | None = None
    received_date: str | None = None
    status: str | None = None
    source_file_name: str | None = None
    source_sheet: str | None = None
    source_row: int | None = None
    source_column: str | None = None
    source_value: str | None = None


class DocumentCreate(BaseModel):
    case_id: int | None = None
    contract_id: int | None = None
    payment_id: int | None = None
    invoice_id: int | None = None
    file_name: str = Field(min_length=1)
    document_type: str = "other"
    parse_status: str = "not_parsed"
    page_no: str | None = None
    evidence_text: str | None = None
    source_note: str | None = None
    uploaded_by: str | None = None


class DocumentUpdate(BaseModel):
    case_id: int | None = None
    contract_id: int | None = None
    payment_id: int | None = None
    invoice_id: int | None = None
    file_name: str | None = None
    document_type: str | None = None
    parse_status: str | None = None
    page_no: str | None = None
    evidence_text: str | None = None
    source_note: str | None = None
    uploaded_by: str | None = None


class ImportBatchCreate(BaseModel):
    source_file_name: str = Field(min_length=1)
    source_type: str = "excel"
    status: str = "uploaded"
    row_count: int = 0


class ImportBatchUpdate(BaseModel):
    source_file_name: str | None = None
    source_type: str | None = None
    status: str | None = None
    row_count: int | None = None


class FieldMappingCreate(BaseModel):
    template_name: str = Field(min_length=1)
    source_field: str = Field(min_length=1)
    target_table: str = Field(min_length=1)
    target_field: str = Field(min_length=1)
    transform_note: str | None = None
    version: str = "v1"
    status: str = "draft"


class FieldMappingUpdate(BaseModel):
    template_name: str | None = None
    source_field: str | None = None
    target_table: str | None = None
    target_field: str | None = None
    transform_note: str | None = None
    version: str | None = None
    status: str | None = None


class TodoCreate(BaseModel):
    case_id: int | None = None
    title: str = Field(min_length=1)
    owner_user: str | None = None
    owner_department: str | None = None
    due_date: str | None = None
    priority: str = "medium"
    task_type: str = "follow_up"
    result_note: str | None = None
    completed_at: str | None = None
    status: str = "open"


class TodoUpdate(BaseModel):
    case_id: int | None = None
    title: str | None = None
    owner_user: str | None = None
    owner_department: str | None = None
    due_date: str | None = None
    priority: str | None = None
    task_type: str | None = None
    result_note: str | None = None
    completed_at: str | None = None
    status: str | None = None


class ReminderCreate(BaseModel):
    case_id: int | None = None
    entity_type: str
    entity_id: int | None = None
    reminder_type: str
    remind_at: str | None = None
    target_user: str | None = None
    target_role: str | None = None
    frequency: str = "once"
    status: str = "open"


class ReminderUpdate(BaseModel):
    case_id: int | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    reminder_type: str | None = None
    remind_at: str | None = None
    target_user: str | None = None
    target_role: str | None = None
    frequency: str | None = None
    status: str | None = None


class DataQualityIssueCreate(BaseModel):
    case_id: int | None = None
    entity_type: str
    entity_id: int | None = None
    severity: str = "warning"
    rule_code: str
    message: str
    source_file_name: str | None = None
    source_sheet: str | None = None
    source_row: int | None = None
    source_column: str | None = None
    original_value: str | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_note: str | None = None
    status: str = "open"


class DataQualityIssueUpdate(BaseModel):
    case_id: int | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    severity: str | None = None
    rule_code: str | None = None
    message: str | None = None
    source_file_name: str | None = None
    source_sheet: str | None = None
    source_row: int | None = None
    source_column: str | None = None
    original_value: str | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_note: str | None = None
    status: str | None = None
