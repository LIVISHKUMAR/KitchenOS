from pydantic import BaseModel
from typing import Optional
from uuid import UUID

# Branch Schemas
class BranchCreate(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    phone: Optional[str] = None

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
