from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from .model import MenuItem


class MenuItemRepository:

    def list_by_menu(
        self,
        db: Session,
        menu_id: UUID
    ):

        return (

            db.query(MenuItem)

            .options(
                joinedload(MenuItem.dish)
            )

            .filter(
                MenuItem.menu_id == menu_id,
                MenuItem.active == True
            )

            .order_by(
                MenuItem.display_order.asc()
            )

            .all()
        )


    def get(
        self,
        db: Session,
        item_id: UUID
    ):

        return (

            db.query(MenuItem)

            .options(
                joinedload(MenuItem.dish)
            )

            .filter(
                MenuItem.id == item_id
            )

            .first()
        )


    def get_existing(
        self,
        db: Session,
        menu_id: UUID,
        dish_id: UUID
    ):

        return (

            db.query(MenuItem)

            .filter(
                MenuItem.menu_id == menu_id,
                MenuItem.dish_id == dish_id
            )

            .first()
        )


    def create(
        self,
        db: Session,
        item: MenuItem
    ):

        db.add(item)

        db.commit()

        db.refresh(item)

        return item


    def delete(
        self,
        db: Session,
        item: MenuItem
    ):

        item.active = False

        db.commit()

        db.refresh(item)

        return item