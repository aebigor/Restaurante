from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from .model import WaiterCall
from .schemas import WaiterCallCreate, WaiterCallUpdate, WaiterCallResponse

router = APIRouter(prefix="/api/waiter-calls", tags=["Waiter Calls"])

@router.post("/", response_model=WaiterCallResponse)
def create_call(data: WaiterCallCreate, db: Session = Depends(get_db)):
    call = WaiterCall(table_id=data.table_id, session_id=data.session_id)
    db.add(call); db.commit(); db.refresh(call)
    return call

@router.get("/", response_model=list[WaiterCallResponse])
def list_calls(db: Session = Depends(get_db)):
    return db.query(WaiterCall).order_by(WaiterCall.requested_at.asc()).all()

@router.get("/pending", response_model=list[WaiterCallResponse])
def pending_calls(db: Session = Depends(get_db)):
    return db.query(WaiterCall).filter(WaiterCall.status.in_(["REQUESTED", "ACKNOWLEDGED"])).order_by(WaiterCall.requested_at.asc()).all()

@router.patch("/{call_id}", response_model=WaiterCallResponse)
def update_call(call_id: str, data: WaiterCallUpdate, db: Session = Depends(get_db)):
    call = db.query(WaiterCall).filter(WaiterCall.id == call_id).first()
    if not call:
        raise HTTPException(404, "Solicitud no encontrada")
    call.status = data.status
    if data.waiter_id:
        call.waiter_id = data.waiter_id
    if data.status == "ACKNOWLEDGED" and not call.acknowledged_at:
        call.acknowledged_at = datetime.utcnow()
    if data.status == "ATTENDED" and not call.attended_at:
        call.attended_at = datetime.utcnow()
    db.commit(); db.refresh(call)
    return call
