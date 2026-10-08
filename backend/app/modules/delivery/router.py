from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import UUID, uuid4
import secrets

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.orders.model import Order
from app.modules.order_items.model import OrderItem
from .model import CourierLocation, CourierPresence, DeliveryMessage, DeliveryPaymentProof
from .schemas import (
    LocationUpdate,
    DeliveryMessageCreate,
    CancelDelivery,
    DeliveryConfirm,
    PaymentMethodUpdate,
    PaymentProofReview,
)

router = APIRouter(prefix='/api/delivery', tags=['Delivery'])
ROLE = 'Domiciliario'
ONLINE_WINDOW_SECONDS = 45
TRANSFER_METHODS = {'TRANSFER', 'TRANSFER_NEQUI', 'TRANSFER_BANCOLOMBIA', 'TRANSFER_LLAVES'}
PAYMENT_METHODS = {'CASH', 'CARD', *TRANSFER_METHODS}


def role_ok(u, roles):
    return u.role and u.role.name in roles


def normalize_payment_method(method: str | None) -> str:
    value = (method or 'CASH').strip().upper().replace(' ', '_')
    aliases = {
        'NEQUI': 'TRANSFER_NEQUI',
        'BANCOLOMBIA': 'TRANSFER_BANCOLOMBIA',
        'BANC0LOMBIA': 'TRANSFER_BANCOLOMBIA',
        'LLAVE': 'TRANSFER_LLAVES',
        'LLAVES': 'TRANSFER_LLAVES',
    }
    value = aliases.get(value, value)
    if value not in PAYMENT_METHODS:
        raise HTTPException(400, 'Método de pago inválido.')
    return value


def _touch_presence(db: Session, courier_id, online=True):
    row = db.query(CourierPresence).filter(CourierPresence.courier_id == courier_id).first()
    now = datetime.now(timezone.utc)
    if not row:
        row = CourierPresence(courier_id=courier_id, last_seen=now, online=online)
        db.add(row)
    else:
        row.last_seen = now
        row.online = online
    return row


def _proof_payload(p: DeliveryPaymentProof, uploader_name=None, reviewer_name=None):
    return {
        'id': str(p.id),
        'order_id': str(p.order_id),
        'payment_method': p.payment_method,
        'file_url': p.file_url,
        'status': p.status,
        'review_note': p.review_note,
        'uploaded_by': uploader_name or (p.uploader.full_name if p.uploader else None),
        'reviewed_by': reviewer_name or (p.reviewer.full_name if p.reviewer else None),
        'created_at': p.created_at,
        'reviewed_at': p.reviewed_at,
    }


def _proofs_for_order(db: Session, order_id):
    return (
        db.query(DeliveryPaymentProof)
        .options(joinedload(DeliveryPaymentProof.uploader), joinedload(DeliveryPaymentProof.reviewer))
        .filter(DeliveryPaymentProof.order_id == order_id)
        .order_by(DeliveryPaymentProof.created_at.desc())
        .all()
    )


def order_payload(db, o):
    items = db.query(OrderItem).options(joinedload(OrderItem.dish), joinedload(OrderItem.product)).filter(OrderItem.order_id == o.id).all()
    total = sum(float(i.total or 0) for i in items)
    kitchen_rows = []
    from app.modules.kitchen_queue.model import KitchenQueue
    qs = db.query(KitchenQueue).join(OrderItem, KitchenQueue.order_item_id == OrderItem.id).filter(OrderItem.order_id == o.id).all()
    for q in qs:
        kitchen_rows.append({'created_at': q.created_at, 'started_at': q.started_at, 'finished_at': q.finished_at})
    finished = [q['finished_at'] for q in kitchen_rows if q['finished_at']]
    started = [q['started_at'] for q in kitchen_rows if q['started_at']]
    kitchen_started = min(started) if started else None
    kitchen_ready = max(finished) if finished else None
    prep_seconds = int((kitchen_ready - kitchen_started).total_seconds()) if kitchen_ready and kitchen_started else None
    now = datetime.now(timezone.utc)
    delivery_seconds = int((now - o.dispatched_at).total_seconds()) if o.dispatched_at and o.status == 'OUT_FOR_DELIVERY' else (int((o.courier_delivered_at - o.dispatched_at).total_seconds()) if o.dispatched_at and o.courier_delivered_at else None)
    proofs = _proofs_for_order(db, o.id)
    return {
        'id': str(o.id),
        'short_id': str(o.id)[:8].upper(),
        'status': o.status,
        'customer': {'id': str(o.customer_id) if o.customer_id else None, 'name': o.customer.full_name if o.customer else 'Cliente', 'phone': o.delivery_phone},
        'address': o.delivery_address,
        'delivery_fee': float(o.delivery_fee or 0),
        'total': total + float(o.delivery_fee or 0),
        'items': [{'name': i.dish.name if i.dish else i.product.name if i.product else 'Producto', 'quantity': i.quantity, 'total': float(i.total or 0)} for i in items],
        'created_at': o.created_at,
        'cashier_confirmed_at': o.cashier_confirmed_at,
        'kitchen_started_at': kitchen_started,
        'ready_at': kitchen_ready,
        'prep_seconds': prep_seconds,
        'dispatched_at': o.dispatched_at,
        'courier_started_at': o.courier_started_at,
        'courier_delivered_at': o.courier_delivered_at,
        'delivery_seconds': delivery_seconds,
        'courier_id': str(o.courier_id) if o.courier_id else None,
        'payment_method': o.payment_method,
        'payment_confirmed_at': o.payment_confirmed_at,
        'payment_proofs': [_proof_payload(p) for p in proofs],
    }


@router.get('/available-orders')
def available_orders(db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {ROLE}):
        raise HTTPException(403, 'Solo Domiciliarios pueden consultar entregas.')
    _touch_presence(db, u.id)
    rows = db.query(Order).options(joinedload(Order.customer)).filter(Order.order_type == 'DOMICILIO', Order.status == 'READY', Order.courier_id.is_(None)).order_by(Order.created_at.asc()).limit(50).all()
    db.commit()
    return [order_payload(db, o) for o in rows]


@router.get('/my-orders')
def my_orders(db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {ROLE}):
        raise HTTPException(403, 'Solo Domiciliarios pueden consultar entregas.')
    _touch_presence(db, u.id)
    rows = db.query(Order).options(joinedload(Order.customer)).filter(Order.order_type == 'DOMICILIO', Order.courier_id == u.id, Order.status.in_(['OUT_FOR_DELIVERY', 'DELIVERED_PENDING_PAYMENT', 'CLOSED', 'CANCELLED'])).order_by(desc(Order.created_at)).limit(30).all()
    db.commit()
    return [order_payload(db, o) for o in rows]


@router.patch('/orders/{order_id}/claim')
def claim(order_id: UUID, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {ROLE}):
        raise HTTPException(403, 'Solo Domiciliarios.')
    o = db.query(Order).filter(Order.id == order_id, Order.order_type == 'DOMICILIO').with_for_update().first()
    if not o:
        raise HTTPException(404, 'Pedido no encontrado.')
    if o.status != 'READY' or o.courier_id:
        raise HTTPException(409, 'Este pedido ya fue asignado o no está listo.')
    now = datetime.now(timezone.utc)
    o.courier_id = u.id
    o.courier_assigned_at = now
    o.status = 'OUT_FOR_DELIVERY'
    o.courier_started_at = now
    o.dispatched_at = now
    _touch_presence(db, u.id)
    db.commit()
    return order_payload(db, o)


@router.post('/location')
def update_location(data: LocationUpdate, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {ROLE}):
        raise HTTPException(403, 'Solo Domiciliarios.')
    row = CourierLocation(id=uuid4(), courier_id=u.id, latitude=data.latitude, longitude=data.longitude, accuracy=data.accuracy)
    db.add(row)
    _touch_presence(db, u.id)
    db.commit()
    return {'ok': True, 'recorded_at': row.recorded_at}


@router.post('/presence')
def presence(db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {ROLE}):
        raise HTTPException(403, 'Solo Domiciliarios.')
    row = _touch_presence(db, u.id)
    db.commit()
    return {'ok': True, 'online': row.online, 'last_seen': row.last_seen}


@router.post('/presence/offline')
def presence_offline(db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {ROLE}):
        raise HTTPException(403, 'Solo Domiciliarios.')
    row = _touch_presence(db, u.id, online=False)
    db.commit()
    return {'ok': True}


@router.get('/locations')
def locations(db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {'Administrador', 'Caja'}):
        raise HTTPException(403, 'Solo Administrador o Caja.')
    from app.modules.users.model import User
    now = datetime.now(timezone.utc)
    couriers = db.query(User).join(User.role).filter(User.role.has(name=ROLE), User.is_active == True).order_by(User.full_name.asc()).all()
    result = []
    for c in couriers:
        loc = db.query(CourierLocation).filter(CourierLocation.courier_id == c.id).order_by(desc(CourierLocation.recorded_at)).first()
        presence_row = db.query(CourierPresence).filter(CourierPresence.courier_id == c.id).first()
        last_seen = presence_row.last_seen if presence_row else (loc.recorded_at if loc else None)
        online = bool(presence_row and presence_row.online and last_seen and (now - last_seen).total_seconds() <= ONLINE_WINDOW_SECONDS)
        active = db.query(Order).filter(Order.courier_id == c.id, Order.status.in_(['OUT_FOR_DELIVERY', 'DELIVERED_PENDING_PAYMENT'])).order_by(desc(Order.created_at)).first()
        result.append({
            'courier_id': str(c.id),
            'name': c.full_name,
            'email': c.email,
            'online': online,
            'last_seen': last_seen,
            'latitude': loc.latitude if loc else None,
            'longitude': loc.longitude if loc else None,
            'accuracy': loc.accuracy if loc else None,
            'recorded_at': loc.recorded_at if loc else None,
            'order_id': str(active.id) if active else None,
            'order_short_id': str(active.id)[:8].upper() if active else None,
            'destination': active.delivery_address if active else None,
            'order_status': active.status if active else None,
        })
    return result


@router.post('/orders/{order_id}/delivered')
def delivered(order_id: UUID, data: DeliveryConfirm, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {ROLE}):
        raise HTTPException(403, 'Solo Domiciliarios.')
    o = db.query(Order).filter(Order.id == order_id, Order.courier_id == u.id, Order.status == 'OUT_FOR_DELIVERY').first()
    if not o:
        raise HTTPException(404, 'Entrega no encontrada o ya finalizada.')
    if not o.delivery_code or secrets.compare_digest(o.delivery_code.strip(), data.code.strip()) is False:
        raise HTTPException(400, 'Código de entrega incorrecto.')
    o.courier_delivered_at = datetime.now(timezone.utc)
    o.status = 'DELIVERED_PENDING_PAYMENT'
    _touch_presence(db, u.id)
    db.commit()
    return {'message': 'Entrega validada. Reporta el método de pago; Caja debe aprobar y cerrar la venta.', 'status': o.status}


@router.patch('/orders/{order_id}/payment-method')
def payment_method(order_id: UUID, data: PaymentMethodUpdate, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {ROLE, 'Caja', 'Administrador'}):
        raise HTTPException(403, 'No autorizado.')
    q = db.query(Order).filter(Order.id == order_id, Order.status == 'DELIVERED_PENDING_PAYMENT')
    if role_ok(u, {ROLE}):
        q = q.filter(Order.courier_id == u.id)
    o = q.first()
    if not o:
        raise HTTPException(404, 'Venta pendiente no encontrada.')
    method = normalize_payment_method(data.payment_method)
    o.payment_method = method
    if role_ok(u, {ROLE}):
        _touch_presence(db, u.id)
    db.commit()
    return {'ok': True, 'payment_method': method}


@router.post('/orders/{order_id}/payment-proof')
async def upload_payment_proof(
    order_id: UUID,
    payment_method: str = Form('TRANSFER'),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    u=Depends(get_current_user),
):
    if not role_ok(u, {ROLE}):
        raise HTTPException(403, 'Solo Domiciliarios pueden subir comprobantes.')
    o = db.query(Order).filter(Order.id == order_id, Order.courier_id == u.id, Order.status == 'DELIVERED_PENDING_PAYMENT').first()
    if not o:
        raise HTTPException(404, 'Venta pendiente no encontrada.')
    method = normalize_payment_method(payment_method)
    if method not in TRANSFER_METHODS:
        raise HTTPException(400, 'El comprobante fotográfico solo aplica a pagos por transferencia.')
    allowed = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}
    if file.content_type not in allowed:
        raise HTTPException(400, 'El comprobante debe ser una imagen JPG, PNG o WEBP.')
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, 'La foto no puede superar 5 MB.')
    folder = Path('app/static/uploads/delivery_proofs')
    folder.mkdir(parents=True, exist_ok=True)
    filename = f'{uuid4().hex}{allowed[file.content_type]}'
    (folder / filename).write_bytes(content)

    proof = DeliveryPaymentProof(
        id=uuid4(),
        order_id=o.id,
        uploaded_by=u.id,
        payment_method=method,
        file_url=f'/static/uploads/delivery_proofs/{filename}',
        status='PENDING',
    )
    db.add(proof)
    o.payment_method = method
    _touch_presence(db, u.id)
    db.commit()
    db.refresh(proof)
    return {'ok': True, 'proof': _proof_payload(proof, u.full_name)}


@router.get('/orders/{order_id}/payment-proofs')
def payment_proofs(order_id: UUID, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {'Administrador', 'Caja', ROLE}):
        raise HTTPException(403, 'No autorizado.')
    o = db.query(Order).filter(Order.id == order_id, Order.order_type == 'DOMICILIO').first()
    if not o:
        raise HTTPException(404, 'Pedido no encontrado.')
    if role_ok(u, {ROLE}) and o.courier_id != u.id:
        raise HTTPException(403, 'No puedes consultar este comprobante.')
    return [_proof_payload(p) for p in _proofs_for_order(db, order_id)]


@router.patch('/payment-proofs/{proof_id}/review')
def review_payment_proof(proof_id: UUID, data: PaymentProofReview, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {'Administrador', 'Caja'}):
        raise HTTPException(403, 'Solo Caja o Administrador pueden revisar comprobantes.')
    proof = db.query(DeliveryPaymentProof).filter(DeliveryPaymentProof.id == proof_id).first()
    if not proof:
        raise HTTPException(404, 'Comprobante no encontrado.')
    proof.status = data.status
    proof.review_note = (data.note or '').strip() or None
    proof.reviewed_by = u.id
    proof.reviewed_at = datetime.now(timezone.utc)
    if data.status == 'APPROVED':
        order = db.query(Order).filter(Order.id == proof.order_id).first()
        if order:
            order.payment_method = proof.payment_method
    db.commit()
    return {'ok': True, 'status': proof.status}


@router.patch('/orders/{order_id}/cancel')
def cancel(order_id: UUID, data: CancelDelivery, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if role_ok(u, {ROLE}):
        o = db.query(Order).filter(Order.id == order_id, Order.courier_id == u.id, Order.status == 'OUT_FOR_DELIVERY').first()
    elif role_ok(u, {'Administrador'}):
        o = db.query(Order).filter(Order.id == order_id, Order.order_type == 'DOMICILIO').first()
    else:
        raise HTTPException(403, 'No autorizado.')
    if not o:
        raise HTTPException(404, 'Entrega no encontrada.')
    if o.status in {'CLOSED', 'CANCELLED', 'DELIVERED_PENDING_PAYMENT'}:
        raise HTTPException(409, 'Este pedido ya no se puede cancelar.')
    o.status = 'CANCELLED'
    o.cancelled_at = datetime.now(timezone.utc)
    o.cancellation_reason = data.reason.strip()
    db.commit()
    return {'status': o.status}


@router.get('/messages')
def messages(order_id: UUID | None = None, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {'Administrador', 'Caja', ROLE}):
        raise HTTPException(403, 'No autorizado.')
    q = db.query(DeliveryMessage).options(joinedload(DeliveryMessage.sender)).order_by(DeliveryMessage.created_at.asc())
    if order_id:
        q = q.filter(DeliveryMessage.order_id == order_id)
    elif role_ok(u, {ROLE}):
        courier_order_ids = [row[0] for row in db.query(Order.id).filter(Order.courier_id == u.id).all()]
        q = q.filter(or_(DeliveryMessage.sender_id == u.id, DeliveryMessage.recipient_id == u.id, DeliveryMessage.order_id.in_(courier_order_ids) if courier_order_ids else False))
    elif role_ok(u, {'Caja'}):
        q = q.filter(or_(DeliveryMessage.sender_id == u.id, DeliveryMessage.recipient_id == u.id, DeliveryMessage.order_id.isnot(None)))
    rows = q.limit(300).all()
    return [
        {
            'id': str(m.id),
            'order_id': str(m.order_id) if m.order_id else None,
            'sender_id': str(m.sender_id),
            'recipient_id': str(m.recipient_id) if m.recipient_id else None,
            'sender': m.sender.full_name if m.sender else 'Usuario',
            'message': m.message,
            'created_at': m.created_at,
        }
        for m in rows
    ]


@router.post('/messages')
def send_message(data: DeliveryMessageCreate, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {'Administrador', 'Caja', ROLE}):
        raise HTTPException(403, 'No autorizado.')
    recipient_id = data.recipient_id
    if data.order_id:
        order = db.query(Order).filter(Order.id == data.order_id, Order.order_type == 'DOMICILIO').first()
        if not order:
            raise HTTPException(404, 'Pedido de domicilio no encontrado.')
        if role_ok(u, {ROLE}) and order.courier_id != u.id:
            raise HTTPException(403, 'Este pedido no está asignado a ti.')
        if role_ok(u, {'Caja'}) and not recipient_id and order.courier_id:
            recipient_id = order.courier_id
        if role_ok(u, {'Administrador'}) and not recipient_id and order.courier_id:
            recipient_id = order.courier_id
    elif role_ok(u, {ROLE}) and not recipient_id:
        from app.modules.users.model import User
        recipient = db.query(User).join(User.role).filter(User.role.has(name='Caja'), User.is_active == True).order_by(User.id.asc()).first()
        recipient_id = recipient.id if recipient else None

    m = DeliveryMessage(id=uuid4(), order_id=data.order_id, sender_id=u.id, recipient_id=recipient_id, message=data.message.strip())
    db.add(m)
    if role_ok(u, {ROLE}):
        _touch_presence(db, u.id)
    db.commit()
    return {'id': str(m.id), 'message': 'Mensaje enviado.', 'recipient_id': str(recipient_id) if recipient_id else None}


# ==========================================================
# ADMINISTRACIÓN DE PEDIDOS Y DOMICILIARIOS
# ==========================================================


def _admin_order_payload(db: Session, order: Order):
    base = order_payload(db, order)
    loc = None
    if order.courier_id:
        row = db.query(CourierLocation).filter(CourierLocation.courier_id == order.courier_id).order_by(desc(CourierLocation.recorded_at)).first()
        if row:
            loc = {'latitude': row.latitude, 'longitude': row.longitude, 'accuracy': row.accuracy, 'recorded_at': row.recorded_at}
    presence_row = db.query(CourierPresence).filter(CourierPresence.courier_id == order.courier_id).first() if order.courier_id else None
    base.update({
        'courier_name': order.courier.full_name if order.courier else None,
        'courier_email': order.courier.email if order.courier else None,
        'courier_assigned_at': order.courier_assigned_at,
        'closed_at': order.closed_at,
        'served_at': order.served_at,
        'location': loc,
        'courier_online': bool(presence_row and presence_row.online and presence_row.last_seen and (datetime.now(timezone.utc) - presence_row.last_seen).total_seconds() <= ONLINE_WINDOW_SECONDS),
        'notes': order.notes,
    })
    return base


@router.get('/admin/orders')
def admin_orders(db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {'Administrador'}):
        raise HTTPException(403, 'Solo Administración puede consultar los pedidos.')
    rows = db.query(Order).options(joinedload(Order.customer), joinedload(Order.courier)).filter(Order.order_type.in_(['ONLINE', 'DOMICILIO'])).order_by(desc(Order.created_at)).limit(100).all()
    return [_admin_order_payload(db, o) for o in rows]


@router.get('/admin/orders/{order_id}')
def admin_order_detail(order_id: UUID, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {'Administrador'}):
        raise HTTPException(403, 'Solo Administración puede consultar el pedido.')
    order = db.query(Order).options(joinedload(Order.customer), joinedload(Order.courier)).filter(Order.id == order_id, Order.order_type.in_(['ONLINE', 'DOMICILIO'])).first()
    if not order:
        raise HTTPException(404, 'Pedido no encontrado.')
    return _admin_order_payload(db, order)


@router.get('/admin/orders/{order_id}/location')
def admin_order_location(order_id: UUID, db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {'Administrador'}):
        raise HTTPException(403, 'Solo Administración puede consultar la ubicación.')
    order = db.query(Order).filter(Order.id == order_id, Order.order_type == 'DOMICILIO').first()
    if not order:
        raise HTTPException(404, 'Pedido no encontrado.')
    if not order.courier_id:
        return {'available': False}
    row = db.query(CourierLocation).filter(CourierLocation.courier_id == order.courier_id).order_by(desc(CourierLocation.recorded_at)).first()
    if not row:
        return {'available': False}
    return {'available': True, 'latitude': row.latitude, 'longitude': row.longitude, 'accuracy': row.accuracy, 'recorded_at': row.recorded_at}


@router.get('/admin/couriers')
def admin_couriers(db: Session = Depends(get_db), u=Depends(get_current_user)):
    if not role_ok(u, {'Administrador'}):
        raise HTTPException(403, 'Solo Administración puede consultar los domiciliarios.')
    return locations(db, u)
