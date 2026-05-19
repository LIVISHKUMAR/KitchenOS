from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.recipe.service import RecipeService

router = APIRouter()


class RecipeIngredientCreate(BaseModel):
    menu_item_id: str
    inventory_item_id: str
    quantity: float
    unit: str


@router.post("/ingredients")
async def add_recipe_ingredient(
    data: RecipeIngredientCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    recipe_service = RecipeService(db)
    return recipe_service.add_recipe_ingredient(
        menu_item_id=data.menu_item_id,
        inventory_item_id=data.inventory_item_id,
        quantity=data.quantity,
        unit=data.unit,
        tenant_id=current_user["tenant_id"]
    )


@router.get("/{menu_item_id}")
async def get_recipe(
    menu_item_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    recipe_service = RecipeService(db)
    return recipe_service.get_recipe(menu_item_id)


@router.get("/{menu_item_id}/cost")
async def calculate_food_cost(
    menu_item_id: str,
    quantity: float = 1,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    recipe_service = RecipeService(db)
    return recipe_service.calculate_food_cost(menu_item_id, quantity)


@router.delete("/{menu_item_id}/ingredients/{ingredient_id}")
async def remove_recipe_ingredient(
    menu_item_id: str,
    ingredient_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    recipe_service = RecipeService(db)
    return recipe_service.remove_recipe_ingredient(menu_item_id, ingredient_id)
