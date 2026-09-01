from sqlalchemy.orm import Session


class DashboardService:

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self):

        return {
            "total_mesas": 0,
            "mesas_ocupadas": 0,
            "pedidos": 0,
            "cocina": 0,
            "usuarios": 1,
            "estado_caja": "Abierta",
            "internet": "Online",
            "servidor": "Activo",
        }