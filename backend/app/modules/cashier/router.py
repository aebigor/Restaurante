from datetime import datetime, timezone, timedelta

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
from app.modules.kitchen_tickets.model import KitchenTicket
from app.modules.order_batches.model import OrderBatch
from app.modules.dishes.model import Dish
from app.modules.products.model import Product

from .model import (
    CashRegister,
    CashPayment,
    CashRegisterMovement
)

from .schemas import (
    CashRegisterOpen,
    CashRegisterClose,
    CashRegisterClosingEdit,
    CashPaymentCreate,
    PrepaymentCodeVerify,
    CashRegisterWithdrawalCreate
)
from app.modules.delivery.schemas import PaymentClose
from app.modules.delivery.model import DeliveryPaymentProof


router = APIRouter(
    prefix="/api/cashier",
    tags=["Cashier"]
)


def _bogota_today():
    """Fecha calendario oficial de Colombia (UTC-5, sin horario de verano).

    Un desplazamiento fijo evita depender de tzdata en Windows.
    """
    bogota_tz = timezone(timedelta(hours=-5), name="America/Bogota")
    return datetime.now(bogota_tz).date()


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
        "total": sum(Decimal(str(item.total or 0)) for item in items) + Decimal(str(order.delivery_fee or 0)),
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

    method = (data.payment_method or order.payment_method or "CASH").strip().upper().replace(" ", "_")
    aliases = {
        "NEQUI": "TRANSFER_NEQUI",
        "BANCOLOMBIA": "TRANSFER_BANCOLOMBIA",
        "LLAVES": "TRANSFER_LLAVES",
        "LLAVE": "TRANSFER_LLAVES",
    }
    method = aliases.get(method, method)
    allowed = {"CASH", "CARD", "TRANSFER", "TRANSFER_NEQUI", "TRANSFER_BANCOLOMBIA", "TRANSFER_LLAVES"}
    if method not in allowed:
        raise HTTPException(400, "Método de pago inválido.")

    register = get_open_register(db, current_user.id)
    if not register:
        raise HTTPException(409, "Debes tener una caja abierta para registrar y cerrar esta venta.")

    proof = None
    if method.startswith("TRANSFER"):
        proof = (
            db.query(DeliveryPaymentProof)
            .filter(
                DeliveryPaymentProof.order_id == order.id,
                DeliveryPaymentProof.payment_method == method,
                DeliveryPaymentProof.status == "APPROVED",
            )
            .order_by(DeliveryPaymentProof.created_at.desc())
            .first()
        )
        if not proof:
            raise HTTPException(409, "Primero debes revisar y aprobar al menos un comprobante de esta transferencia.")

    existing = db.query(CashPayment).filter(CashPayment.order_id == order.id).first()
    if existing:
        raise HTTPException(409, "Esta venta ya fue registrada en Caja.")

    items_total = sum(
        (Decimal(str(row[0] or 0)) for row in db.query(func.sum(OrderItem.total)).filter(OrderItem.order_id == order.id).all()),
        Decimal("0")
    )
    total = items_total + Decimal(str(order.delivery_fee or 0))
    now = datetime.now(timezone.utc)
    payment = CashPayment(
        cash_register_id=register.id,
        session_id=None,
        order_id=order.id,
        cashier_id=current_user.id,
        method=method,
        amount=total,
        received_amount=total,
        change_amount=Decimal("0"),
        reference=f"DOMICILIO #{str(order.id)[:8].upper()}",
    )
    db.add(payment)
    order.payment_method = method
    order.payment_confirmed_at = now
    order.status = "CLOSED"
    order.closed_at = now
    db.commit()
    return {
        "message": "Pago registrado y pedido cerrado por Caja.",
        "order_id": str(order.id),
        "status": order.status,
        "payment_method": method,
        "amount": total,
        "proof_id": str(proof.id) if proof else None,
    }


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


    withdrawal_total = sum(
        (
            Decimal(str(m.amount or 0))
            for m in db.query(CashRegisterMovement)
            .filter(
                CashRegisterMovement.cash_register_id == register.id,
                CashRegisterMovement.movement_type == "WITHDRAWAL"
            )
            .all()
        ),
        Decimal("0")
    )

    expected_cash = (
        Decimal(str(register.opening_amount or 0))
        + cash_total
        - withdrawal_total
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
            ),
            "prepayment_required": bool(table.prepayment_required),
            "payment_pending": bool(table.prepayment_required and balance > 0 and db.query(Order).filter(
                Order.session_id == session.id,
                Order.status == "PENDING_PAYMENT"
            ).first()),
            "payment_pending_since": (
                db.query(Order.created_at)
                .filter(Order.session_id == session.id, Order.status == "PENDING_PAYMENT")
                .order_by(Order.created_at.asc())
                .limit(1)
                .scalar()
            )

        })


    tables.sort(key=lambda row: (not row.get("payment_pending", False), row.get("table_number", 0)))

    return {

        "register_open": True,

        "register": {

            "id": str(register.id),

            "opening_amount":
                register.opening_amount,

            "cash_sales":
                cash_total,

            "withdrawals":
                withdrawal_total,

            "cash_available":
                expected_cash,

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

    today = _bogota_today()

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
        (Decimal(str(p.amount or 0)) for p in payments_today if str(p.method or "").startswith("TRANSFER")),
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
        .options(
            joinedload(CashRegister.opened_by_user),
            joinedload(CashRegister.closing_amount_edited_by_user),
        )
        .filter(CashRegister.status == "OPEN")
        .order_by(CashRegister.opened_at.asc())
        .all()
    )

    # ------------------------------------------------------
    # CAJAS CERRADAS HOY + CUENTA DE CADA CAJA
    # ------------------------------------------------------
    closed_registers = (
        db.query(CashRegister)
        .options(
            joinedload(CashRegister.opened_by_user),
            joinedload(CashRegister.closing_amount_edited_by_user),
        )
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
            (Decimal(str(p.amount or 0)) for p in payments if str(p.method or "").startswith("TRANSFER")),
            Decimal("0")
        )
        return cash, card, transfer, cash + card + transfer, len(payments)

    def serialize_register(register, status):
        cash, card, transfer, total, payment_count = register_totals(register)
        withdrawal_rows = (
            db.query(CashRegisterMovement)
            .filter(
                CashRegisterMovement.cash_register_id == register.id,
                CashRegisterMovement.movement_type == "WITHDRAWAL"
            )
            .order_by(CashRegisterMovement.created_at.desc())
            .all()
        )
        withdrawal_total = sum(
            (Decimal(str(m.amount or 0)) for m in withdrawal_rows),
            Decimal("0")
        )
        movement_rows = [
            {
                "id": str(m.id),
                "type": m.movement_type,
                "amount": m.amount,
                "recipient_name": m.recipient_name,
                "recipient_document": m.recipient_document,
                "reason": m.reason,
                "created_at": m.created_at,
                "cashier_name": m.cashier.full_name if m.cashier else "Sin usuario",
            }
            for m in withdrawal_rows
        ]
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
            "withdrawals": withdrawal_total,
            "cash_available": Decimal(str(register.opening_amount or 0)) + cash - withdrawal_total,
            "withdrawal_count": len(withdrawal_rows),
            "movements": movement_rows,
            "card_sales": card,
            "transfer_sales": transfer,
            "total_sales": total,
            "payment_count": payment_count,
            "expected_cash": register.expected_cash,
            "closing_amount": register.closing_amount,
            "difference": register.difference,
            "closing_amount_edit_count": register.closing_amount_edit_count or 0,
            "closing_amount_edited_at": register.closing_amount_edited_at,
            "closing_amount_edited_by": (
                register.closing_amount_edited_by_user.full_name
                if register.closing_amount_edited_by_user
                else None
            ),
            "closing_amount_edit_reason": register.closing_amount_edit_reason,
            "closing_amount_edit_allowed": bool(
                status == "CLOSED"
                and register.closed_at
                and register.closed_at.astimezone(timezone(timedelta(hours=-5), name="America/Bogota")).date() == _bogota_today()
                and (register.closing_amount_edit_count or 0) == 0
            ),
        }

    pending_prepayment_rows = (
        db.query(RestaurantSession, Table)
        .join(Table, Table.id == RestaurantSession.table_id)
        .filter(
            RestaurantSession.status == "OPEN",
            Table.prepayment_required.is_(True)
        )
        .order_by(Table.number.asc())
        .all()
    )

    pending_prepayments = []
    for session, table in pending_prepayment_rows:
        pending_order = (
            db.query(Order)
            .filter(
                Order.session_id == session.id,
                Order.status == "PENDING_PAYMENT"
            )
            .order_by(Order.created_at.asc())
            .first()
        )
        if not pending_order:
            continue
        total = calculate_session_total(db, session.id)
        paid = sum(
            (Decimal(str(p.amount or 0)) for p in db.query(CashPayment).filter(CashPayment.session_id == session.id).all()),
            Decimal("0")
        )
        pending_prepayments.append({
            "session_id": str(session.id),
            "table_id": table.id,
            "table_number": table.number,
            "table_name": table.name,
            "zone": table.zone,
            "total": total,
            "balance": max(Decimal("0"), total - paid),
            "created_at": pending_order.created_at,
            "waiter_id": str(session.waiter_id) if session.waiter_id else None,
        })

    transfer_methods = {"TRANSFER", "TRANSFER_NEQUI", "TRANSFER_BANCOLOMBIA", "TRANSFER_LLAVES"}
    transfer_payments_today = [p for p in payments_today if p.method in transfer_methods]
    approved_proofs_today = (
        db.query(DeliveryPaymentProof)
        .options(joinedload(DeliveryPaymentProof.uploader), joinedload(DeliveryPaymentProof.reviewer))
        .filter(
            func.date(DeliveryPaymentProof.created_at) == today,
            DeliveryPaymentProof.status == "APPROVED",
        )
        .order_by(DeliveryPaymentProof.created_at.desc())
        .all()
    )
    transfer_provider_labels = {
        "TRANSFER": "Transferencia",
        "TRANSFER_NEQUI": "Nequi",
        "TRANSFER_BANCOLOMBIA": "Bancolombia",
        "TRANSFER_LLAVES": "Llaves",
    }
    provider_summary = {}
    for method, label in transfer_provider_labels.items():
        rows = [p for p in transfer_payments_today if p.method == method]
        proofs = [p for p in approved_proofs_today if p.payment_method == method]
        provider_summary[method] = {
            "label": label,
            "sales_count": len(rows),
            "sales_total": sum((Decimal(str(p.amount or 0)) for p in rows), Decimal("0")),
            "proof_count": len(proofs),
        }

    proof_rows_today = (
        db.query(DeliveryPaymentProof)
        .options(joinedload(DeliveryPaymentProof.order), joinedload(DeliveryPaymentProof.uploader), joinedload(DeliveryPaymentProof.reviewer))
        .filter(func.date(DeliveryPaymentProof.created_at) == today)
        .order_by(DeliveryPaymentProof.created_at.desc())
        .all()
    )
    transfer_evidence = []
    pending_transfer_closures = []
    for proof in proof_rows_today:
        if proof.order is None:
            continue
        registered = db.query(CashPayment).filter(CashPayment.order_id == proof.order_id).first()
        item = {
            "id": str(proof.id),
            "order_id": str(proof.order_id),
            "order_short_id": str(proof.order_id)[:8].upper(),
            "customer_name": proof.order.customer.full_name if proof.order.customer else "Cliente",
            "method": proof.payment_method,
            "method_label": transfer_provider_labels.get(proof.payment_method, proof.payment_method),
            "file_url": proof.file_url,
            "status": proof.status,
            "review_note": proof.review_note,
            "uploaded_by": proof.uploader.full_name if proof.uploader else None,
            "reviewed_by": proof.reviewer.full_name if proof.reviewer else None,
            "created_at": proof.created_at,
            "reviewed_at": proof.reviewed_at,
            "registered_in_cash": bool(registered),
            "cash_payment_id": str(registered.id) if registered else None,
        }
        transfer_evidence.append(item)
        if proof.status == "APPROVED" and not registered:
            pending_transfer_closures.append(item)

    # Ventas de transferencia cerradas sin comprobante aprobado: se muestran
    # como excepción para que el arqueo no quede en silencio.
    transfer_sales_without_proof = []
    for payment in transfer_payments_today:
        if not payment.order_id:
            continue
        approved = db.query(DeliveryPaymentProof).filter(
            DeliveryPaymentProof.order_id == payment.order_id,
            DeliveryPaymentProof.status == "APPROVED"
        ).first()
        if not approved:
            order = db.query(Order).filter(Order.id == payment.order_id).first()
            transfer_sales_without_proof.append({
                "order_id": str(payment.order_id),
                "order_short_id": str(payment.order_id)[:8].upper(),
                "method": payment.method,
                "method_label": transfer_provider_labels.get(payment.method, payment.method),
                "amount": payment.amount,
                "customer_name": order.customer.full_name if order and order.customer else "Cliente",
                "paid_at": payment.paid_at,
            })

    movement_rows_today = (
        db.query(CashRegisterMovement)
        .filter(func.date(CashRegisterMovement.created_at) == today)
        .order_by(CashRegisterMovement.created_at.desc())
        .all()
    )
    movements_today = [
        {
            "id": str(m.id),
            "register_id": str(m.cash_register_id),
            "type": m.movement_type,
            "amount": m.amount,
            "recipient_name": m.recipient_name,
            "recipient_document": m.recipient_document,
            "reason": m.reason,
            "created_at": m.created_at,
            "cashier_name": m.cashier.full_name if m.cashier else "Sin usuario",
        }
        for m in movement_rows_today
    ]

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
        "pending_prepayments": pending_prepayments,
        "pending_prepayment_count": len(pending_prepayments),
        "movements_today": movements_today,
        "withdrawals_today": sum(
            (Decimal(str(m.amount or 0)) for m in movement_rows_today if m.movement_type == "WITHDRAWAL"),
            Decimal("0")
        ),
        "transfer_reconciliation": {
            "registered_count": len(transfer_payments_today),
            "registered_total": transfer_today,
            "approved_proof_count": len(approved_proofs_today),
            "pending_transfer_closures": pending_transfer_closures,
            "sales_without_approved_proof": transfer_sales_without_proof,
            "providers": provider_summary,
        },
        "transfer_evidence_today": transfer_evidence,
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
                table.zone,

            "prepayment_required": bool(table.prepayment_required),

            "comanda_print_priority": table.comanda_print_priority or 2

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


@router.post("/payments/prepayment/verify")
def verify_prepayment_code(
    data: PrepaymentCodeVerify,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Comprueba que el código impreso pertenece a la comanda pendiente de esa mesa."""
    if not current_user.role or current_user.role.name != "Caja":
        raise HTTPException(403, "Solo Caja puede validar comandas.")

    code = str(data.confirmation_code).strip()
    order = (
        db.query(Order)
        .filter(
            Order.session_id == data.session_id,
            Order.confirmation_code == code,
            Order.status == "PENDING_PAYMENT"
        )
        .order_by(Order.created_at.asc())
        .first()
    )
    if not order:
        raise HTTPException(404, "Código de comanda inválido o ya utilizado.")

    session = (
        db.query(RestaurantSession)
        .options(joinedload(RestaurantSession.table))
        .filter(RestaurantSession.id == data.session_id, RestaurantSession.status == "OPEN")
        .first()
    )
    if not session or not session.table or not session.table.prepayment_required:
        raise HTTPException(400, "La mesa no está configurada para pago anticipado.")

    total = calculate_session_total(db, session.id)
    paid = sum(
        (Decimal(str(p.amount or 0)) for p in db.query(CashPayment).filter(CashPayment.session_id == session.id).all()),
        Decimal("0")
    )
    balance = max(Decimal("0"), total - paid)

    return {
        "valid": True,
        "session_id": str(session.id),
        "order_id": str(order.id),
        "table_number": session.table.number,
        "table_name": session.table.name,
        "balance": balance,
        "message": "Comanda validada. Puedes registrar el pago para enviarla a cocina."
    }


# ==========================================================
# COBRO ANTICIPADO DE MESAS CONFIGURADAS
# ==========================================================

@router.post("/payments/prepayment")
def prepay_session(
    data: CashPaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Cobra una mesa de pago anticipado y luego libera sus items a cocina."""
    if not current_user.role or current_user.role.name != "Caja":
        raise HTTPException(403, "Solo Caja puede registrar el pago anticipado.")

    register = get_open_register(db, current_user.id)
    if not register:
        raise HTTPException(400, "Primero debes abrir la caja.")

    session = (
        db.query(RestaurantSession)
        .options(joinedload(RestaurantSession.table))
        .filter(RestaurantSession.id == data.session_id, RestaurantSession.status == "OPEN")
        .first()
    )
    if not session:
        raise HTTPException(404, "La mesa no tiene una cuenta abierta.")
    if not session.table.prepayment_required:
        raise HTTPException(400, "Esta mesa no está configurada para pago anticipado.")

    code = str(data.confirmation_code or "").strip()
    if not code:
        raise HTTPException(400, "Debes introducir el código impreso en la comanda.")

    pending_order = (
        db.query(Order)
        .filter(
            Order.session_id == session.id,
            Order.confirmation_code == code,
            Order.status == "PENDING_PAYMENT"
        )
        .order_by(Order.created_at.asc())
        .first()
    )
    if not pending_order:
        raise HTTPException(400, "El código de la comanda no es válido o ya fue utilizado.")

    total = calculate_session_total(db, session.id)
    previous_payments = db.query(CashPayment).filter(CashPayment.session_id == session.id).all()
    already_paid = sum((Decimal(str(p.amount or 0)) for p in previous_payments), Decimal("0"))
    balance = max(Decimal("0"), total - already_paid)
    if balance <= 0:
        raise HTTPException(400, "Esta mesa ya tiene el total pagado.")

    method = data.method.upper().strip()
    if method not in {"CASH", "CARD", "TRANSFER"}:
        raise HTTPException(400, "Método de pago inválido. Usa CASH, CARD o TRANSFER.")

    received = Decimal(str(data.received_amount))
    change = Decimal("0")
    if method == "CASH":
        if received < balance:
            raise HTTPException(400, "El efectivo recibido es menor al total.")
        change = received - balance
    else:
        received = balance

    payment = CashPayment(
        cash_register_id=register.id, session_id=session.id, cashier_id=current_user.id,
        method=method, amount=balance, received_amount=received, change_amount=change,
        reference=data.reference
    )
    db.add(payment)
    db.flush()

    items = (
        db.query(OrderItem)
        .options(joinedload(OrderItem.dish).joinedload(Dish.station), joinedload(OrderItem.product).joinedload(Product.station))
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.session_id == session.id, Order.status != "CANCELLED", OrderItem.status == "PENDING")
        .all()
    )

    for item in items:
        if db.query(KitchenQueue).filter(KitchenQueue.order_item_id == item.id).first():
            continue
        source = item.dish or item.product
        if not source or not source.station_id:
            continue
        batch = db.query(OrderBatch).filter(OrderBatch.order_id == item.order_id, OrderBatch.station_id == source.station_id).first()
        if batch is None:
            batch = OrderBatch(order_id=item.order_id, station_id=source.station_id, status="PENDING")
            db.add(batch)
            db.flush()
            db.add(KitchenTicket(batch_id=batch.id, station_id=source.station_id, status="WAITING"))
        else:
            batch.status = "PENDING"
            ticket = db.query(KitchenTicket).filter(KitchenTicket.batch_id == batch.id).first()
            if ticket:
                ticket.status = "WAITING"
            else:
                db.add(KitchenTicket(batch_id=batch.id, station_id=source.station_id, status="WAITING"))
        db.add(KitchenQueue(station_id=source.station_id, order_item_id=item.id, status="WAITING"))

    for order in db.query(Order).filter(Order.session_id == session.id, Order.status == "PENDING_PAYMENT").all():
        order.status = "OPEN"

    db.commit()
    db.refresh(payment)
    return {
        "message": "Pago anticipado registrado. La comanda fue enviada a cocina.",
        "payment_id": str(payment.id), "session_id": str(session.id), "table_id": session.table_id,
        "total": balance, "method": method, "received_amount": received, "change_amount": change, "status": "OPEN"
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


    # La cuenta sigue siendo cobrable si el mesero ya marcó la mesa como
    # limpia. Limpiar NO libera la mesa: Caja todavía debe registrar el pago.
    session = (
        db.query(RestaurantSession)
        .filter(
            RestaurantSession.id == data.session_id,
            RestaurantSession.status.in_(["OPEN", "CLEAN"])
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

    # Si ya estaba limpia, conservar CLEAN para que Caja pueda finalizar
    # la liberación solo después de registrar el pago. Si no, PAID mantiene
    # la mesa ocupada hasta que el mesero complete la limpieza.
    session.status = "CLEAN" if session.status == "CLEAN" else "PAID"


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

    # Caja puede liberar una mesa pagada sin esperar a que el mesero
    # la marque como limpia. Así un estado de entrega atascado no deja
    # la mesa ocupada indefinidamente.
    # Se aceptan sesiones activas OPEN, PAID o CLEAN, pero siempre se exige
    # un pago registrado antes de cerrar la sesión y dejar libre la mesa.
    session = (
        db.query(RestaurantSession)
        .filter(
            RestaurantSession.id == session_id,
            RestaurantSession.status.in_(["OPEN", "PAID", "CLEAN"])
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=409,
            detail="La sesión no está activa o ya fue liberada."
        )

    has_payment = db.query(CashPayment.id).filter(
        CashPayment.session_id == session.id
    ).first() is not None
    if not has_payment:
        raise HTTPException(
            status_code=409,
            detail="Antes de liberar la mesa, Caja debe registrar y confirmar el pago."
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
# RETIRO DE DINERO
# ==========================================================

@router.post("/register/withdrawal")
def register_withdrawal(
    data: CashRegisterWithdrawalCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    register = get_open_register(db, current_user.id)
    if not register:
        raise HTTPException(status_code=400, detail="No hay una caja abierta.")

    amount = Decimal(str(data.amount))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="El valor del retiro debe ser mayor que cero.")

    cash_sales = sum(
        (Decimal(str(payment.amount or 0)) for payment in db.query(CashPayment).filter(
            CashPayment.cash_register_id == register.id,
            CashPayment.method == "CASH"
        ).all()),
        Decimal("0")
    )
    withdrawals = sum(
        (Decimal(str(m.amount or 0)) for m in db.query(CashRegisterMovement).filter(
            CashRegisterMovement.cash_register_id == register.id,
            CashRegisterMovement.movement_type == "WITHDRAWAL"
        ).all()),
        Decimal("0")
    )
    available = Decimal(str(register.opening_amount or 0)) + cash_sales - withdrawals
    if amount > available:
        raise HTTPException(
            status_code=400,
            detail=f"El retiro supera el efectivo disponible en caja. Disponible: {available:.2f}."
        )

    movement = CashRegisterMovement(
        cash_register_id=register.id,
        cashier_id=current_user.id,
        movement_type="WITHDRAWAL",
        amount=amount,
        recipient_name=data.recipient_name.strip(),
        recipient_document=data.recipient_document.strip(),
        reason=data.reason.strip() if data.reason else "Retiro de efectivo"
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)

    return {
        "message": "Retiro registrado correctamente.",
        "movement_id": str(movement.id),
        "amount": movement.amount,
        "cash_available": available - amount,
        "created_at": movement.created_at,
    }


# ==========================================================
# CORREGIR EFECTIVO CONTADO - SOLO ADMIN / UNA VEZ / MISMO DÍA
# ==========================================================

@router.patch("/admin/register/{register_id}/closing-amount")
def edit_closed_register_closing_amount(
    register_id: UUID,
    data: CashRegisterClosingEdit,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user.role or current_user.role.name != "Administrador":
        raise HTTPException(403, "Solo el administrador puede corregir un arqueo cerrado.")

    register = (
        db.query(CashRegister)
        .filter(CashRegister.id == register_id)
        .first()
    )
    if not register:
        raise HTTPException(404, "Caja no encontrada.")

    if register.status != "CLOSED":
        raise HTTPException(409, "Solo se puede corregir una caja que ya esté cerrada.")

    if not register.closed_at:
        raise HTTPException(409, "La caja no tiene fecha de cierre registrada.")

    closed_local_date = register.closed_at.astimezone(
        timezone(timedelta(hours=-5), name="America/Bogota")
    ).date()
    if closed_local_date != _bogota_today():
        raise HTTPException(409, "La corrección solo está disponible durante el mismo día del cierre.")

    if (register.closing_amount_edit_count or 0) >= 1:
        raise HTTPException(409, "Esta caja ya tuvo su única corrección administrativa. No se puede volver a editar.")

    if register.expected_cash is None:
        raise HTTPException(409, "La caja no tiene efectivo esperado calculado.")

    new_amount = Decimal(str(data.closing_amount))
    new_difference = new_amount - Decimal(str(register.expected_cash))

    register.closing_amount = new_amount
    register.difference = new_difference
    register.closing_amount_edit_count = 1
    register.closing_amount_edited_at = datetime.now(timezone.utc)
    register.closing_amount_edited_by = current_user.id
    register.closing_amount_edit_reason = data.reason.strip()

    db.commit()
    db.refresh(register)

    return {
        "message": "El efectivo contado fue corregido una sola vez y el arqueo quedó actualizado.",
        "register_id": str(register.id),
        "closing_amount": register.closing_amount,
        "expected_cash": register.expected_cash,
        "difference": register.difference,
        "edited_at": register.closing_amount_edited_at,
        "edited_by": current_user.full_name,
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


    withdrawal_total = sum(
        (Decimal(str(m.amount or 0)) for m in db.query(CashRegisterMovement).filter(
            CashRegisterMovement.cash_register_id == register.id,
            CashRegisterMovement.movement_type == "WITHDRAWAL"
        ).all()),
        Decimal("0")
    )

    expected_cash = (
        Decimal(str(register.opening_amount or 0))
        + cash_sales
        - withdrawal_total
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

        "withdrawals":
            withdrawal_total,

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