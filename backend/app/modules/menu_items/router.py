from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.core.database import get_db

from .schemas import (
    MenuItemCreate,
    MenuItemResponse
)

from .service import MenuItemService


router = APIRouter(

    prefix="/api/menu",

    tags=["Menu Items"]

)


service = MenuItemService()


# ==========================================================
# LISTAR PLATOS DE UN MENÚ
# ==========================================================

@router.get(
    "/{menu_id}/items",
    response_model=list[MenuItemResponse]
)
def list_menu_items(

    menu_id: UUID,

    db: Session = Depends(get_db)

):

    return service.list_by_menu(

        db,

        menu_id

    )


# ==========================================================
# AGREGAR PLATO AL MENÚ
# ==========================================================

@router.post(
    "/{menu_id}/items",
    response_model=MenuItemResponse
)
def create_menu_item(

    menu_id: UUID,

    data: MenuItemCreate,

    db: Session = Depends(get_db)

):

    return service.create(

        db,

        menu_id,

        data

    )


# ==========================================================
# QUITAR PLATO DEL MENÚ
# ==========================================================

@router.delete(
    "/{menu_id}/items/{item_id}",
    response_model=MenuItemResponse
)
def delete_menu_item(

    menu_id: UUID,

    item_id: UUID,

    db: Session = Depends(get_db)

):

    item = service.repository.get(

        db,

        item_id

    )

    if not item:

        raise HTTPException(

            status_code=404,

            detail="Elemento del menú no encontrado."

        )

    if item.menu_id != menu_id:

        raise HTTPException(

            status_code=400,

            detail="El elemento no pertenece a este menú."

        )

    return service.delete(

        db,

        item_id

    )