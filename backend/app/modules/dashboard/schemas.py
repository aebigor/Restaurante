from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.configuracion.models.table import Table


class DashboardService:

    @staticmethod
    def resumen(db: Session):

        total_mesas = db.query(func.count(Table.id)).scalar() or 0

        mesas_ocupadas = (
            db.query(func.count(Table.id))
            .filter(Table.status == "OCUPADA")
            .scalar() or 0
        )

        return {

            "mesas_ocupadas": mesas_ocupadas,
            "mesas_totales": total_mesas,

            "pedidos": 0,

            "cocina": 0,

            "caja": "Abierta",

            "internet": "Online",

            "servidor": "Activo",

            "usuarios": 1

        }