from sqlalchemy.orm import Session

from app.modules.tables.model import Table
from app.modules.tables.repository import TableRepository
from app.modules.tables.schema import (
    TableCreate,
    TableUpdate
)


class TableService:

    def __init__(self, db: Session):

        self.repository = TableRepository(db)

    # ==========================================
    # LISTAR
    # ==========================================

    def get_all(self):

        return self.repository.get_all()

    # ==========================================
    # OBTENER
    # ==========================================

    def get(self, table_id: int):

        table = self.repository.get_by_id(table_id)

        if not table:

            raise Exception("La mesa no existe.")

        return table

    # ==========================================
    # CREAR
    # ==========================================

    def create(self, data: TableCreate):

        exists = self.repository.get_by_number(data.number)

        if exists:

            raise Exception("Ya existe una mesa con ese número.")

        table = Table(

            number=data.number,

            name=data.name,

            capacity=data.capacity,

            zone=data.zone,

            active=data.active

        )

        return self.repository.create(table)

    # ==========================================
    # ACTUALIZAR
    # ==========================================

    def update(self, table_id: int, data: TableUpdate):

        table = self.repository.get_by_id(table_id)

        if not table:

            raise Exception("Mesa no encontrada.")

        if data.number is not None:

            exists = self.repository.get_by_number(data.number)

            if exists and exists.id != table.id:

                raise Exception("Ese número de mesa ya existe.")

            table.number = data.number

        if data.name is not None:

            table.name = data.name

        if data.capacity is not None:

            table.capacity = data.capacity

        if data.zone is not None:

            table.zone = data.zone

        if data.active is not None:

            table.active = data.active

        return self.repository.update(table)

    # ==========================================
    # ELIMINAR
    # ==========================================

    def delete(self, table_id: int):

        table = self.repository.get_by_id(table_id)

        if not table:

            raise Exception("Mesa no encontrada.")

        self.repository.delete(table)

        return True

    # ==========================================
    # DASHBOARD
    # ==========================================

    def dashboard(self):

        return {

            "total": self.repository.count(),

            "disponibles": self.repository.count_available(),

            "ocupadas": self.repository.count_busy(),

            "reservadas": self.repository.count_reserved(),

            "fuera_servicio": self.repository.count_out_service()

        }