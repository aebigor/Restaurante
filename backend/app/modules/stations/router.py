from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db

from .schemas import (
    StationCreate,
    StationResponse
)

from .service import StationService


router = APIRouter(
    prefix="/stations",
    tags=["Stations"]
)


# =========================================================
# LISTAR ESTACIONES
# =========================================================

@router.get(
    "/",
    response_model=list[StationResponse]
)
def list_stations(
    db: Session = Depends(get_db)
):
    return StationService(db).list()


# =========================================================
# CREAR ESTACIÓN
# =========================================================

@router.post(
    "/",
    response_model=StationResponse
)
def create_station(
    data: StationCreate,
    db: Session = Depends(get_db)
):
    return StationService(db).create(data)


# =========================================================
# DASHBOARD DE ESTACIONES
# =========================================================
#
# IMPORTANTE:
# Por ahora NO consultamos:
#
#   dishes
#   screens
#
# porque esas tablas todavía no existen en la base de datos
# actual.
#
# Cuando terminemos de sincronizar las migraciones de esos
# módulos, volveremos a conectar esas estadísticas.
#
# =========================================================

@router.get("/dashboard")
def stations_dashboard(
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # Kitchen Queue
    # -----------------------------------------------------
    #
    # Esta tabla sí debe existir para poder consultar
    # el estado de las comandas.
    #
    # Si todavía no existe en tu BD, también tendremos
    # que sincronizar esa migración.
    # -----------------------------------------------------

    try:

        from app.modules.kitchen_queue.model import KitchenQueue

    except ImportError:

        KitchenQueue = None


    # -----------------------------------------------------
    # Obtener estaciones
    # -----------------------------------------------------

    stations = StationService(db).list()

    result = []


    # -----------------------------------------------------
    # Procesar cada estación
    # -----------------------------------------------------

    for station in stations:

        waiting = 0
        preparing = 0
        ready = 0


        # -------------------------------------------------
        # Estadísticas de cocina
        # -------------------------------------------------

        if KitchenQueue is not None:

            try:

                waiting = db.query(
                    func.count(KitchenQueue.id)
                ).filter(
                    KitchenQueue.station_id == station.id,
                    KitchenQueue.status == "WAITING"
                ).scalar() or 0


                preparing = db.query(
                    func.count(KitchenQueue.id)
                ).filter(
                    KitchenQueue.station_id == station.id,
                    KitchenQueue.status == "PREPARING"
                ).scalar() or 0


                ready = db.query(
                    func.count(KitchenQueue.id)
                ).filter(
                    KitchenQueue.station_id == station.id,
                    KitchenQueue.status == "READY"
                ).scalar() or 0

            except Exception:

                # Si KitchenQueue todavía no existe en BD,
                # el dashboard no debe caerse.
                waiting = 0
                preparing = 0
                ready = 0


        # -------------------------------------------------
        # Respuesta de estación
        # -------------------------------------------------

        result.append({

            "id": station.id,

            "name": station.name,

            "priority": station.priority,

            "printer_name": station.printer_name,

            "color": station.color,

            "active": station.active,


            # -------------------------------------------------
            # PLATOS
            # -------------------------------------------------
            #
            # La tabla dishes todavía no existe en la BD.
            # Por eso temporalmente devolvemos 0.
            #
            # Posteriormente lo conectaremos al módulo real
            # de platos.
            # -------------------------------------------------

            "dishes_count": 0,


            # -------------------------------------------------
            # ESTADOS DE COCINA
            # -------------------------------------------------

            "waiting": waiting,

            "preparing": preparing,

            "ready": ready,

            "total_active":
                waiting + preparing,


            # -------------------------------------------------
            # PANTALLAS KDS
            # -------------------------------------------------
            #
            # La tabla screens todavía no existe en la BD.
            # Por ahora devolvemos una lista vacía.
            #
            # Después conectaremos aquí las pantallas
            # reales de cada estación.
            # -------------------------------------------------

            "screens": []

        })


    return result