from pydantic import BaseModel, Field
from typing import Optional


class SigningCaseCreate(BaseModel):
    case_code: Optional[str] = None
    title: str = Field(min_length=1)
    category: Optional[str] = None
    owner_department: Optional[str] = None
    owner_user: Optional[str] = None
    vendor_name: Optional[str] = None
    role: str = "manager"
    permission_scope: str = "department"
    amount: float = 0
    budget_status: str = "pending"
    project_status: str = "pending"
    signing_status: str = "pending"
    approval_status: str = "pending"
    contract_status: str = "pending"
    procurement_status: str = "pending"
    payment_status: str = "pending"
    invoice_status: str = "pending"
    source_file_name: Optional[str] = None
    source_sheet: Optional[str] = None
    source_row: Optional[int] = None
    source_column: Optional[str] = None
    source_value: Optional[str] = None
    cmdb_ci_id: Optional[str] = None
    cmdb_ci_name: Optional[str] = None
    cmdb_system_name: Optional[str] = None
    cmdb_service_name: Optional[str] = None
    cmdb_owner_department: Optional[str] = None
    cmdb_environment: Optional[str] = None
    cmdb_import_batch_id: Optional[str] = None
    cmdb_last_synced_at: Optional[str] = None
    cmdb_match_status: str = "reserved"
    cmdb_evidence_note: Optional[str] = None
    status: str = "draft"


class SigningCaseUpdate(BaseModel):
    case_code: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    owner_department: Optional[str] = None
    owner_user: Optional[str] = None
    vendor_name: Optional[str] = None
    role: Optional[str] = None
    permission_scope: Optional[str] = None
    amount: Optional[float] = None
    budget_status: Optional[str] = None
    project_status: Optional[str] = None
    signing_status: Optional[str] = None
    approval_status: Optional[str] = None
    contract_status: Optional[str] = None
    procurement_status: Optional[str] = None
    payment_status: Optional[str] = None
    invoice_status: Optional[str] = None
    source_file_name: Optional[str] = None
    source_sheet: Optional[str] = None
    source_row: Optional[int] = None
    source_column: Optional[str] = None
    source_value: Optional[str] = None
    cmdb_ci_id: Optional[str] = None
    cmdb_ci_name: Optional[str] = None
    cmdb_system_name: Optional[str] = None
    cmdb_service_name: Optional[str] = None
    cmdb_owner_department: Optional[str] = None
    cmdb_environment: Optional[str] = None
    cmdb_import_batch_id: Optional[str] = None
    cmdb_last_synced_at: Optional[str] = None
    cmdb_match_status: Optional[str] = None
    cmdb_evidence_note: Optional[str] = None
    status: Optional[str] = None
