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
from app.modules.tables.model import Table

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

    dishes.sort(
        key=lambda dish: (
            dish["category"] or "",
            dish["display_order"],
            dish["name"].lower()
        )
    )

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

        "dishes": dishes
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
                RestaurantSession.status == "OPEN"
            )
            .all()
        )
    }

    result = []

    for table in tables:

        session = open_sessions.get(
            table.id
        )

        result.append({

            "id": table.id,

            "number": table.number,

            "name": table.name,

            "capacity": table.capacity,

            "zone": table.zone,

            "status": (
                "OCCUPIED"
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
            status="OPEN"
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

        dish = (
            db.query(Dish)
            .options(
                joinedload(Dish.station)
            )
            .filter(
                Dish.id == requested.dish_id,
                Dish.active.is_(True),
                Dish.available.is_(True)
            )
            .first()
        )

        if not dish:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"El plato {requested.dish_id} "
                    "no existe o no está disponible."
                )
            )

        # ==================================================
        # VALIDAR ESTACIÓN
        # ==================================================

        if not dish.station_id:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"El plato '{dish.name}' "
                    "no tiene estación de cocina asignada."
                )
            )

        station_id = dish.station_id
        station_key = str(station_id)

        # ==================================================
        # CREAR ITEM DENTRO DE LA MISMA COMANDA
        # ==================================================

        item = OrderItem(
            order_id=order.id,
            dish_id=dish.id,
            quantity=requested.quantity,
            unit_price=dish.price,
            total=dish.price * requested.quantity,
            notes=requested.notes,
            status="PENDING"
        )

        db.add(item)
        db.flush()

        # ==================================================
        # BATCH DE LA ESTACIÓN
        # ==================================================

        if station_key not in batches:

            batch = (
                db.query(OrderBatch)
                .filter(
                    OrderBatch.order_id == order.id,
                    OrderBatch.station_id == station_id
                )
                .first()
            )

            # --------------------------------------------------
            # SI LA COMANDA NUNCA HABÍA IDO A ESTA ESTACIÓN
            # --------------------------------------------------

            if batch is None:

                batch = OrderBatch(
                    order_id=order.id,
                    station_id=station_id,
                    status="PENDING"
                )

                db.add(batch)
                db.flush()

                ticket = KitchenTicket(
                    batch_id=batch.id,
                    station_id=station_id,
                    status="WAITING"
                )

                db.add(ticket)

            # --------------------------------------------------
            # SI YA EXISTÍA EL BATCH
            # --------------------------------------------------

            else:

                batch.status = "PENDING"

                ticket = (
                    db.query(KitchenTicket)
                    .filter(
                        KitchenTicket.batch_id == batch.id
                    )
                    .first()
                )

                if ticket:

                    ticket.status = "WAITING"

                else:

                    ticket = KitchenTicket(
                        batch_id=batch.id,
                        station_id=station_id,
                        status="WAITING"
                    )

                    db.add(ticket)

            batches[station_key] = batch

            station_names[station_key] = (
                dish.station.name
                if dish.station
                else "Cocina"
            )

        # ==================================================
        # AGREGAR EL NUEVO PLATO A LA COLA DE COCINA
        # ==================================================

        queue = KitchenQueue(
            station_id=station_id,
            order_item_id=item.id,
            status="WAITING"
        )

        db.add(queue)

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

@router.patch("/orders/{order_id}/serve")
def serve_order(

    order_id: str,

    db: Session = Depends(get_db),

    current_user=Depends(
        get_current_user
    ),
):

    order = (

        db.query(Order)

        .join(
            RestaurantSession,
            RestaurantSession.id == Order.session_id
        )

        .filter(

            Order.id == order_id,

            RestaurantSession.waiter_id
            == current_user.id,

            RestaurantSession.status
            == "OPEN"
        )

        .first()
    )

    if not order:

        raise HTTPException(
            status_code=404,
            detail="No se encontró el pedido."
        )

    if order.served_at:

        return {

            "message": "El pedido ya fue entregado.",

            "order_id": str(
                order.id
            ),

            "status": "SERVED",

            "served_at": order.served_at
        }

    # ======================================================
    # VERIFICAR QUE TODO ESTÉ LISTO
    # ======================================================

    items = (
        db.query(OrderItem)
        .filter(
            OrderItem.order_id == order.id
        )
        .all()
    )

    if not items:

        raise HTTPException(
            status_code=400,
            detail="El pedido no tiene productos."
        )

    not_ready = [
        item
        for item in items
        if item.status != "READY"
    ]

    if not_ready:

        raise HTTPException(
            status_code=400,
            detail=(
                "No puedes entregar el pedido "
                "porque todavía hay productos "
                "que no están listos."
            )
        )

    # ======================================================
    # MARCAR COMO ENTREGADO
    # ======================================================

    served_at = datetime.now(
        timezone.utc
    )

    order.status = "SERVED"

    order.served_at = served_at

    # También dejamos los items como SERVED
    for item in items:

        item.status = "SERVED"

    db.commit()

    db.refresh(order)

    return {

        "message": (
            "Pedido entregado correctamente."
        ),

        "order_id": str(
            order.id
        ),

        "status": "SERVED",

        "served_at": order.served_at
    }


# ==========================================================
# CERRAR / LIBERAR MESA
# ==========================================================

@router.patch("/sessions/{session_id}/close")
def close_table_session(

    session_id: str,

    db: Session = Depends(get_db),

    current_user=Depends(
        get_current_user
    ),
):

    session = (

        db.query(RestaurantSession)

        .filter(

            RestaurantSession.id
            == session_id,

            RestaurantSession.waiter_id
            == current_user.id,

            RestaurantSession.status
            == "OPEN"
        )

        .first()
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail=(
                "No se encontró una sesión abierta "
                "para esta mesa."
            )
        )

    # ======================================================
    # BUSCAR TODAS LAS ÓRDENES
    # ======================================================

    orders = (
        db.query(Order)
        .filter(
            Order.session_id == session.id
        )
        .all()
    )

    # ======================================================
    # NO PERMITIR LIBERAR SI HAY PEDIDOS SIN ENTREGAR
    # ======================================================

    pending_orders = [

        order

        for order in orders

        if not order.served_at
        and order.status not in (
            "CLOSED",
            "CANCELLED"
        )
    ]

    if pending_orders:

        raise HTTPException(
            status_code=400,
            detail=(
                "No puedes liberar la mesa porque "
                "hay pedidos que todavía no han "
                "sido entregados."
            )
        )

    # ======================================================
    # CERRAR ÓRDENES
    # ======================================================

    closed_at = datetime.now(
        timezone.utc
    )

    for order in orders:

        if order.status != "CANCELLED":

            order.status = "CLOSED"

            order.closed_at = closed_at

    # ======================================================
    # CERRAR SESIÓN
    # ======================================================

    session.status = "CLOSED"

    session.closed_at = datetime.now()

    db.commit()

    return {

        "message": (
            "Mesa liberada correctamente."
        ),

        "session_id": str(
            session.id
        ),

        "table_id": session.table_id,

        "status": "CLOSED",

        "closed_at": session.closed_at
    }


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