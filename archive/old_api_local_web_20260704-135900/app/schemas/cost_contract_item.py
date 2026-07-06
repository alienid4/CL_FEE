from pydantic import BaseModel, Field
from typing import Optional


class CostContractItemCreate(BaseModel):
    cost_item_code: Optional[str] = None
    cost_item_name: str = Field(min_length=1)
    vendor_name: Optional[str] = None
    contract_amount: float = 0
    status: str = "draft"


class CostContractItemUpdate(BaseModel):
    cost_item_code: Optional[str] = None
    cost_item_name: Optional[str] = None
    vendor_name: Optional[str] = None
    contract_amount: Optional[float] = None
    status: Optional[str] = None
