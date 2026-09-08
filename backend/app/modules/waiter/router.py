from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user

from app.modules.sessions.model import Session as RestaurantSession
from app.modules.orders.model import Order
from app.modules.order_items.model import OrderItem
from app.modules.order_batches.model import OrderBatch
from app.modules.kitchen_tickets.model import KitchenTicket
from app.modules.kitchen_queue.model import KitchenQueue

from app.modules.menu.model import Menu
from app.modules.menu_items.model import MenuItem
from app.modules.dishes.model import Dish
from app.modules.products.model import Product
from app.modules.tables.model import Table
from app.modules.cashier.model import CashPayment

from .schemas import WaiterOrderCreate


router = APIRouter(
    prefix="/api/waiter",
    tags=["Waiter"]
)


# ==========================================================
# MENÚ ACTIVO
# ==========================================================

@router.get("/menu")
def active_menu(
    db: Session = Depends(get_db)
):

    menu = (
        db.query(Menu)
        .options(
            joinedload(Menu.items)
            .joinedload(MenuItem.dish)
            .joinedload(Dish.category),

            joinedload(Menu.items)
            .joinedload(MenuItem.dish)
            .joinedload(Dish.station)
        )
        .filter(
            Menu.active.is_(True)
        )
        .order_by(
            Menu.display_order.asc()
        )
        .first()
    )

    if not menu:

        return {
            "active": False,
            "menu": None,
            "categories": [],
            "dishes": []
        }

    dishes = []
    categories_map = {}

    for item in menu.items:

        if not item.active:
            continue

        dish = item.dish

        if not dish:
            continue

        if not dish.active:
            continue

        if not dish.available:
            continue

        category = dish.category
        station = dish.station

        category_id = (
            str(category.id)
            if category
            else None
        )

        if category:

            if category.id not in categories_map:

                categories_map[category.id] = {
                    "id": str(category.id),
                    "name": category.name,
                    "description": category.description,
                    "color": category.color,
                    "icon": category.icon,
                    "display_order": (
                        category.display_order
                        if category.display_order is not None
                        else 0
                    )
                }

        dishes.append({

            "id": str(dish.id),

            "name": dish.name,

            "description": dish.description,

            "price": float(dish.price),

            "category_id": category_id,

            "category": (
                category.name
                if category
                else "Sin categoría"
            ),

            "station": (
                station.name
                if station
                else "Sin estación"
            ),

            "portion": dish.portion,

            "image": dish.image,

            "preparation_time": dish.preparation_time,

            "available": dish.available,

            "active": dish.active,

            "display_order": (
                item.display_order
                if item.display_order is not None
                else 0
            )
        })

    # Los productos (bebidas y otros artículos) también forman parte
    # del catálogo que utiliza el mesero. No dependen de menu_items.
    products = (
        db.query(Product)
        .options(
            joinedload(Product.category),
            joinedload(Product.station)
        )
        .filter(
            Product.active.is_(True),
            Product.stock > 0
        )
        .order_by(Product.name.asc())
        .all()
    )

    for product in products:
        category = product.category
        if category and category.id not in categories_map:
            categories_map[category.id] = {
                "id": str(category.id),
                "name": category.name,
                "description": category.description,
                "color": category.color,
                "icon": category.icon,
                "display_order": category.display_order or 0
            }

    dishes.sort(
        key=lambda dish: (
            dish["category"] or "",
            dish["display_order"],
            dish["name"].lower()
        )
    )

    product_data = []
    for product in products:
        category = product.category
        station = product.station
        product_data.append({
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "category_id": str(category.id) if category else None,
            "category": category.name if category else "Sin categoría",
            "station": station.name if station else "Sin estación",
            "portion": None,
            "image": None,
            "preparation_time": product.preparation_time,
            "available": product.active and product.stock > 0,
            "active": product.active,
            "display_order": 999999,
            "is_product": True,
            "stock": product.stock
        })

    categories = list(
        categories_map.values()
    )

    categories.sort(
        key=lambda category: (
            category["display_order"],
            category["name"].lower()
        )
    )

    return {

        "active": True,

        "menu": {

            "id": str(menu.id),

            "title": menu.title,

            "slug": menu.slug,

            "description": menu.description,

            "active": menu.active
        },

        "categories": categories,

        "dishes": dishes,

        "products": product_data
    }


# ==========================================================
# MESAS
# ==========================================================

@router.get("/tables")
def waiter_tables(
    db: Session = Depends(get_db)
):

    tables = (
        db.query(Table)
        .filter(
            Table.active.is_(True)
        )
        .order_by(
            Table.number.asc()
        )
        .all()
    )

    open_sessions = {
        session.table_id: session
        for session in (
            db.query(RestaurantSession)
            .filter(
                RestaurantSession.status.in_(["OPEN", "PAID", "CLEAN"])
            )
            .all()
        )
    }

    result = []

    for table in tables:

        session = open_sessions.get(
            table.id
        )

        pending_delivery = 0
        if session:
            pending_delivery = db.query(Order).filter(
                Order.session_id == session.id,
                Order.status != "CANCELLED",
                Order.served_at.is_(None)
            ).count()

        result.append({

            "id": table.id,

            "number": table.number,

            "name": table.name,

            "capacity": table.capacity,

            "zone": table.zone,

            "status": (
                session.status
                if session and session.status in ("PAID", "CLEAN")
                else "OCCUPIED"
                if session
                else "FREE"
            ),

            "session_id": (
                str(session.id)
                if session
                else None
            ),

            "session_opened_at": (
                session.opened_at
                if session
                else None
            ),
            "paid_at": (
                db.query(CashPayment.paid_at)
                .filter(CashPayment.session_id == session.id)
                .order_by(CashPayment.paid_at.desc())
                .limit(1)
                .scalar()
                if session and session.status in ("PAID", "CLEAN")
                else None
            ),
            "pending_delivery": pending_delivery,
            "can_mark_clean": bool(session and session.status == "PAID" and pending_delivery == 0),
            "last_served_at": (
                db.query(Order.served_at)
                .filter(
                    Order.session_id == session.id,
                    Order.served_at.isnot(None),
                    Order.status != "CANCELLED"
                )
                .order_by(Order.served_at.desc())
                .limit(1)
                .scalar()
                if session
                else None
            )
        })

    return result


# ==========================================================
# CREAR PEDIDO
# ==========================================================

@router.post("/orders")
def create_waiter_order(
    data: WaiterOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Crea/agrega productos a la comanda de una mesa.

    REGLA IMPORTANTE:

    Una sesión abierta = UNA SOLA COMANDA.

    Si la mesa ya tiene una comanda abierta y el mesero
    agrega otro pedido, NO se crea otra Order.

    Los nuevos platos se agregan a la Order existente.
    """

    # ======================================================
    # 1. VALIDAR QUE VENGA MESA O SESIÓN
    # ======================================================

    if not data.session_id and not data.table_id:
        raise HTTPException(
            status_code=400,
            detail="Debes indicar una mesa o una sesión."
        )

    # ======================================================
    # 2. BUSCAR SESIÓN EXISTENTE
    # ======================================================

    session = None

    if data.session_id:

        session = (
            db.query(RestaurantSession)
            .filter(
                RestaurantSession.id == data.session_id,
                RestaurantSession.status == "OPEN"
            )
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=404,
                detail="La sesión de la mesa no existe o ya está cerrada."
            )

    # ======================================================
    # 3. SI NO VIENE SESSION_ID, BUSCAR POR MESA
    # ======================================================

    if session is None:

        table = (
            db.query(Table)
            .filter(
                Table.id == data.table_id,
                Table.active.is_(True)
            )
            .first()
        )

        if not table:
            raise HTTPException(
                status_code=404,
                detail="La mesa no existe o está inactiva."
            )

        # Una mesa pagada todavía no está libre.
        # El cajero autoriza el pago y solamente después el mesero
        # puede confirmar que está limpia y liberarla.
        paid_session = (
            db.query(RestaurantSession)
            .filter(
                RestaurantSession.table_id == table.id,
                RestaurantSession.status == "PAID"
            )
            .first()
        )

        if paid_session:
            raise HTTPException(
                status_code=409,
                detail=(
                    "La mesa ya fue pagada. El mesero debe confirmar que "
                    "está limpia y liberarla antes de tomar un nuevo pedido."
                )
            )

        # MUY IMPORTANTE:
        # primero intentamos recuperar la sesión abierta.
        session = (
            db.query(RestaurantSession)
            .filter(
                RestaurantSession.table_id == table.id,
                RestaurantSession.status == "OPEN"
            )
            .first()
        )

        # ==================================================
        # 4. CREAR SESIÓN SOLAMENTE SI REALMENTE NO EXISTE
        # ==================================================

        if session is None:

            session = RestaurantSession(
                table_id=table.id,
                waiter_id=current_user.id,
                people=data.people,
                status="OPEN"
            )

            db.add(session)
            db.flush()

    # ======================================================
    # 5. BUSCAR LA COMANDA EXISTENTE
    # ======================================================
    #
    # ESTE ES EL PUNTO CLAVE.
    #
    # Toda la atención de una mesa pertenece a una sesión.
    #
    # Por lo tanto:
    #
    # session
    #    ↓
    # Order única
    #    ↓
    # muchos OrderItem
    #
    # ======================================================

    order = (
        db.query(Order)
        .filter(
            Order.session_id == session.id
        )
        .order_by(
            Order.created_at.asc()
        )
        .first()
    )

    # ======================================================
    # 6. SOLO CREAR COMANDA SI NO EXISTE
    # ======================================================

    if order is None:

        order = Order(
            session_id=session.id,
            status="OPEN",
            created_at=datetime.now(timezone.utc)
        )

        db.add(order)
        db.flush()

    else:

        # --------------------------------------------------
        # YA EXISTE LA COMANDA
        # --------------------------------------------------
        #
        # NO CREAMOS OTRA.
        #
        # Simplemente reabrimos la misma comanda porque
        # el cliente acaba de agregar productos.
        #

        order.status = "OPEN"
        order.served_at = None
        order.closed_at = None

    # ======================================================
    # 7. PREPARAR ESTACIONES
    # ======================================================

    batches = {}
    station_names = {}

    # ======================================================
    # 8. CREAR LOS NUEVOS ITEMS
    # ======================================================

    for requested in data.items:

        if not requested.dish_id and not requested.product_id:
            raise HTTPException(400, "Cada elemento debe tener un plato o producto.")
        if requested.dish_id and requested.product_id:
            raise HTTPException(400, "Cada elemento solo puede ser plato o producto.")

        if requested.dish_id:
            source = (
                db.query(Dish)
                .options(joinedload(Dish.station))
                .filter(
                    Dish.id == requested.dish_id,
                    Dish.active.is_(True),
                    Dish.available.is_(True)
                )
                .first()
            )
            if not source:
                raise HTTPException(404, "El plato no existe o no está disponible.")
            product_id = None
            dish_id = source.id
        else:
            source = (
                db.query(Product)
                .options(joinedload(Product.station))
                .filter(
                    Product.id == requested.product_id,
                    Product.active.is_(True)
                )
                .first()
            )
            if not source:
                raise HTTPException(404, "El producto no existe o está inactivo.")
            if source.stock < requested.quantity:
                raise HTTPException(409, f"Stock insuficiente para '{source.name}'. Disponible: {source.stock}.")
            product_id = source.id
            dish_id = None
            source.stock -= requested.quantity

        if not source.station_id:
            raise HTTPException(400, f"'{source.name}' no tiene estación asignada.")

        station_id = source.station_id
        station_key = str(station_id)

        item = OrderItem(
            order_id=order.id,
            product_id=product_id,
            dish_id=dish_id,
            quantity=requested.quantity,
            unit_price=source.price,
            total=source.price * requested.quantity,
            notes=requested.notes,
            status="PENDING"
        )

        db.add(item)
        db.flush()

        if station_key not in batches:
            batch = (
                db.query(OrderBatch)
                .filter(
                    OrderBatch.order_id == order.id,
                    OrderBatch.station_id == station_id
                )
                .first()
            )

            if batch is None:
                batch = OrderBatch(
                    order_id=order.id,
                    station_id=station_id,
                    status="PENDING"
                )
                db.add(batch)
                db.flush()
                db.add(KitchenTicket(
                    batch_id=batch.id,
                    station_id=station_id,
                    status="WAITING"
                ))
            else:
                batch.status = "PENDING"
                ticket = db.query(KitchenTicket).filter(KitchenTicket.batch_id == batch.id).first()
                if ticket:
                    ticket.status = "WAITING"
                else:
                    db.add(KitchenTicket(
                        batch_id=batch.id,
                        station_id=station_id,
                        status="WAITING"
                    ))

            batches[station_key] = batch
            station_names[station_key] = source.station.name if source.station else "Cocina"

        db.add(KitchenQueue(
            station_id=station_id,
            order_item_id=item.id,
            status="WAITING"
        ))

    # ======================================================
    # 9. GUARDAR TODO
    # ======================================================

    db.commit()
    db.refresh(order)

    # ======================================================
    # 10. RESPUESTA
    # ======================================================

    return {
        "message": (
            "Pedido agregado correctamente a la comanda."
            if order.created_at
            else "Pedido enviado correctamente."
        ),

        "order_id": str(order.id),

        "session_id": str(session.id),

        "table_id": str(session.table_id),

        "stations": [
            {
                "id": str(batch.station_id),
                "name": station_names.get(
                    str(batch.station_id),
                    "Cocina"
                )
            }
            for batch in batches.values()
        ],

        "status": order.status
    }

# ==========================================================
# PEDIDOS ACTIVOS
# ==========================================================

@router.get("/orders/active")
def active_waiter_orders(

    db: Session = Depends(get_db),

    current_user=Depends(
        get_current_user
    ),
):

    rows = (

        db.query(
            Order,
            RestaurantSession,
            Table
        )

        .join(
            RestaurantSession,
            RestaurantSession.id == Order.session_id
        )

        .join(
            Table,
            Table.id == RestaurantSession.table_id
        )

        .filter(

            RestaurantSession.waiter_id
            == current_user.id,

            RestaurantSession.status
            == "OPEN",

            Order.status.in_(
                [
                    "OPEN",
                    "PREPARING",
                    "READY",
                    "SERVED"
                ]
            )
        )

        .order_by(
            Order.created_at.desc()
        )

        .all()
    )

    result = []

    for order, session, table in rows:

        items = (

            db.query(OrderItem)

            .options(

                joinedload(
                    OrderItem.dish
                ),

                joinedload(
                    OrderItem.product
                )
            )

            .filter(
                OrderItem.order_id
                == order.id
            )

            .order_by(
                OrderItem.id.asc()
            )

            .all()
        )

        serialized_items = []

        for item in items:

            source = (
                item.dish
                or
                item.product
            )

            serialized_items.append({

                "id": str(
                    item.id
                ),

                "product_id": str(item.product_id) if item.product_id else None,
                "dish_id": str(item.dish_id) if item.dish_id else None,

                "name": (
                    source.name
                    if source
                    else "Producto"
                ),

                "quantity": item.quantity,

                "notes": item.notes,

                "status": item.status,

                "unit_price": float(
                    item.unit_price
                ),

                "total": float(
                    item.total
                )
            })

        total = sum(
            float(item.total or 0)
            for item in items
        )

        all_ready = (
            bool(items)
            and all(
                item.status == "READY"
                for item in items
            )
        )

        has_preparing = any(
            item.status in (
                "PENDING",
                "PREPARING"
            )
            for item in items
        )

        # ==================================================
        # CALCULAR ESTADO REAL
        # ==================================================

        if order.served_at:

            order_status = "SERVED"

        elif all_ready:

            order_status = "READY"

        elif has_preparing:

            order_status = "PREPARING"

        else:

            order_status = order.status

        # ==================================================
        # TIEMPO DE SESIÓN
        # ==================================================

        session_opened_at = (
            session.opened_at
        )

        result.append({

            "id": str(
                order.id
            ),

            "session_id": str(
                session.id
            ),

            "table_id": table.id,

            "table_number": table.number,

            "table_name": table.name,

            "status": order_status,

            "created_at": order.created_at,

            "closed_at": order.closed_at,

            "served_at": order.served_at,

            "session_opened_at": (
                session_opened_at
            ),

            "total": total,

            "items": serialized_items
        })

    return result


# ==========================================================
# ENTREGAR PEDIDO
# ==========================================================

@router.patch("/orders/{order_id}/items/{item_id}/serve")
def serve_order_item(
    order_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Entrega únicamente un producto que ya está listo."""
    order = (
        db.query(Order)
        .join(RestaurantSession, RestaurantSession.id == Order.session_id)
        .filter(
            Order.id == order_id,
            RestaurantSession.waiter_id == current_user.id,
            RestaurantSession.status == "OPEN"
        ).first()
    )
    if not order:
        raise HTTPException(404, "No se encontró el pedido.")

    item = db.query(OrderItem).filter(
        OrderItem.id == item_id,
        OrderItem.order_id == order.id
    ).first()
    if not item:
        raise HTTPException(404, "Producto de la comanda no encontrado.")
    if item.status == "SERVED":
        return {"message": "Producto ya entregado.", "item_id": str(item.id), "status": "SERVED"}
    if item.status != "READY":
        raise HTTPException(400, "Este producto todavía no está listo en cocina.")

    item.status = "SERVED"
    db.commit()
    return {"message": "Producto entregado.", "item_id": str(item.id), "status": "SERVED"}


@router.patch("/orders/{order_id}/serve")
def serve_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Confirma que toda la comanda ya fue entregada. No entrega productos por sí sola."""
    order = (
        db.query(Order)
        .join(RestaurantSession, RestaurantSession.id == Order.session_id)
        .filter(
            Order.id == order_id,
            RestaurantSession.waiter_id == current_user.id,
            RestaurantSession.status == "OPEN"
        ).first()
    )
    if not order:
        raise HTTPException(404, "No se encontró el pedido.")
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    items = [item for item in items if item.status != "CANCELLED"]
    if not items:
        raise HTTPException(400, "El pedido no tiene productos.")
    pending = [item for item in items if item.status != "SERVED"]
    if pending:
        raise HTTPException(400, "Entrega primero todos los productos listos y luego confirma la entrega total.")

    served_at = datetime.now(timezone.utc)
    order.status = "SERVED"
    order.served_at = served_at
    db.commit()
    db.refresh(order)
    return {"message": "Toda la comanda fue entregada correctamente.", "order_id": str(order.id), "status": "SERVED", "served_at": order.served_at}


# ==========================================================
# CERRAR / LIBERAR MESA
# ==========================================================

@router.patch("/sessions/{session_id}/clean")
def mark_table_clean(
    session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """El mesero solo marca la mesa como LIMPIA. Nunca la libera."""

    # La autorización de pago pertenece a Caja.
    # El mesero puede marcar como limpia cualquier mesa pagada que esté
    # atendiendo; NO puede liberarla. La liberación sigue siendo exclusiva
    # de Caja. No exigimos que el waiter_id coincida porque el panel de
    # mesas muestra las mesas del salón y una mesa puede ser atendida por
    # otro mesero durante el servicio.
    session = (
        db.query(RestaurantSession)
        .filter(
            RestaurantSession.id == session_id,
            RestaurantSession.status == "PAID"
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="La mesa no está pendiente de limpieza o el pago aún no fue autorizado por Caja."
        )

    orders = db.query(Order).filter(Order.session_id == session.id).all()
    pending_orders = [
        order for order in orders
        if order.status != "CANCELLED" and not order.served_at
    ]

    if pending_orders:
        raise HTTPException(
            status_code=400,
            detail="No puedes marcar la mesa como limpia hasta entregar todos los pedidos."
        )

    session.status = "CLEAN"
    db.commit()

    return {
        "message": "Mesa marcada como limpia. Caja debe liberarla.",
        "session_id": str(session.id),
        "table_id": session.table_id,
        "status": "CLEAN"
    }


# Ruta antigua: se conserva para evitar errores de clientes antiguos, pero
# deliberadamente ya no permite que el mesero libere la mesa.
@router.patch("/sessions/{session_id}/close")
def waiter_close_disabled(
    session_id: str,
    current_user=Depends(get_current_user),
):
    raise HTTPException(
        status_code=403,
        detail="El mesero no puede liberar la mesa. Debe marcarla como limpia; Caja realiza la liberación."
    )


# ==========================================================
# HISTORIAL DE PEDIDOS
# ==========================================================

@router.get("/orders/history")
def waiter_order_history(

    db: Session = Depends(get_db),

    current_user=Depends(
        get_current_user
    ),
):

    rows = (

        db.query(
            Order,
            RestaurantSession,
            Table
        )

        .join(
            RestaurantSession,
            RestaurantSession.id == Order.session_id
        )

        .join(
            Table,
            Table.id == RestaurantSession.table_id
        )

        .filter(

            RestaurantSession.waiter_id
            == current_user.id,

            Order.status.in_(
                [
                    "SERVED",
                    "CLOSED"
                ]
            )
        )

        .order_by(
            Order.created_at.desc()
        )

        .all()
    )

    result = []

    for order, session, table in rows:

        items = (

            db.query(OrderItem)

            .options(

                joinedload(
                    OrderItem.dish
                ),

                joinedload(
                    OrderItem.product
                )
            )

            .filter(
                OrderItem.order_id
                == order.id
            )

            .all()
        )

        total = sum(
            float(item.total or 0)
            for item in items
        )

        result.append({

            "id": str(
                order.id
            ),

            "session_id": str(
                session.id
            ),

            "table_id": table.id,

            "table_number": table.number,

            "table_name": table.name,

            "status": order.status,

            "created_at": order.created_at,

            "served_at": order.served_at,

            "closed_at": order.closed_at,

            "total": total,

            "items": [

                {

                    "id": str(
                        item.id
                    ),

                    "name": (
                        item.dish.name
                        if item.dish
                        else (
                            item.product.name
                            if item.product
                            else "Producto"
                        )
                    ),

                    "quantity": item.quantity,

                    "unit_price": float(
                        item.unit_price
                    ),

                    "total": float(
                        item.total
                    ),

                    "notes": item.notes
                }

                for item in items
            ]
        })

    return result