from uuid import UUID

from app.modules.categories.model import Category
from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schema import (
    CategoryCreate,
    CategoryUpdate
)


class CategoryService:

    def __init__(self, repository: CategoryRepository):

        self.repository = repository

    # ==========================================
    # LISTAR
    # ==========================================

    def get_all(self):

        return self.repository.get_all()

    # ==========================================
    # ACTIVAS
    # ==========================================

    def get_active(self):

        return self.repository.get_active()

    # ==========================================
    # OBTENER
    # ==========================================

    def get(

        self,

        category_id: UUID

    ):

        categoria = self.repository.get_by_id(category_id)

        if not categoria:

            raise Exception(

                "La categoría no existe."

            )

        return categoria

    # ==========================================
    # CREAR
    # ==========================================

    def create(

        self,

        data: CategoryCreate

    ):

        existe = self.repository.get_by_name(data.name)

        if existe:

            raise Exception(

                "Ya existe una categoría con ese nombre."

            )

        categoria = Category(

            name=data.name,

            description=data.description,

            color=data.color,

            icon=data.icon,

            display_order=data.display_order,

            active=data.active,
            station_id=data.station_id

        )

        return self.repository.create(categoria)

    # ==========================================
    # ACTUALIZAR
    # ==========================================

    def update(

        self,

        category_id: UUID,

        data: CategoryUpdate

    ):

        categoria = self.repository.get_by_id(category_id)

        if not categoria:

            raise Exception(

                "Categoría no encontrada."

            )

        if data.station_id is not None:
            categoria.station_id = data.station_id

        if data.name is not None:

            repetida = self.repository.get_by_name(data.name)

            if repetida and repetida.id != categoria.id:

                raise Exception(

                    "Ya existe otra categoría con ese nombre."

                )

            categoria.name = data.name

        if data.description is not None:

            categoria.description = data.description

        if data.color is not None:

            categoria.color = data.color

        if data.icon is not None:

            categoria.icon = data.icon

        if data.display_order is not None:

            categoria.display_order = data.display_order

        if data.active is not None:

            categoria.active = data.active

        return self.repository.update(categoria)

    # ==========================================
    # ELIMINAR
    # ==========================================

    def delete(

        self,

        category_id: UUID

    ):

        categoria = self.repository.get_by_id(category_id)

        if not categoria:

            raise Exception(

                "Categoría no encontrada."

            )

        # Más adelante aquí validaremos
        # si la categoría tiene productos.

        self.repository.delete(categoria)

        return True

    # ==========================================
    # DASHBOARD
    # ==========================================

    def dashboard(self):

        return {

            "total": self.repository.count(),

            "active": self.repository.count_active(),

            "inactive": self.repository.count_inactive()

        }