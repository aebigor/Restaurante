from uuid import UUID
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.modules.menu.model import Menu
from app.modules.dishes.model import Dish

from .model import MenuItem
from .repository import MenuItemRepository
from .schemas import MenuItemCreate


class MenuItemService:

    def __init__(self):

        self.repository = MenuItemRepository()


    # ==========================================================
    # LISTAR ELEMENTOS DEL MENÚ
    # ==========================================================

    def list_by_menu(
        self,
        db: Session,
        menu_id: UUID
    ):

        menu = (
            db.query(Menu)
            .filter(Menu.id == menu_id)
            .first()
        )

        if not menu:

            raise HTTPException(
                status_code=404,
                detail="Menú no encontrado."
            )

        return self.repository.list_by_menu(
            db,
            menu_id
        )


    # ==========================================================
    # AGREGAR PLATO
    # ==========================================================

    def create(
        self,
        db: Session,
        menu_id: UUID,
        data: MenuItemCreate
    ):

        # ------------------------------------------------------
        # VERIFICAR MENÚ
        # ------------------------------------------------------

        menu = (
            db.query(Menu)
            .filter(
                Menu.id == menu_id,
                Menu.active == True
            )
            .first()
        )

        if not menu:

            raise HTTPException(
                status_code=404,
                detail="El menú no existe o está inactivo."
            )


        # ------------------------------------------------------
        # VERIFICAR PLATO
        # ------------------------------------------------------

        dish = (
            db.query(Dish)
            .filter(
                Dish.id == data.dish_id,
                Dish.active == True,
                Dish.available == True
            )
            .first()
        )

        if not dish:

            raise HTTPException(
                status_code=404,
                detail=(
                    "El plato no existe, está inactivo "
                    "o no está disponible."
                )
            )


        # ------------------------------------------------------
        # EVITAR DUPLICADOS
        # ------------------------------------------------------

        existing = self.repository.get_existing(
            db,
            menu_id,
            data.dish_id
        )

        if existing:

            if not existing.active:

                existing.active = True

                existing.display_order = (
                    data.display_order
                )

                db.commit()

                db.refresh(existing)

                return existing


            raise HTTPException(
                status_code=400,
                detail="Este plato ya está agregado al menú."
            )


        # ------------------------------------------------------
        # CREAR ITEM
        # ------------------------------------------------------

        item = MenuItem(

            id=uuid.uuid4(),

            menu_id=menu_id,

            dish_id=data.dish_id,

            display_order=data.display_order,

            active=True

        )


        return self.repository.create(
            db,
            item
        )


    # ==========================================================
    # ELIMINAR / DESACTIVAR
    # ==========================================================

    def delete(
        self,
        db: Session,
        item_id: UUID
    ):

        item = self.repository.get(
            db,
            item_id
        )

        if not item:

            raise HTTPException(
                status_code=404,
                detail="Elemento del menú no encontrado."
            )


        return self.repository.delete(
            db,
            item
        )