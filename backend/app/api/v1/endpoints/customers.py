from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.customer.service import CustomerService
from app.modules.customer.schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse
)

router = APIRouter()

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create a new customer.
    """
    customer_service = CustomerService(db)
    customer.tenant_id = current_user["tenant_id"]
    return customer_service.create_customer(customer.dict())

@router.get("/", response_model=List[CustomerResponse])
async def read_customers(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve customers.
    """
    customer_service = CustomerService(db)
    return customer_service.get_customers(
        tenant_id=current_user["tenant_id"],
        skip=skip,
        limit=limit
    )

@router.get("/{customer_id}", response_model=CustomerResponse)
async def read_customer(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve a specific customer by ID.
    """
    customer_service = CustomerService(db)
    customer = customer_service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    # Check tenant access
    if customer.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return customer

@router.get("/phone/{phone}", response_model=CustomerResponse)
async def read_customer_by_phone(
    phone: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve a specific customer by phone number.
    """
    customer_service = CustomerService(db)
    customer = customer_service.get_customer_by_phone(phone, current_user["tenant_id"])
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Update a specific customer.
    """
    customer_service = CustomerService(db)
    # Check tenant access
    db_customer = customer_service.get_customer(customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if db_customer.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_customer = customer_service.update_customer(customer_id, customer)
    if not updated_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return updated_customer

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Delete a specific customer.
    """
    customer_service = CustomerService(db)
    # Check tenant access
    db_customer = customer_service.get_customer(customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if db_customer.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = customer_service.delete_customer(customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    return None
