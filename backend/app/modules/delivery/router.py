from datetime import datetime, timezone
from uuid import UUID, uuid4
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.orders.model import Order
from app.modules.order_items.model import OrderItem
from app.modules.dishes.model import Dish
from .model import CourierLocation, DeliveryMessage
from .schemas import LocationUpdate, DeliveryMessageCreate, CancelDelivery, DeliveryConfirm, PaymentClose

router=APIRouter(prefix='/api/delivery',tags=['Delivery'])
ROLE='Domiciliario'

def role_ok(u, roles):
    return u.role and u.role.name in roles

def order_payload(db,o):
    items=db.query(OrderItem).options(joinedload(OrderItem.dish),joinedload(OrderItem.product)).filter(OrderItem.order_id==o.id).all()
    total=sum(float(i.total or 0) for i in items)
    kitchen_rows=[]
    # kitchen time is derived from all queues belonging to this order
    from app.modules.kitchen_queue.model import KitchenQueue
    qs=db.query(KitchenQueue).join(OrderItem,KitchenQueue.order_item_id==OrderItem.id).filter(OrderItem.order_id==o.id).all()
    for q in qs:
        kitchen_rows.append({'created_at':q.created_at,'started_at':q.started_at,'finished_at':q.finished_at})
    finished=[q['finished_at'] for q in kitchen_rows if q['finished_at']]
    started=[q['started_at'] for q in kitchen_rows if q['started_at']]
    kitchen_started=min(started) if started else None
    kitchen_ready=max(finished) if finished else None
    prep_seconds=int((kitchen_ready-kitchen_started).total_seconds()) if kitchen_ready and kitchen_started else None
    now=datetime.now(timezone.utc)
    delivery_seconds=int((now-o.dispatched_at).total_seconds()) if o.dispatched_at and o.status=='OUT_FOR_DELIVERY' else (int((o.courier_delivered_at-o.dispatched_at).total_seconds()) if o.dispatched_at and o.courier_delivered_at else None)
    return {'id':str(o.id),'short_id':str(o.id)[:8].upper(),'status':o.status,'customer':{'id':str(o.customer_id) if o.customer_id else None,'name':o.customer.full_name if o.customer else 'Cliente','phone':o.delivery_phone},'address':o.delivery_address,'delivery_fee':float(o.delivery_fee or 0),'total':total+float(o.delivery_fee or 0),'items':[{'name':i.dish.name if i.dish else i.product.name if i.product else 'Producto','quantity':i.quantity,'total':float(i.total or 0)} for i in items],'created_at':o.created_at,'cashier_confirmed_at':o.cashier_confirmed_at,'kitchen_started_at':kitchen_started,'ready_at':kitchen_ready,'prep_seconds':prep_seconds,'dispatched_at':o.dispatched_at,'courier_started_at':o.courier_started_at,'courier_delivered_at':o.courier_delivered_at,'delivery_seconds':delivery_seconds,'courier_id':str(o.courier_id) if o.courier_id else None,'payment_method':o.payment_method}

@router.get('/available-orders')
def available_orders(db:Session=Depends(get_db),u=Depends(get_current_user)):
    if not role_ok(u,{ROLE}): raise HTTPException(403,'Solo Domiciliarios pueden consultar entregas.')
    rows=db.query(Order).options(joinedload(Order.customer)).filter(Order.order_type=='DOMICILIO',Order.status=='READY',Order.courier_id.is_(None)).order_by(Order.created_at.asc()).limit(50).all()
    return [order_payload(db,o) for o in rows]

@router.get('/my-orders')
def my_orders(db:Session=Depends(get_db),u=Depends(get_current_user)):
    if not role_ok(u,{ROLE}): raise HTTPException(403,'Solo Domiciliarios pueden consultar entregas.')
    rows=db.query(Order).options(joinedload(Order.customer)).filter(Order.order_type=='DOMICILIO',Order.courier_id==u.id,Order.status.in_(['OUT_FOR_DELIVERY','DELIVERED_PENDING_PAYMENT','CANCELLED'])).order_by(desc(Order.created_at)).limit(30).all()
    return [order_payload(db,o) for o in rows]

@router.patch('/orders/{order_id}/claim')
def claim(order_id:UUID,db:Session=Depends(get_db),u=Depends(get_current_user)):
    if not role_ok(u,{ROLE}): raise HTTPException(403,'Solo Domiciliarios.')
    o=db.query(Order).filter(Order.id==order_id,Order.order_type=='DOMICILIO').with_for_update().first()
    if not o: raise HTTPException(404,'Pedido no encontrado.')
    if o.status!='READY' or o.courier_id: raise HTTPException(409,'Este pedido ya fue asignado o no está listo.')
    now=datetime.now(timezone.utc); o.courier_id=u.id; o.courier_assigned_at=now; o.status='OUT_FOR_DELIVERY'; o.courier_started_at=now; o.dispatched_at=now
    db.commit(); return order_payload(db,o)

@router.post('/location')
def update_location(data:LocationUpdate,db:Session=Depends(get_db),u=Depends(get_current_user)):
    if not role_ok(u,{ROLE}): raise HTTPException(403,'Solo Domiciliarios.')
    row=CourierLocation(id=uuid4(),courier_id=u.id,latitude=data.latitude,longitude=data.longitude,accuracy=data.accuracy)
    db.add(row); db.commit(); return {'ok':True,'recorded_at':row.recorded_at}

@router.get('/locations')
def locations(db:Session=Depends(get_db),u=Depends(get_current_user)):
    if not role_ok(u,{'Administrador','Caja'}): raise HTTPException(403,'Solo Administrador o Caja.')
    users={}
    from app.modules.users.model import User
    couriers=db.query(User).join(User.role).filter(User.role.has(name=ROLE),User.is_active==True).all()
    for c in couriers:
        loc=db.query(CourierLocation).filter(CourierLocation.courier_id==c.id).order_by(desc(CourierLocation.recorded_at)).first()
        active=db.query(Order).filter(Order.courier_id==c.id,Order.status=='OUT_FOR_DELIVERY').order_by(desc(Order.created_at)).first()
        users[str(c.id)]={'courier_id':str(c.id),'name':c.full_name,'latitude':loc.latitude if loc else None,'longitude':loc.longitude if loc else None,'accuracy':loc.accuracy if loc else None,'recorded_at':loc.recorded_at if loc else None,'order_id':str(active.id) if active else None}
    return list(users.values())

@router.post('/orders/{order_id}/delivered')
def delivered(order_id:UUID,data:DeliveryConfirm,db:Session=Depends(get_db),u=Depends(get_current_user)):
    if not role_ok(u,{ROLE}): raise HTTPException(403,'Solo Domiciliarios.')
    o=db.query(Order).filter(Order.id==order_id,Order.courier_id==u.id,Order.status=='OUT_FOR_DELIVERY').first()
    if not o: raise HTTPException(404,'Entrega no encontrada o ya finalizada.')
    if not o.delivery_code or secrets.compare_digest(o.delivery_code.strip(),data.code.strip()) is False: raise HTTPException(400,'Código de entrega incorrecto.')
    o.courier_delivered_at=datetime.now(timezone.utc); o.status='DELIVERED_PENDING_PAYMENT'; db.commit(); return {'message':'Entrega validada. Caja debe registrar el pago y cerrar el pedido.','status':o.status}

@router.patch('/orders/{order_id}/cancel')
def cancel(order_id:UUID,data:CancelDelivery,db:Session=Depends(get_db),u=Depends(get_current_user)):
    if not role_ok(u,{ROLE}): raise HTTPException(403,'Solo Domiciliarios.')
    o=db.query(Order).filter(Order.id==order_id,Order.courier_id==u.id,Order.status=='OUT_FOR_DELIVERY').first()
    if not o: raise HTTPException(404,'Entrega no encontrada.')
    o.status='CANCELLED'; o.cancelled_at=datetime.now(timezone.utc); o.cancellation_reason=data.reason.strip(); db.commit(); return {'status':o.status}

@router.get('/messages')
def messages(order_id:UUID|None=None,db:Session=Depends(get_db),u=Depends(get_current_user)):
    if not role_ok(u,{'Administrador','Caja',ROLE}): raise HTTPException(403,'No autorizado.')
    q=db.query(DeliveryMessage).options(joinedload(DeliveryMessage.sender)).filter(DeliveryMessage.order_id==order_id if order_id else True).order_by(DeliveryMessage.created_at.asc()).limit(200)
    return [{'id':str(m.id),'order_id':str(m.order_id) if m.order_id else None,'sender_id':str(m.sender_id),'sender':m.sender.full_name if m.sender else 'Usuario','message':m.message,'created_at':m.created_at} for m in q.all()]

@router.post('/messages')
def send_message(data:DeliveryMessageCreate,db:Session=Depends(get_db),u=Depends(get_current_user)):
    if not role_ok(u,{'Administrador','Caja',ROLE}): raise HTTPException(403,'No autorizado.')
    m=DeliveryMessage(id=uuid4(),order_id=data.order_id,sender_id=u.id,recipient_id=data.recipient_id,message=data.message.strip())
    db.add(m); db.commit(); return {'id':str(m.id),'message':'Mensaje enviado.'}
