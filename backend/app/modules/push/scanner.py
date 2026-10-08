from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.core.config import settings
from app.modules.kitchen_queue.model import KitchenQueue
from app.modules.order_items.model import OrderItem
from app.modules.push.model import PushSubscription
from app.modules.waiter_calls.model import WaiterCall
from app.modules.users.model import User
from .service import send_push

_last_new_scan = None
_seen_waiter_calls = set()
_seen_ready_items = set()

def _waiter_subs(db):
    return db.query(PushSubscription).join(User, PushSubscription.user_id == User.id).filter(User.role.has(name='Mesero')).all()

def scan():
    global _last_new_scan
    if not settings.WEB_PUSH_VAPID_PRIVATE_KEY or not settings.WEB_PUSH_VAPID_EMAIL:
        return
    db=SessionLocal()
    try:
        now=datetime.now(timezone.utc)
        cutoff=_last_new_scan or (now-timedelta(seconds=30))

        # Nueva comanda -> estación correspondiente.
        rows=db.query(KitchenQueue).filter(KitchenQueue.status=='WAITING',KitchenQueue.created_at>cutoff).all()
        for q in rows:
            subs=db.query(PushSubscription).filter(PushSubscription.station_id==q.station_id).all()
            item=db.query(OrderItem).filter(OrderItem.id==q.order_item_id).first()
            source=(item.dish or item.product) if item else None
            name=source.name if source else 'Nueva comanda'
            for sub in subs:
                send_push(sub,{"title":"🔥 Nueva comanda","body":f"{name} · nueva preparación en tu estación","url":"/kitchen","tag":f"queue-{q.id}"})

        # Preparación atrasada -> una alerta por comanda.
        overdue=db.query(KitchenQueue).filter(KitchenQueue.status=='PREPARING',KitchenQueue.started_at.isnot(None),KitchenQueue.overdue_notified_at.is_(None)).all()
        for q in overdue:
            item=db.query(OrderItem).filter(OrderItem.id==q.order_item_id).first(); source=(item.dish or item.product) if item else None; target=int(getattr(source,'preparation_time',0) or 0) if source else 0
            started=q.started_at.replace(tzinfo=timezone.utc) if q.started_at.tzinfo is None else q.started_at
            if target<=0 or now < started+timedelta(minutes=target): continue
            subs=db.query(PushSubscription).filter(PushSubscription.station_id==q.station_id).all(); name=source.name if source else 'Comanda'
            for sub in subs:
                send_push(sub,{"title":"⚠️ Preparación atrasada","body":f"{name} ya superó su tiempo objetivo de {target} min.","url":"/kitchen","tag":f"late-{q.id}"})
            q.overdue_notified_at=datetime.utcnow()

        # Solicitud de atención -> todos los meseros con alertas activadas.
        calls=db.query(WaiterCall).filter(WaiterCall.status=='REQUESTED',WaiterCall.requested_at>cutoff).all()
        waiter_subs=_waiter_subs(db)
        for call in calls:
            key=str(call.id)
            if key in _seen_waiter_calls: continue
            table=call.table.number if call.table else '?'
            for sub in waiter_subs:
                send_push(sub,{"title":"🔔 Solicitud de atención","body":f"La mesa {table} está solicitando al mesero.","url":"/waiter","tag":f"call-{call.id}"})
            _seen_waiter_calls.add(key)

        # Producto listo -> todos los meseros con alertas activadas.
        ready=db.query(KitchenQueue).filter(KitchenQueue.status=='READY',KitchenQueue.finished_at>cutoff).all()
        for q in ready:
            key=str(q.id)
            if key in _seen_ready_items: continue
            item=db.query(OrderItem).filter(OrderItem.id==q.order_item_id).first(); source=(item.dish or item.product) if item else None
            name=source.name if source else 'Pedido'
            for sub in waiter_subs:
                send_push(sub,{"title":"🍽️ Pedido listo","body":f"{name} está listo para entregar.","url":"/waiter","tag":f"ready-{q.id}"})
            _seen_ready_items.add(key)

        # Limpieza de memoria de eventos antiguos.
        if len(_seen_waiter_calls)>500: _seen_waiter_calls.clear()
        if len(_seen_ready_items)>500: _seen_ready_items.clear()
        db.commit(); _last_new_scan=now
    finally:
        db.close()
