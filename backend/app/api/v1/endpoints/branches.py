from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import Branch
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class BranchBase(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = 'India'
    phone: Optional[str] = None
    email: Optional[str] = None
    timezone: str = 'Asia/Kolkata'
    currency: str = 'INR'
    tax_identifier: Optional[str] = None
    business_type: Optional[str] = None
    is_active: bool = True


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    tax_identifier: Optional[str] = None
    business_type: Optional[str] = None
    is_active: Optional[bool] = None


class BranchResponse(BranchBase):
    id: str
    tenant_id: str

    class Config:
        from_attributes = True


@router.post("/", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    branch: BranchCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    db_branch = Branch(**branch.model_dump())
    db_branch.tenant_id = current_user["tenant_id"]
    db.add(db_branch)
    db.commit()
    db.refresh(db_branch)
    return db_branch


@router.get("/", response_model=List[BranchResponse])
async def read_branches(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    return db.query(Branch).filter(
        Branch.tenant_id == current_user["tenant_id"]
    ).offset(skip).limit(limit).all()


@router.get("/{branch_id}", response_model=BranchResponse)
async def read_branch(
    branch_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    if str(branch.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return branch


@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: str,
    branch: BranchUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    db_branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not db_branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    if str(db_branch.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    for field, value in branch.model_dump(exclude_unset=True).items():
        setattr(db_branch, field, value)
    db.commit()
    db.refresh(db_branch)
    return db_branch


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    db_branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not db_branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    if str(db_branch.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    db.delete(db_branch)
    db.commit()
    return None
