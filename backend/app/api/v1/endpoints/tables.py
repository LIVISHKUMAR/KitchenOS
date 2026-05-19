from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.table.service import TableService
from app.modules.table.schemas import (
    TableCreate, TableUpdate, TableResponse, TableTransfer, TableMerge
)

router = APIRouter()


@router.post("/", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
async def create_table(
    table: TableCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    table_service = TableService(db)
    return table_service.create_table(table.model_dump())


@router.get("/", response_model=List[TableResponse])
async def list_tables(
    branch_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    table_service = TableService(db)
    return table_service.get_tables(branch_id, skip=skip, limit=limit)


@router.get("/available", response_model=List[TableResponse])
async def list_available_tables(
    branch_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    table_service = TableService(db)
    return table_service.get_available_tables(branch_id)


@router.get("/{table_id}", response_model=TableResponse)
async def get_table(
    table_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    table_service = TableService(db)
    table = table_service.get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return table


@router.put("/{table_id}", response_model=TableResponse)
async def update_table(
    table_id: str,
    table: TableUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    table_service = TableService(db)
    updated = table_service.update_table(table_id, table.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Table not found")
    return updated


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(
    table_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    table_service = TableService(db)
    if not table_service.delete_table(table_id):
        raise HTTPException(status_code=404, detail="Table not found")
    return None


@router.post("/transfer")
async def transfer_table(
    data: TableTransfer,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    table_service = TableService(db)
    return table_service.transfer_table(data.from_table_id, data.to_table_id)


@router.post("/merge")
async def merge_tables(
    data: TableMerge,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    table_service = TableService(db)
    return table_service.merge_tables(data.source_table_ids, data.target_table_id)
