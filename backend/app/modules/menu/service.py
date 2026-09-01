import re
import unicodedata

from sqlalchemy.orm import Session

from .model import Menu
from .repository import MenuRepository
from .schemas import (
    MenuCreate,
    MenuUpdate
)


class MenuService:

    def __init__(self):

        self.repository = MenuRepository()


    # ==========================================================
    # LISTAR
    # ==========================================================

    def list(self, db: Session):

        return self.repository.get_all()


    # ==========================================================
    # OBTENER
    # ==========================================================

    def get(
        self,
        db: Session,
        menu_id
    ):

        return self.repository.get_by_id(
            db,
            menu_id
        )


    # ==========================================================
    # OBTENER MENÚ ACTIVO
    # ==========================================================

    def get_active(self, db: Session):

        return (
            db.query(Menu)
            .filter(
                Menu.active == True
            )
            .order_by(
                Menu.display_order.asc(),
                Menu.created_at.desc()
            )
            .first()
        )


    # ==========================================================
    # CREAR MENÚ
    # ==========================================================

    def create(
        self,
        db: Session,
        data: MenuCreate
    ):

        if self.repository.get_by_title(
            db,
            data.title
        ):

            raise Exception(
                "Ya existe un menú con ese nombre."
            )


        slug = self.generate_slug(
            data.title
        )


        if self.repository.get_by_slug(
            db,
            slug
        ):

            raise Exception(
                "Ya existe un slug con ese nombre."
            )


        # ======================================================
        # SI EL NUEVO MENÚ ES ACTIVO
        # DESACTIVAMOS LOS ANTERIORES
        # ======================================================

        if data.active:

            (
                db.query(Menu)
                .filter(
                    Menu.active == True
                )
                .update(
                    {
                        Menu.active: False
                    },
                    synchronize_session=False
                )
            )


        menu = Menu(

            title=data.title,

            slug=slug,

            description=data.description,

            cover_image=data.cover_image,

            display_order=data.display_order,

            active=data.active

        )


        db.add(menu)

        db.commit()

        db.refresh(menu)

        return menu


    # ==========================================================
    # ACTUALIZAR MENÚ
    # ==========================================================

    def update(
        self,
        db: Session,
        menu_id,
        data: MenuUpdate
    ):

        menu = self.repository.get_by_id(
            db,
            menu_id
        )


        if not menu:

            raise Exception(
                "Menú no encontrado."
            )


        # ======================================================
        # VALIDAR NOMBRE
        # ======================================================

        existing_title = (
            db.query(Menu)
            .filter(
                Menu.title == data.title,
                Menu.id != menu_id
            )
            .first()
        )


        if existing_title:

            raise Exception(
                "Ya existe un menú con ese nombre."
            )


        # ======================================================
        # GENERAR SLUG
        # ======================================================

        slug = self.generate_slug(
            data.title
        )


        existing_slug = (
            db.query(Menu)
            .filter(
                Menu.slug == slug,
                Menu.id != menu_id
            )
            .first()
        )


        if existing_slug:

            raise Exception(
                "Ya existe un slug con ese nombre."
            )


        # ======================================================
        # SI ESTE MENÚ PASA A SER ACTIVO
        # DESACTIVAR TODOS LOS DEMÁS
        # ======================================================

        if data.active:

            (
                db.query(Menu)
                .filter(
                    Menu.id != menu_id,
                    Menu.active == True
                )
                .update(
                    {
                        Menu.active: False
                    },
                    synchronize_session=False
                )
            )


        menu.title = data.title

        menu.description = data.description

        menu.cover_image = data.cover_image

        menu.display_order = data.display_order

        menu.active = data.active

        menu.slug = slug


        db.commit()

        db.refresh(menu)

        return menu


    # ==========================================================
    # ELIMINAR
    # ==========================================================

    def delete(
        self,
        db: Session,
        menu_id
    ):

        menu = self.repository.get_by_id(
            db,
            menu_id
        )


        if not menu:

            raise Exception(
                "Menú no encontrado."
            )


        self.repository.delete(
            db,
            menu
        )


    # ==========================================================
    # SLUG
    # ==========================================================

    def generate_slug(
        self,
        text: str
    ) -> str:

        text = unicodedata.normalize(
            "NFKD",
            text
        )


        text = text.encode(
            "ascii",
            "ignore"
        ).decode(
            "utf-8"
        )


        text = text.lower()


        text = re.sub(
            r"[^a-z0-9]+",
            "-",
            text
        )


        return text.strip("-")