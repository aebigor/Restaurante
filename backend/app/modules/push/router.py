from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from .model import PushSubscription
from .service import vapid_public_key
router=APIRouter(prefix="/api/push",tags=["Web Push"])
class SubscriptionKeys(BaseModel):
    p256dh:str; auth:str
class SubscriptionIn(BaseModel):
    endpoint:str=Field(min_length=10,max_length=2000); keys:SubscriptionKeys; station_id:str|None=None
@router.get('/public-key')
def public_key():
    key=vapid_public_key(); return {"enabled":bool(key),"public_key":key}
@router.post('/subscribe')
def subscribe(data:SubscriptionIn,db:Session=Depends(get_db),u=Depends(get_current_user)):
    role=u.role.name if u.role else ''
    if role not in {'Cocina','Mesero'}: raise HTTPException(403,'Las alertas web solo están disponibles para Cocina y Mesero.')
    row=db.query(PushSubscription).filter(PushSubscription.endpoint==data.endpoint).first()
    if not row:
        row=PushSubscription(endpoint=data.endpoint,p256dh=data.keys.p256dh,auth=data.keys.auth,user_id=u.id); db.add(row)
    else:
        row.p256dh=data.keys.p256dh; row.auth=data.keys.auth; row.user_id=u.id
    row.station_id=data.station_id if role=='Cocina' else None
    db.commit(); return {'ok':True,'enabled':bool(settings.WEB_PUSH_VAPID_PRIVATE_KEY and settings.WEB_PUSH_VAPID_EMAIL)}
@router.delete('/unsubscribe')
def unsubscribe(endpoint:str,db:Session=Depends(get_db),u=Depends(get_current_user)):
    row=db.query(PushSubscription).filter(PushSubscription.endpoint==endpoint,PushSubscription.user_id==u.id).first()
    if row: db.delete(row); db.commit()
    return {'ok':True}
