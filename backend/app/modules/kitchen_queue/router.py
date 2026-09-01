
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db

from .model import KitchenQueue
from .schemas import KitchenQueueCreate

from app.modules.order_items.model import OrderItem
from app.modules.dishes.model import Dish
from app.modules.products.model import Product


router = APIRouter(
    prefix="/api/kitchen-queue",
    tags=["Kitchen Queue"]
)


# ==========================================================
# CREAR COMANDA EN COLA
# ==========================================================

@router.post("/")
def create(
    data: KitchenQueueCreate,
    db: Session = Depends(get_db)
):
    queue = KitchenQueue(
        station_id=data.station_id,
        order_item_id=data.order_item_id,
        status="WAITING",
        created_at=datetime.utcnow(),
    )

    db.add(queue)
    db.commit()
    db.refresh(queue)

    return _serialize(queue)


# ==========================================================
# TODA LA COLA
# ==========================================================

@router.get("/")
def list_queue(
    db: Session = Depends(get_db)
):
    rows = (
        db.query(KitchenQueue)
        .options(
            joinedload(KitchenQueue.order_item)
            .joinedload(OrderItem.dish),

            joinedload(KitchenQueue.order_item)
            .joinedload(OrderItem.product)
        )
        .order_by(KitchenQueue.created_at.asc())
        .all()
    )

    return [_serialize(x) for x in rows]


# ==========================================================
# COLA DE UNA ESTACIÓN
# ==========================================================

@router.get("/station/{station_id}")
def station_queue(
    station_id: str,
    db: Session = Depends(get_db)
):
    rows = (
        db.query(KitchenQueue)
        .filter(
            KitchenQueue.station_id == station_id,
            KitchenQueue.status.in_(["WAITING", "PREPARING"])
        )
        .options(
            joinedload(KitchenQueue.order_item)
            .joinedload(OrderItem.dish),

            joinedload(KitchenQueue.order_item)
            .joinedload(OrderItem.product)
        )
        .order_by(KitchenQueue.created_at.asc())
        .all()
    )

    return [_serialize(x) for x in rows]


# ==========================================================
# ESPERANDO
# ==========================================================

@router.get("/waiting")
def waiting(
    db: Session = Depends(get_db)
):
    rows = (
        db.query(KitchenQueue)
        .filter(KitchenQueue.status == "WAITING")
        .order_by(KitchenQueue.created_at.asc())
        .all()
    )

    return [_serialize(x) for x in rows]


# ==========================================================
# HISTORIAL
# ==========================================================

@router.get("/station/{station_id}/history")
def station_history(
    station_id: str,
    db: Session = Depends(get_db)
):
    """
    Historial de comandas terminadas de una estación.

    Se conservan los tres tiempos:

    1. created_at  = llegó a cocina
    2. started_at  = cocina comenzó
    3. finished_at = cocina terminó
    """

    rows = (
        db.query(KitchenQueue)
        .filter(
            KitchenQueue.station_id == station_id,
            KitchenQueue.status == "READY"
        )
        .options(
            joinedload(KitchenQueue.order_item)
            .joinedload(OrderItem.dish),

            joinedload(KitchenQueue.order_item)
            .joinedload(OrderItem.product)
        )
        .order_by(KitchenQueue.finished_at.desc())
        .limit(100)
        .all()
    )

    return [_serialize(x) for x in rows]


# ==========================================================
# TOMAR PEDIDO
# ==========================================================

@router.patch("/{queue_id}/start")
def start(
    queue_id: str,
    db: Session = Depends(get_db)
):
    queue = (
        db.query(KitchenQueue)
        .filter(KitchenQueue.id == queue_id)
        .first()
    )

    if not queue:
        raise HTTPException(
            404,
            "Pedido de cocina no encontrado"
        )

    # Evita reiniciar el cronómetro si alguien pulsa dos veces.
    if queue.status == "WAITING":
        queue.status = "PREPARING"
        queue.started_at = datetime.utcnow()

    item = (
        db.query(OrderItem)
        .filter(OrderItem.id == queue.order_item_id)
        .first()
    )

    if item:
        item.status = "PREPARING"

        from app.modules.order_batches.model import OrderBatch

        batch = (
            db.query(OrderBatch)
            .filter(
                OrderBatch.order_id == item.order_id,
                OrderBatch.station_id == queue.station_id
            )
            .first()
        )

        if batch:
            batch.status = "PREPARING"

            from app.modules.kitchen_tickets.model import KitchenTicket

            ticket = (
                db.query(KitchenTicket)
                .filter(
                    KitchenTicket.batch_id == batch.id
                )
                .first()
            )

            if ticket:
                ticket.status = "PREPARING"

        from app.modules.orders.model import Order

        order = (
            db.query(Order)
            .filter(Order.id == item.order_id)
            .first()
        )

        if order and order.status == "OPEN":
            order.status = "PREPARING"

    db.commit()
    db.refresh(queue)

    return _serialize(queue)


# ==========================================================
# MARCAR LISTO
# ==========================================================

@router.patch("/{queue_id}/finish")
def finish(
    queue_id: str,
    db: Session = Depends(get_db)
):
    queue = (
        db.query(KitchenQueue)
        .filter(KitchenQueue.id == queue_id)
        .first()
    )

    if not queue:
        raise HTTPException(
            404,
            "Pedido de cocina no encontrado"
        )

    # Evita modificar nuevamente una comanda ya terminada.
    if queue.status == "READY":
        return _serialize(queue)

    queue.status = "READY"
    queue.finished_at = datetime.utcnow()

    item = (
        db.query(OrderItem)
        .filter(OrderItem.id == queue.order_item_id)
        .first()
    )

    if item:

        item.status = "READY"

        # --------------------------------------------------
        # Actualizar batch
        # --------------------------------------------------

        from app.modules.order_batches.model import OrderBatch

        batch = (
            db.query(OrderBatch)
            .filter(
                OrderBatch.order_id == item.order_id,
                OrderBatch.station_id == queue.station_id,
            )
            .first()
        )

        if batch:

            station_items = (
                db.query(OrderItem)
                .join(
                    KitchenQueue,
                    KitchenQueue.order_item_id == OrderItem.id
                )
                .filter(
                    OrderItem.order_id == item.order_id,
                    KitchenQueue.station_id == queue.station_id,
                )
                .all()
            )

            if station_items and all(
                x.status == "READY"
                for x in station_items
            ):

                batch.status = "READY"

                from app.modules.kitchen_tickets.model import KitchenTicket

                ticket = (
                    db.query(KitchenTicket)
                    .filter(
                        KitchenTicket.batch_id == batch.id
                    )
                    .first()
                )

                if ticket:
                    ticket.status = "READY"

        # --------------------------------------------------
        # Actualizar pedido completo
        # --------------------------------------------------

        from app.modules.orders.model import Order

        order = (
            db.query(Order)
            .filter(Order.id == item.order_id)
            .first()
        )

        if order:

            all_items = (
                db.query(OrderItem)
                .filter(OrderItem.order_id == order.id)
                .all()
            )

            if all_items and all(
                x.status == "READY"
                for x in all_items
            ):
                order.status = "READY"

    db.commit()
    db.refresh(queue)

    return _serialize(queue)


# ==========================================================
# SERIALIZAR
# ==========================================================

def _serialize(queue):

    item = queue.order_item

    dish = (
        item.dish
        if item and item.dish
        else None
    )

    product = (
        item.product
        if item and item.product
        else None
    )

    source = dish or product

    # ------------------------------------------------------
    # Cálculo de tiempos
    # ------------------------------------------------------

    waiting_seconds = None
    preparation_seconds = None
    total_seconds = None

    if queue.created_at and queue.started_at:

        waiting_seconds = max(
            0,
            int(
                (
                    queue.started_at
                    - queue.created_at
                ).total_seconds()
            )
        )

    if queue.started_at and queue.finished_at:

        preparation_seconds = max(
            0,
            int(
                (
                    queue.finished_at
                    - queue.started_at
                ).total_seconds()
            )
        )

    if queue.created_at and queue.finished_at:

        total_seconds = max(
            0,
            int(
                (
                    queue.finished_at
                    - queue.created_at
                ).total_seconds()
            )
        )

    return {
        "id": str(queue.id),

        "station_id": str(
            queue.station_id
        ),

        "order_item_id": str(
            queue.order_item_id
        ),

        "status": queue.status,

        "created_at": queue.created_at,

        "started_at": queue.started_at,

        "finished_at": queue.finished_at,

        "waiting_seconds": waiting_seconds,

        "preparation_seconds": preparation_seconds,

        "total_seconds": total_seconds,

        "name": (
            source.name
            if source
            else "Producto"
        ),

        "quantity": (
            item.quantity
            if item
            else 1
        ),

        "notes": (
            item.notes
            if item
            else None
        ),

        "order_id": (
            str(item.order_id)
            if item
            else None
        ),
    }

