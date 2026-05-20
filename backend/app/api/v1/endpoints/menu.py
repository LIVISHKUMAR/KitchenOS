from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_current_user
from app.modules.auth.rbac import require_permission
from app.infrastructure.database import get_db_session
from app.modules.menu.service import MenuService
from app.modules.menu.schemas import (
    MenuCategoryCreate, MenuCategoryUpdate, MenuCategoryResponse,
    MenuItemCreate, MenuItemUpdate, MenuItemResponse,
    MenuVariantCreate, MenuVariantUpdate, MenuVariantResponse,
    MenuModifierGroupCreate, MenuModifierGroupUpdate, MenuModifierGroupResponse,
    MenuModifierCreate, MenuModifierUpdate, MenuModifierResponse
)

router = APIRouter()


# Category endpoints
@router.post("/categories", response_model=MenuCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: MenuCategoryCreate,
    current_user: dict = Depends(require_permission("menu:create")),
    db: Session = Depends(get_db_session)
):
    menu_service = MenuService(db)
    category_data = category.model_dump()
    category_data["tenant_id"] = current_user["tenant_id"]
    category_data["branch_id"] = current_user.get("branch_id")
    return menu_service.create_category_from_dict(category_data)


@router.get("/categories", response_model=List[MenuCategoryResponse])
async def read_categories(
    branch_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    menu_service = MenuService(db)
    return menu_service.get_categories(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        skip=skip,
        limit=limit
    )


@router.get("/categories/{category_id}", response_model=MenuCategoryResponse)
async def read_category(
    category_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    menu_service = MenuService(db)
    category = menu_service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if str(category.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return category


@router.put("/categories/{category_id}", response_model=MenuCategoryResponse)
async def update_category(
    category_id: str,
    category: MenuCategoryUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    menu_service = MenuService(db)
    db_category = menu_service.get_category(category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    if str(db_category.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    updated_category = menu_service.update_category(category_id, category.model_dump(exclude_unset=True))
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    menu_service = MenuService(db)
    db_category = menu_service.get_category(category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    if str(db_category.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    success = menu_service.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return None


# Item endpoints
@router.post("/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: MenuItemCreate,
    current_user: dict = Depends(require_permission("menu:create")),
    db: Session = Depends(get_db_session)
):
    menu_service = MenuService(db)
    item_data = item.model_dump()
    item_data["tenant_id"] = current_user["tenant_id"]
    item_data["branch_id"] = current_user.get("branch_id")
    return menu_service.create_item_from_dict(item_data)


@router.get("/items", response_model=List[MenuItemResponse])
async def read_items(
    branch_id: Optional[str] = None,
    category_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    menu_service = MenuService(db)
    return menu_service.get_items(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        category_id=category_id,
        skip=skip,
        limit=limit
    )


@router.get("/items/{item_id}", response_model=MenuItemResponse)
async def read_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    menu_service = MenuService(db)
    item = menu_service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if str(item.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return item


@router.put("/items/{item_id}", response_model=MenuItemResponse)
async def update_item(
    item_id: str,
    item: MenuItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    menu_service = MenuService(db)
    db_item = menu_service.get_item(item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if str(db_item.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    updated_item = menu_service.update_item(item_id, item.model_dump(exclude_unset=True))
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    menu_service = MenuService(db)
    db_item = menu_service.get_item(item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if str(db_item.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    success = menu_service.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return None


# Variant endpoints
@router.post("/variants", response_model=MenuVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_variant(
    variant: MenuVariantCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    from app.models import MenuVariant
    variant_data = variant.model_dump()
    variant_data["tenant_id"] = current_user["tenant_id"]
    db_variant = MenuVariant(**variant_data)
    return repo.create_variant(db_variant)


@router.get("/variants", response_model=List[MenuVariantResponse])
async def read_variants(
    menu_item_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    return repo.get_variants(
        tenant_id=current_user["tenant_id"],
        menu_item_id=menu_item_id,
        skip=skip,
        limit=limit
    )


@router.get("/variants/{variant_id}", response_model=MenuVariantResponse)
async def read_variant(
    variant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    variant = repo.get_variant(variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    if str(variant.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return variant


@router.put("/variants/{variant_id}", response_model=MenuVariantResponse)
async def update_variant(
    variant_id: str,
    variant: MenuVariantUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    db_variant = repo.get_variant(variant_id)
    if not db_variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    if str(db_variant.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    updated_variant = repo.update_variant(variant_id, variant.model_dump(exclude_unset=True))
    if not updated_variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return updated_variant


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    variant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    db_variant = repo.get_variant(variant_id)
    if not db_variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    if str(db_variant.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    success = repo.delete_variant(variant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Variant not found")
    return None


# Modifier group endpoints
@router.post("/modifier-groups", response_model=MenuModifierGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_modifier_group(
    modifier_group: MenuModifierGroupCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    from app.models import MenuModifierGroup
    group_data = modifier_group.model_dump()
    group_data["tenant_id"] = current_user["tenant_id"]
    db_modifier_group = MenuModifierGroup(**group_data)
    return repo.create_modifier_group(db_modifier_group)


@router.get("/modifier-groups", response_model=List[MenuModifierGroupResponse])
async def read_modifier_groups(
    menu_item_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    return repo.get_modifier_groups(
        tenant_id=current_user["tenant_id"],
        menu_item_id=menu_item_id,
        skip=skip,
        limit=limit
    )


@router.get("/modifier-groups/{group_id}", response_model=MenuModifierGroupResponse)
async def read_modifier_group(
    group_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    modifier_group = repo.get_modifier_group(group_id)
    if not modifier_group:
        raise HTTPException(status_code=404, detail="Modifier group not found")
    if str(modifier_group.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return modifier_group


@router.put("/modifier-groups/{group_id}", response_model=MenuModifierGroupResponse)
async def update_modifier_group(
    group_id: str,
    modifier_group: MenuModifierGroupUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    db_modifier_group = repo.get_modifier_group(group_id)
    if not db_modifier_group:
        raise HTTPException(status_code=404, detail="Modifier group not found")
    if str(db_modifier_group.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    updated_modifier_group = repo.update_modifier_group(group_id, modifier_group.model_dump(exclude_unset=True))
    if not updated_modifier_group:
        raise HTTPException(status_code=404, detail="Modifier group not found")
    return updated_modifier_group


@router.delete("/modifier-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_modifier_group(
    group_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    db_modifier_group = repo.get_modifier_group(group_id)
    if not db_modifier_group:
        raise HTTPException(status_code=404, detail="Modifier group not found")
    if str(db_modifier_group.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    success = repo.delete_modifier_group(group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Modifier group not found")
    return None


# Modifier endpoints
@router.post("/modifiers", response_model=MenuModifierResponse, status_code=status.HTTP_201_CREATED)
async def create_modifier(
    modifier: MenuModifierCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    from app.models import MenuModifier
    db_modifier = MenuModifier(**modifier.model_dump())
    return repo.create_modifier(db_modifier)


@router.get("/modifiers", response_model=List[MenuModifierResponse])
async def read_modifiers(
    group_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    return repo.get_modifiers(
        tenant_id=current_user["tenant_id"],
        group_id=group_id,
        skip=skip,
        limit=limit
    )


@router.get("/modifiers/{modifier_id}", response_model=MenuModifierResponse)
async def read_modifier(
    modifier_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    modifier = repo.get_modifier(modifier_id)
    if not modifier:
        raise HTTPException(status_code=404, detail="Modifier not found")
    return modifier


@router.put("/modifiers/{modifier_id}", response_model=MenuModifierResponse)
async def update_modifier(
    modifier_id: str,
    modifier: MenuModifierUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    db_modifier = repo.get_modifier(modifier_id)
    if not db_modifier:
        raise HTTPException(status_code=404, detail="Modifier not found")
    updated_modifier = repo.update_modifier(modifier_id, modifier.model_dump(exclude_unset=True))
    if not updated_modifier:
        raise HTTPException(status_code=404, detail="Modifier not found")
    return updated_modifier


@router.delete("/modifiers/{modifier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_modifier(
    modifier_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from app.modules.menu.repository import MenuRepository
    repo = MenuRepository(db)
    db_modifier = repo.get_modifier(modifier_id)
    if not db_modifier:
        raise HTTPException(status_code=404, detail="Modifier not found")
    success = repo.delete_modifier(modifier_id)
    if not success:
        raise HTTPException(status_code=404, detail="Modifier not found")
    return None
