from uuid import UUID

from sqlalchemy.orm import Session

from .model import Menu


class MenuRepository:

    def get_all(self, db: Session):

        return (
            db.query(Menu)
            .order_by(Menu.display_order.asc())
            .all()
        )

    def get_by_id(
        self,
        db: Session,
        menu_id: UUID
    ):

        return (
            db.query(Menu)
            .filter(Menu.id == menu_id)
            .first()
        )

    def get_by_title(
        self,
        db: Session,
        title: str
    ):

        return (
            db.query(Menu)
            .filter(Menu.title == title)
            .first()
        )

    def get_by_slug(
        self,
        db: Session,
        slug: str
    ):

        return (
            db.query(Menu)
            .filter(Menu.slug == slug)
            .first()
        )

    def create(
        self,
        db: Session,
        menu: Menu
    ):

        db.add(menu)
        db.commit()
        db.refresh(menu)

        return menu

    def update(
        self,
        db: Session,
        menu: Menu
    ):

        db.commit()
        db.refresh(menu)

        return menu

    def delete(
        self,
        db: Session,
        menu: Menu
    ):

        db.delete(menu)
        db.commit()