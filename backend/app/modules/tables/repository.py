from typing import List, Optional

from sqlalchemy.orm import Session

from app.modules.tables.model import Table


class TableRepository:

    def __init__(self, db: Session):
        self.db = db

    # =====================================
    # LISTAR
    # =====================================

    def get_all(self) -> List[Table]:

        return (
            self.db.query(Table)
            .order_by(Table.number.asc())
            .all()
        )

    # =====================================
    # OBTENER
    # =====================================

    def get_by_id(self, table_id: int) -> Optional[Table]:

        return (
            self.db.query(Table)
            .filter(Table.id == table_id)
            .first()
        )

    # =====================================
    # BUSCAR POR NÚMERO
    # =====================================

    def get_by_number(self, number: int):

        return (
            self.db.query(Table)
            .filter(Table.number == number)
            .first()
        )

    # =====================================
    # CREAR
    # =====================================

    def create(self, table: Table):

        self.db.add(table)
        self.db.commit()
        self.db.refresh(table)

        return table

    # =====================================
    # ACTUALIZAR
    # =====================================

    def update(self, table: Table):

        self.db.commit()
        self.db.refresh(table)

        return table

    # =====================================
    # ELIMINAR
    # =====================================

    def delete(self, table: Table):

        self.db.delete(table)
        self.db.commit()

    # =====================================
    # CONTADORES
    # =====================================

    def count(self):

        return self.db.query(Table).count()

    def count_available(self):

        return (
            self.db.query(Table)
            .filter(Table.active == True)
            .count()
        )

    def count_busy(self):

        return 0

    def count_reserved(self):

        return 0

    def count_out_service(self):

        return (
            self.db.query(Table)
            .filter(Table.active == False)
            .count()
        )