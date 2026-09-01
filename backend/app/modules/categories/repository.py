from typing import List
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.categories.model import Category


class CategoryRepository:

    def __init__(self, db: Session):

        self.db = db

    # ==========================================
    # LISTAR
    # ==========================================

    def get_all(self) -> List[Category]:

        return (

            self.db.query(Category)

            .order_by(Category.display_order.asc())

            .all()

        )

    # ==========================================
    # SOLO ACTIVAS
    # ==========================================

    def get_active(self):

        return (

            self.db.query(Category)

            .filter(Category.active == True)

            .order_by(Category.display_order.asc())

            .all()

        )

    # ==========================================
    # OBTENER POR ID
    # ==========================================

    def get_by_id(

        self,

        category_id: UUID

    ) -> Optional[Category]:

        return (

            self.db.query(Category)

            .filter(Category.id == category_id)

            .first()

        )

    # ==========================================
    # BUSCAR POR NOMBRE
    # ==========================================

    def get_by_name(

        self,

        name: str

    ) -> Optional[Category]:

        return (

            self.db.query(Category)

            .filter(Category.name == name)

            .first()

        )

    # ==========================================
    # CREAR
    # ==========================================

    def create(

        self,

        category: Category

    ):

        self.db.add(category)

        self.db.commit()

        self.db.refresh(category)

        return category

    # ==========================================
    # ACTUALIZAR
    # ==========================================

    def update(

        self,

        category: Category

    ):

        self.db.commit()

        self.db.refresh(category)

        return category

    # ==========================================
    # ELIMINAR
    # ==========================================

    def delete(

        self,

        category: Category

    ):

        self.db.delete(category)

        self.db.commit()

    # ==========================================
    # CONTADORES
    # ==========================================

    def count(self):

        return self.db.query(Category).count()

    def count_active(self):

        return (

            self.db.query(Category)

            .filter(Category.active == True)

            .count()

        )

    def count_inactive(self):

        return (

            self.db.query(Category)

            .filter(Category.active == False)

            .count()

        )