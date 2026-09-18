from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import secrets

from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.dishes.model import Dish
from app.modules.order_items.model import OrderItem
from app.modules.order_batches.service import OrderBatchService
from app.modules.kitchen_queue.model import KitchenQueue

from .schemas import OrderCreate, CustomerOrderCreate
from .model import Order

from .service import OrderService

router = APIRouter(

    prefix="/orders",

    tags=["Orders"]

)

service = OrderService()


@router.post("/")

def create_order(

    data: OrderCreate,

    db: Session = Depends(get_db)

):

    return service.create(db, data)


@router.get("/")

def list_orders(

    db: Session = Depends(get_db)

):

    return service.list(db)

@router.post("/customer")
def create_customer_order(
    data: CustomerOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crea un pedido web. Caja lo confirma antes de enviarlo a cocina."""
    if not current_user.role or current_user.role.name != "Cliente":
        raise HTTPException(403, "Solo los clientes pueden crear pedidos desde la web.")
    if not data.items:
        raise HTTPException(400, "El pedido debe tener al menos un producto.")

    order_type = (data.order_type or "ONLINE").upper().strip()
    if order_type not in {"ONLINE", "DOMICILIO"}:
        raise HTTPException(400, "Tipo de pedido inválido.")

    address = (data.delivery_address or "").strip() or None
    phone = (data.delivery_phone or "").strip() or None

    delivery_fee = 7000 if order_type == "DOMICILIO" else 0
    delivery_code = f"{secrets.randbelow(1000000):06d}" if order_type == "DOMICILIO" else None
    if order_type == "DOMICILIO":
        if not address:
            raise HTTPException(400, "Para un domicilio debes indicar la dirección de entrega.")
        if not phone:
            raise HTTPException(400, "Para un domicilio debes indicar un teléfono de contacto.")
        if len(address) > 300:
            raise HTTPException(400, "La dirección es demasiado larga.")
        if len(phone) > 30:
            raise HTTPException(400, "El teléfono es demasiado largo.")

    order = Order(
        session_id=None,
        customer_id=current_user.id,
        order_type=order_type,
        status="PENDING_CASHIER",
        notes=(data.notes or "").strip() or None,
        delivery_address=address,
        delivery_phone=phone,
        delivery_fee=delivery_fee,
        delivery_code=delivery_code,
    )
    db.add(order)
    db.flush()

    total = 0
    created_items = []
    for requested in data.items:
        if requested.quantity < 1 or requested.quantity > 50:
            raise HTTPException(400, "La cantidad de un producto no es válida.")
        dish = db.query(Dish).filter(
            Dish.id == requested.dish_id,
            Dish.active == True,
            Dish.available == True,
        ).first()
        if not dish:
            raise HTTPException(404, "Uno de los platos ya no está disponible.")

        item_total = float(dish.price) * requested.quantity
        item = OrderItem(
            order_id=order.id,
            dish_id=dish.id,
            quantity=requested.quantity,
            unit_price=dish.price,
            total=item_total,
            notes=requested.notes,
            status="PENDING",
        )
        db.add(item)
        db.flush()
        total += item_total
        created_items.append(item.id)

    db.commit()
    return {
        "message": "Pedido recibido. Caja debe confirmarlo antes de enviarlo a cocina.",
        "order_id": str(order.id),
        "status": order.status,
        "subtotal": total,
        "delivery_fee": delivery_fee,
        "total": total + delivery_fee,
        "delivery_code": delivery_code,
        "items": len(created_items),
    }


def _customer_order_payload(db: Session, order: Order):
    items = (
        db.query(OrderItem)
        .options(joinedload(OrderItem.dish), joinedload(OrderItem.product))
        .filter(OrderItem.order_id == order.id)
        .all()
    )
    queue_rows = (
        db.query(KitchenQueue)
        .filter(KitchenQueue.order_item_id.in_([x.id for x in items]) if items else False)
        .all()
    )
    queue_statuses = [q.status for q in queue_rows]

    status = order.status
    if status == "PENDING_CASHIER":
        label = "Recibido — esperando confirmación de caja"
    elif status == "OPEN":
        label = "Confirmado — enviado a cocina"
    elif status == "PREPARING":
        label = "En preparación"
    elif status == "READY":
        label = "Listo"
    elif status == "OUT_FOR_DELIVERY":
        label = "En camino"
    elif status == "DELIVERED_PENDING_PAYMENT":
        label = "Entregado — pendiente de cierre en Caja"
    elif status == "DELIVERED":
        label = "Entregado"
    elif status == "CLOSED":
        label = "Cerrado"
    elif status == "CANCELLED":
        label = "Cancelado"
    else:
        label = status

    courier_location = None
    if order.order_type == "DOMICILIO" and order.courier_id:
        from app.modules.delivery.model import CourierLocation
        location = (
            db.query(CourierLocation)
            .filter(CourierLocation.courier_id == order.courier_id)
            .order_by(CourierLocation.recorded_at.desc())
            .first()
        )
        if location:
            courier_location = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "accuracy": location.accuracy,
                "recorded_at": location.recorded_at,
            }

    return {
        "id": str(order.id),
        "short_id": str(order.id)[:8].upper(),
        "status": status,
        "status_label": label,
        "order_type": order.order_type,
        "created_at": order.created_at,
        "cashier_confirmed_at": order.cashier_confirmed_at,
        "dispatched_at": order.dispatched_at,
        "served_at": order.served_at,
        "delivery_address": order.delivery_address,
        "delivery_phone": order.delivery_phone,
        "delivery_fee": float(order.delivery_fee or 0),
        "delivery_code": order.delivery_code if order.order_type == "DOMICILIO" else None,
        "courier_id": str(order.courier_id) if order.courier_id else None,
        "courier_location": courier_location,
        "notes": order.notes,
        "queue_statuses": queue_statuses,
        "items": [
            {
                "id": str(item.id),
                "name": (item.dish.name if item.dish else item.product.name if item.product else "Producto"),
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total": item.total,
                "status": item.status,
            }
            for item in items
        ],
        "total": sum(float(item.total or 0) for item in items) + float(order.delivery_fee or 0),
    }


@router.get("/customer")
def customer_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "Cliente":
        raise HTTPException(403, "Solo los clientes pueden consultar sus pedidos.")
    orders = (
        db.query(Order)
        .filter(Order.customer_id == current_user.id)
        .order_by(Order.created_at.desc())
        .limit(50)
        .all()
    )
    return [_customer_order_payload(db, order) for order in orders]


@router.get("/customer/{order_id}")
def customer_order_detail(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "Cliente":
        raise HTTPException(403, "Solo los clientes pueden consultar sus pedidos.")
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id == current_user.id).first()
    if not order:
        raise HTTPException(404, "Pedido no encontrado.")
    return _customer_order_payload(db, order)

