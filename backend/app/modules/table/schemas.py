from pydantic import BaseModel
from typing import Optional


class TableBase(BaseModel):
    table_number: str
    capacity: int = 4
    section: Optional[str] = None
    is_active: bool = True


class TableCreate(TableBase):
    branch_id: str


class TableUpdate(BaseModel):
    table_number: Optional[str] = None
    capacity: Optional[int] = None
    section: Optional[str] = None
    is_active: Optional[bool] = None


class TableResponse(TableBase):
    id: str
    branch_id: str
    current_order_id: Optional[str] = None

    class Config:
        from_attributes = True


class TableTransfer(BaseModel):
    from_table_id: str
    to_table_id: str


class TableMerge(BaseModel):
    source_table_ids: list[str]
    target_table_id: str
