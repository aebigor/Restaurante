from datetime import datetime, timezone

from decimal import Decimal

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db

from app.core.dependencies import get_current_user

from app.modules.sessions.model import Session as RestaurantSession

from app.modules.tables.model import Table

from app.modules.orders.model import Order

from app.modules.order_items.model import OrderItem
from app.modules.order_batches.service import OrderBatchService
from app.modules.kitchen_queue.model import KitchenQueue
from app.modules.dishes.model import Dish

from .model import (
    CashRegister,
    CashPayment
)

from .schemas import (
    CashRegisterOpen,
    CashRegisterClose,
    CashPaymentCreate
)
from app.modules.delivery.schemas import PaymentClose


router = APIRouter(
    prefix="/api/cashier",
    tags=["Cashier"]
)


def _online_order_payload(db: Session, order: Order):
    items = (
        db.query(OrderItem)
        .options(joinedload(OrderItem.dish), joinedload(OrderItem.product))
        .filter(OrderItem.order_id == order.id)
        .all()
    )
    return {
        "id": str(order.id),
        "short_id": str(order.id)[:8].upper(),
        "status": order.status,
        "order_type": order.order_type,
        "customer": {
            "id": str(order.customer_id) if order.customer_id else None,
            "name": order.customer.full_name if order.customer else "Cliente",
            "email": order.customer.email if order.customer else None,
        },
        "created_at": order.created_at,
        "notes": order.notes,
        "delivery_address": order.delivery_address,
        "delivery_phone": order.delivery_phone,
        "delivery_fee": float(order.delivery_fee or 0),
        "courier_id": str(order.courier_id) if order.courier_id else None,
        "courier_name": order.courier.full_name if order.courier else None,
        "dispatched_at": order.dispatched_at,
        "courier_delivered_at": order.courier_delivered_at,
        "items": [
            {
                "id": str(item.id),
                "name": item.dish.name if item.dish else item.product.name if item.product else "Producto",
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total": item.total,
            }
            for item in items
        ],
        "total": sum(Decimal(str(item.total or 0)) for item in items),
    }


@router.get("/online-orders")
def online_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "Caja":
        raise HTTPException(403, "Solo Caja puede gestionar pedidos online.")
    orders = (
        db.query(Order)
        .options(joinedload(Order.customer))
        .filter(
            Order.customer_id.isnot(None),
            Order.order_type.in_(["ONLINE", "DOMICILIO"]),
            Order.status.in_(["PENDING_CASHIER", "OPEN", "PREPARING", "READY", "OUT_FOR_DELIVERY", "DELIVERED_PENDING_PAYMENT"])
        )
        .order_by(Order.created_at.asc())
        .limit(100)
        .all()
    )
    return [_online_order_payload(db, order) for order in orders]


@router.patch("/online-orders/{order_id}/confirm")
def confirm_online_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "Caja":
        raise HTTPException(403, "Solo Caja puede confirmar pedidos online.")
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id.isnot(None)).first()
    if not order:
        raise HTTPException(404, "Pedido online no encontrado.")
    if order.status != "PENDING_CASHIER":
        raise HTTPException(409, f"El pedido ya está en estado {order.status}.")

    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    if not items:
        raise HTTPException(409, "El pedido no tiene productos.")

    batch_service = OrderBatchService()
    for item in items:
        dish = item.dish or db.query(Dish).filter(Dish.id == item.dish_id).first()
        if not dish or not dish.station_id:
            raise HTTPException(409, "Uno de los productos no tiene estación de cocina configurada.")
        batch_service.get_or_create(db, order.id, dish.station_id)
        exists = db.query(KitchenQueue).filter(KitchenQueue.order_item_id == item.id).first()
        if not exists:
            db.add(KitchenQueue(station_id=dish.station_id, order_item_id=item.id, status="WAITING", created_at=datetime.utcnow()))
        item.status = "PENDING"

    order.status = "OPEN"
    order.cashier_confirmed_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Pedido confirmado y enviado a cocina.", "order_id": str(order.id), "status": order.status}


@router.patch("/online-orders/{order_id}/dispatch")
def dispatch_online_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "Caja":
        raise HTTPException(403, "Solo Caja puede marcar un domicilio en camino.")
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id.isnot(None)).first()
    if not order:
        raise HTTPException(404, "Pedido online no encontrado.")
    if order.order_type != "DOMICILIO":
        raise HTTPException(400, "Solo los domicilios pueden pasar a estado En camino.")
    if order.status != "READY":
        raise HTTPException(409, "El pedido debe estar listo antes de salir a domicilio.")
    # La salida real la registra el Domiciliario al tomar la entrega.
    return {"message": "Pedido listo para que un domiciliario lo tome.", "order_id": str(order.id), "status": order.status}


@router.patch("/online-orders/{order_id}/close-payment")
def close_online_payment(
    order_id: UUID,
    data: PaymentClose,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "Caja":
        raise HTTPException(403, "Solo Caja puede cerrar el pedido y registrar el pago.")
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id.isnot(None)).first()
    if not order:
        raise HTTPException(404, "Pedido online no encontrado.")
    if order.status != "DELIVERED_PENDING_PAYMENT":
        raise HTTPException(409, "El domiciliario debe validar primero la entrega con el código del cliente.")
    method = (data.payment_method or "CASH").upper()
    if method not in {"CASH", "CARD", "TRANSFER"}:
        raise HTTPException(400, "Método de pago inválido.")
    now = datetime.now(timezone.utc)
    order.payment_method = method
    order.payment_confirmed_at = now
    order.status = "CLOSED"
    order.closed_at = now
    db.commit()
    return {"message":"Pago registrado y pedido cerrado por Caja.","order_id":str(order.id),"status":order.status,"payment_method":method}


# ==========================================================
# UTILIDAD
# ==========================================================

def get_open_register(
    db: Session,
    cashier_id=None
):
    """Obtiene la caja abierta del cajero actual.

    Se permite más de una caja abierta en el restaurante, pero
    cada cajero opera únicamente su propio turno.
    """
    query = db.query(CashRegister).filter(
        CashRegister.status == "OPEN"
    )

    if cashier_id is not None:
        query = query.filter(
            CashRegister.opened_by == cashier_id
        )

    return query.order_by(
        CashRegister.opened_at.desc()
    ).first()


# ==========================================================
# CALCULAR CUENTA DE UNA SESIÓN
# ==========================================================

def calculate_session_total(
    db: Session,
    session_id
):

    orders = (
        db.query(Order)
        .filter(
            Order.session_id == session_id,
            Order.status != "CANCELLED"
        )
        .all()
    )

    total = Decimal("0")

    for order in orders:

        items = (
            db.query(OrderItem)
            .filter(
                OrderItem.order_id == order.id,
                OrderItem.status != "CANCELLED"
            )
            .all()
        )

        for item in items:

            total += Decimal(
                str(item.total or 0)
            )

    return total


# ==========================================================
# RESUMEN DE CAJA
# ==========================================================

@router.get("/summary")
def cashier_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    register = get_open_register(db, current_user.id)

    if not register:

        return {
            "register_open": False,
            "register": None,
            "tables": []
        }


    # ======================================================
    # TOTALES DE LA CAJA
    # ======================================================

    payments = (
        db.query(CashPayment)
        .filter(
            CashPayment.cash_register_id
            == register.id
        )
        .all()
    )


    cash_total = Decimal("0")
    card_total = Decimal("0")
    transfer_total = Decimal("0")


    for payment in payments:

        amount = Decimal(
            str(payment.amount or 0)
        )

        if payment.method == "CASH":

            cash_total += amount

        elif payment.method == "CARD":

            card_total += amount

        elif payment.method == "TRANSFER":

            transfer_total += amount


    expected_cash = (
        Decimal(
            str(register.opening_amount or 0)
        )
        +
        cash_total
    )


    # ======================================================
    # MESAS OCUPADAS
    # ======================================================

    sessions = (
        db.query(
            RestaurantSession,
            Table
        )
        .join(
            Table,
            Table.id == RestaurantSession.table_id
        )
        .filter(
            RestaurantSession.status.in_(["OPEN", "PAID", "CLEAN"])
        )
        .order_by(
            Table.number.asc()
        )
        .all()
    )


    tables = []


    for session, table in sessions:

        total = calculate_session_total(
            db,
            session.id
        )


        paid = (
            db.query(CashPayment)
            .filter(
                CashPayment.session_id
                == session.id
            )
            .all()
        )


        paid_total = sum(
            (
                Decimal(
                    str(payment.amount or 0)
                )
                for payment in paid
            ),
            Decimal("0")
        )


        balance = max(
            Decimal("0"),
            total - paid_total
        )


        tables.append({

            "table_id": table.id,

            "table_number": table.number,

            "table_name": table.name,

            "zone": table.zone,

            "session_id": str(
                session.id
            ),

            "people": session.people,

            "opened_at": session.opened_at,

            "total": total,

            "paid": paid_total,

            "balance": balance,

            "status": session.status,

            "paid_at": (
                db.query(CashPayment.paid_at)
                .filter(CashPayment.session_id == session.id)
                .order_by(CashPayment.paid_at.desc())
                .limit(1)
                .scalar()
            )

        })


    return {

        "register_open": True,

        "register": {

            "id": str(register.id),

            "opening_amount":
                register.opening_amount,

            "cash_sales":
                cash_total,

            "card_sales":
                card_total,

            "transfer_sales":
                transfer_total,

            "total_sales":
                cash_total
                + card_total
                + transfer_total,

            "expected_cash":
                expected_cash,

            "opened_at":
                register.opened_at

        },

        "tables": tables

    }


# ==========================================================
# RESUMEN ADMINISTRATIVO DE CAJAS Y GANANCIAS
# ==========================================================

@router.get("/admin-summary")
def admin_cash_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if not current_user.role or current_user.role.name != "Administrador":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador puede consultar este resumen."
        )

    from datetime import date

    today = date.today()

    # ------------------------------------------------------
    # VENTAS DEL DÍA
    # ------------------------------------------------------
    payments_today = (
        db.query(CashPayment)
        .filter(func.date(CashPayment.paid_at) == today)
        .all()
    )

    sales_today = sum(
        (Decimal(str(p.amount or 0)) for p in payments_today),
        Decimal("0")
    )

    cash_today = sum(
        (Decimal(str(p.amount or 0)) for p in payments_today if p.method == "CASH"),
        Decimal("0")
    )
    card_today = sum(
        (Decimal(str(p.amount or 0)) for p in payments_today if p.method == "CARD"),
        Decimal("0")
    )
    transfer_today = sum(
        (Decimal(str(p.amount or 0)) for p in payments_today if p.method == "TRANSFER"),
        Decimal("0")
    )

    orders_today = (
        db.query(Order)
        .filter(
            func.date(Order.created_at) == today,
            Order.status != "CANCELLED"
        )
        .count()
    )

    # Sesiones que ya fueron cobradas hoy, aunque todavía estén
    # esperando que el mesero confirme que la mesa quedó limpia.
    paid_sessions_today = (
        db.query(RestaurantSession)
        .join(
            CashPayment,
            CashPayment.session_id == RestaurantSession.id
        )
        .filter(func.date(CashPayment.paid_at) == today)
        .distinct()
        .count()
    )

    # ------------------------------------------------------
    # CAJAS ABIERTAS
    # ------------------------------------------------------
    open_registers = (
        db.query(CashRegister)
        .options(joinedload(CashRegister.opened_by_user))
        .filter(CashRegister.status == "OPEN")
        .order_by(CashRegister.opened_at.asc())
        .all()
    )

    # ------------------------------------------------------
    # CAJAS CERRADAS HOY + CUENTA DE CADA CAJA
    # ------------------------------------------------------
    closed_registers = (
        db.query(CashRegister)
        .options(joinedload(CashRegister.opened_by_user))
        .filter(
            CashRegister.status == "CLOSED",
            func.date(CashRegister.closed_at) == today
        )
        .order_by(CashRegister.closed_at.desc())
        .all()
    )

    def register_totals(register):
        payments = (
            db.query(CashPayment)
            .filter(CashPayment.cash_register_id == register.id)
            .all()
        )
        cash = sum(
            (Decimal(str(p.amount or 0)) for p in payments if p.method == "CASH"),
            Decimal("0")
        )
        card = sum(
            (Decimal(str(p.amount or 0)) for p in payments if p.method == "CARD"),
            Decimal("0")
        )
        transfer = sum(
            (Decimal(str(p.amount or 0)) for p in payments if p.method == "TRANSFER"),
            Decimal("0")
        )
        return cash, card, transfer, cash + card + transfer, len(payments)

    def serialize_register(register, status):
        cash, card, transfer, total, payment_count = register_totals(register)
        return {
            "id": str(register.id),
            "status": status,
            "opened_by": (
                register.opened_by_user.full_name
                if register.opened_by_user
                else "Sin usuario"
            ),
            "opened_at": register.opened_at,
            "closed_at": register.closed_at,
            "opening_amount": register.opening_amount,
            "cash_sales": cash,
            "card_sales": card,
            "transfer_sales": transfer,
            "total_sales": total,
            "payment_count": payment_count,
            "expected_cash": register.expected_cash,
            "closing_amount": register.closing_amount,
            "difference": register.difference,
        }

    return {
        "date": today.isoformat(),
        "sales_today": sales_today,
        "cash_today": cash_today,
        "card_today": card_today,
        "transfer_today": transfer_today,
        "payments_today": len(payments_today),
        "orders_today": orders_today,
        "paid_sessions_today": paid_sessions_today,
        "open_registers": len(open_registers),
        "closed_registers_today": len(closed_registers),
        "registers": [serialize_register(r, "OPEN") for r in open_registers],
        "closed_registers": [serialize_register(r, "CLOSED") for r in closed_registers],
    }


# ==========================================================
# ABRIR CAJA
# ==========================================================

@router.post("/register/open")
def open_register(
    data: CashRegisterOpen,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    existing = get_open_register(db, current_user.id)

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Este cajero ya tiene una caja abierta."
        )


    register = CashRegister(

        opened_by=current_user.id,

        opening_amount=data.opening_amount,

        status="OPEN"

    )


    db.add(register)

    db.commit()

    db.refresh(register)


    return {

        "message":
            "Caja abierta correctamente.",

        "register_id":
            str(register.id),

        "opening_amount":
            register.opening_amount

    }


# ==========================================================
# CUENTA DE UNA MESA
# ==========================================================

@router.get("/sessions/{session_id}/account")
def session_account(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    session = (
        db.query(RestaurantSession)
        .options(
            joinedload(
                RestaurantSession.table
            )
        )
        .filter(
            RestaurantSession.id == session_id,
            RestaurantSession.status.in_(["OPEN", "PAID", "CLEAN"])
        )
        .first()
    )


    if not session:

        raise HTTPException(
            status_code=404,
            detail="La cuenta ya no está abierta."
        )


    table = session.table


    orders = (
        db.query(Order)
        .filter(
            Order.session_id == session.id,
            Order.status != "CANCELLED"
        )
        .order_by(
            Order.created_at.asc()
        )
        .all()
    )


    result_orders = []

    total = Decimal("0")


    for order in orders:

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
                OrderItem.order_id == order.id,
                OrderItem.status != "CANCELLED"
            )
            .all()
        )


        result_items = []


        for item in items:

            source = (
                item.dish
                or
                item.product
            )


            item_total = Decimal(
                str(item.total or 0)
            )


            total += item_total


            result_items.append({

                "id": str(item.id),

                "name": (
                    source.name
                    if source
                    else "Producto"
                ),

                "quantity":
                    item.quantity,

                "unit_price":
                    item.unit_price,

                "total":
                    item.total,

                "notes":
                    item.notes

            })


        result_orders.append({

            "id": str(order.id),

            "status":
                order.status,

            "created_at":
                order.created_at,

            "items":
                result_items

        })


    payments = (
        db.query(CashPayment)
        .filter(
            CashPayment.session_id
            == session.id
        )
        .order_by(
            CashPayment.paid_at.asc()
        )
        .all()
    )


    paid = sum(
        (
            Decimal(
                str(payment.amount or 0)
            )
            for payment in payments
        ),
        Decimal("0")
    )


    balance = max(
        Decimal("0"),
        total - paid
    )


    return {

        "session_id":
            str(session.id),

        "table": {

            "id":
                table.id,

            "number":
                table.number,

            "name":
                table.name,

            "zone":
                table.zone

        },

        "people":
            session.people,

        "opened_at":
            session.opened_at,

        "orders":
            result_orders,

        "total":
            total,

        "paid":
            paid,

        "balance":
            balance,

        "payments": [

            {

                "id":
                    str(payment.id),

                "method":
                    payment.method,

                "amount":
                    payment.amount,

                "paid_at":
                    payment.paid_at

            }

            for payment in payments

        ]

    }


# ==========================================================
# COBRAR CUENTA
# ==========================================================

@router.post("/payments")
def pay_session(
    data: CashPaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    register = get_open_register(db, current_user.id)


    if not register:

        raise HTTPException(
            status_code=400,
            detail="Primero debes abrir la caja."
        )


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
            detail="La mesa no tiene una cuenta abierta."
        )


    total = calculate_session_total(
        db,
        session.id
    )


    previous_payments = (
        db.query(CashPayment)
        .filter(
            CashPayment.session_id
            == session.id
        )
        .all()
    )


    already_paid = sum(
        (
            Decimal(
                str(payment.amount or 0)
            )
            for payment in previous_payments
        ),
        Decimal("0")
    )


    balance = max(
        Decimal("0"),
        total - already_paid
    )


    if balance <= 0:

        raise HTTPException(
            status_code=400,
            detail="Esta cuenta ya está pagada."
        )


    method = data.method.upper().strip()


    allowed_methods = {
        "CASH",
        "CARD",
        "TRANSFER"
    }


    if method not in allowed_methods:

        raise HTTPException(
            status_code=400,
            detail=(
                "Método de pago inválido. "
                "Usa CASH, CARD o TRANSFER."
            )
        )


    received = Decimal(
        str(data.received_amount)
    )


    change = Decimal("0")


    # ======================================================
    # EFECTIVO
    # ======================================================

    if method == "CASH":

        if received < balance:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El efectivo recibido "
                    "es menor al total."
                )
            )


        change = received - balance


    # ======================================================
    # TARJETA / TRANSFERENCIA
    # ======================================================

    else:

        if received != balance:

            received = balance


    payment = CashPayment(

        cash_register_id=register.id,

        session_id=session.id,

        cashier_id=current_user.id,

        method=method,

        amount=balance,

        received_amount=received,

        change_amount=change,

        reference=data.reference

    )


    db.add(payment)


    # ======================================================
    # CERRAR PEDIDOS
    # ======================================================

    now = datetime.now(
        timezone.utc
    )


    orders = (
        db.query(Order)
        .filter(
            Order.session_id == session.id
        )
        .all()
    )


    for order in orders:

        if order.status != "CANCELLED":

            order.status = "CLOSED"

            order.closed_at = now


    # ======================================================
    # AUTORIZAR PAGO SIN LIBERAR LA MESA
    # ======================================================
    #
    # La caja es la única que confirma que la cuenta fue pagada.
    # La sesión permanece abierta en estado PAID para que el mesero
    # pueda comprobar que la mesa ya quedó limpia y liberarla.

    session.status = "PAID"


    db.commit()

    db.refresh(payment)


    return {

        "message":
            "Cuenta cobrada correctamente.",

        "payment_id":
            str(payment.id),

        "session_id":
            str(session.id),

        "table_id":
            session.table_id,

        "total":
            balance,

        "method":
            method,

        "received_amount":
            received,

        "change_amount":
            change,

        "status":
            "PAID"

    }


# ==========================================================
# LIBERAR MESA DESDE CAJA
# ==========================================================

@router.patch("/sessions/{session_id}/release")
def release_table_from_cashier(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if not current_user.role or current_user.role.name != "Caja":
        raise HTTPException(
            status_code=403,
            detail="Solo Caja puede liberar una mesa."
        )

    session = (
        db.query(RestaurantSession)
        .filter(
            RestaurantSession.id == session_id,
            RestaurantSession.status == "CLEAN"
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=409,
            detail="La mesa debe estar pagada y marcada como limpia por el mesero antes de liberarla."
        )

    now = datetime.now(timezone.utc)
    orders = db.query(Order).filter(Order.session_id == session.id).all()

    for order in orders:
        if order.status != "CANCELLED":
            order.status = "CLOSED"
            order.closed_at = now

    session.status = "CLOSED"
    session.closed_at = now

    db.commit()

    return {
        "message": "Mesa liberada correctamente por Caja.",
        "session_id": str(session.id),
        "table_id": session.table_id,
        "status": "CLOSED",
        "closed_at": session.closed_at
    }


# ==========================================================
# CERRAR CAJA
# ==========================================================

@router.post("/register/close")
def close_register(
    data: CashRegisterClose,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    register = get_open_register(db, current_user.id)


    if not register:

        raise HTTPException(
            status_code=400,
            detail="No hay una caja abierta."
        )


    # ======================================================
    # NO CERRAR CAJA SI HAY CUENTAS PENDIENTES
    # ======================================================

    open_sessions = (
        db.query(RestaurantSession)
        .filter(
            RestaurantSession.status == "OPEN"
        )
        .all()
    )


    for session in open_sessions:

        total = calculate_session_total(
            db,
            session.id
        )


        paid = sum(
            (
                Decimal(
                    str(payment.amount or 0)
                )
                for payment in db.query(CashPayment)
                .filter(
                    CashPayment.session_id
                    == session.id
                )
                .all()
            ),
            Decimal("0")
        )


        if total > paid:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No puedes cerrar la caja porque "
                    "todavía existen cuentas pendientes."
                )
            )


    # ======================================================
    # CALCULAR EFECTIVO ESPERADO
    # ======================================================

    cash_sales = sum(
        (
            Decimal(
                str(payment.amount or 0)
            )
            for payment in db.query(CashPayment)
            .filter(
                CashPayment.cash_register_id
                == register.id,
                CashPayment.method == "CASH"
            )
            .all()
        ),
        Decimal("0")
    )


    expected_cash = (
        Decimal(
            str(register.opening_amount or 0)
        )
        +
        cash_sales
    )


    closing_amount = Decimal(
        str(data.closing_amount)
    )


    difference = (
        closing_amount -
        expected_cash
    )


    # ======================================================
    # CERRAR
    # ======================================================

    register.status = "CLOSED"

    register.closed_at = datetime.now(
        timezone.utc
    )

    register.closing_amount = (
        closing_amount
    )

    register.expected_cash = (
        expected_cash
    )

    register.difference = (
        difference
    )


    db.commit()

    db.refresh(register)


    return {

        "message":
            "Caja cerrada correctamente.",

        "register_id":
            str(register.id),

        "expected_cash":
            expected_cash,

        "closing_amount":
            closing_amount,

        "difference":
            difference,

        "status":
            "CLOSED"

    }


# ==========================================================
# HISTORIAL DE PAGOS
# ==========================================================

@router.get("/payments/history")
def payment_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    payments = (
        db.query(CashPayment)
        .options(
            joinedload(
                CashPayment.session
            )
            .joinedload(
                RestaurantSession.table
            )
        )
        .order_by(
            CashPayment.paid_at.desc()
        )
        .limit(100)
        .all()
    )


    return [

        {

            "id":
                str(payment.id),

            "session_id":
                str(payment.session_id),

            "table_number":
                (
                    payment.session.table.number
                    if payment.session
                    and payment.session.table
                    else None
                ),

            "method":
                payment.method,

            "amount":
                payment.amount,

            "received_amount":
                payment.received_amount,

            "change_amount":
                payment.change_amount,

            "reference":
                payment.reference,

            "paid_at":
                payment.paid_at

        }

        for payment in payments

    ]