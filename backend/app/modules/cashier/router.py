from datetime import datetime, timezone

from decimal import Decimal

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db

from app.core.dependencies import get_current_user

from app.modules.sessions.model import Session as RestaurantSession

from app.modules.tables.model import Table

from app.modules.orders.model import Order

from app.modules.order_items.model import OrderItem

from .model import (
    CashRegister,
    CashPayment
)

from .schemas import (
    CashRegisterOpen,
    CashRegisterClose,
    CashPaymentCreate
)


router = APIRouter(
    prefix="/api/cashier",
    tags=["Cashier"]
)


# ==========================================================
# UTILIDAD
# ==========================================================

def get_open_register(
    db: Session
):

    return (
        db.query(CashRegister)
        .filter(
            CashRegister.status == "OPEN"
        )
        .order_by(
            CashRegister.opened_at.desc()
        )
        .first()
    )


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

    register = get_open_register(db)

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
            RestaurantSession.status == "OPEN"
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

            "balance": balance

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
# ABRIR CAJA
# ==========================================================

@router.post("/register/open")
def open_register(
    data: CashRegisterOpen,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    existing = get_open_register(db)


    if existing:

        raise HTTPException(
            status_code=400,
            detail="Ya existe una caja abierta."
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
            RestaurantSession.status == "OPEN"
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

    register = get_open_register(db)


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
    # CERRAR SESIÓN / LIBERAR MESA
    # ======================================================

    session.status = "CLOSED"

    session.closed_at = now


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
# CERRAR CAJA
# ==========================================================

@router.post("/register/close")
def close_register(
    data: CashRegisterClose,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    register = get_open_register(db)


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