from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from .model import Screen
from .schemas import ScreenCreate, ScreenResponse
router = APIRouter(prefix="/api/screens", tags=["Screens"])
@router.get("/", response_model=list[ScreenResponse])
def list_screens(db: Session = Depends(get_db)):
    return db.query(Screen).order_by(Screen.name.asc()).all()
@router.post("/", response_model=ScreenResponse)
def create_screen(data: ScreenCreate, db: Session = Depends(get_db)):
    if db.query(Screen).filter(Screen.code == data.code).first():
        raise HTTPException(400, "El código de pantalla ya existe")
    screen = Screen(**data.model_dump()); db.add(screen); db.commit(); db.refresh(screen); return screen


@router.post("/ensure/{station_id}")
def ensure_station_screen(station_id: str, db: Session = Depends(get_db)):
    from app.modules.stations.model import Station
    station = db.query(Station).filter(Station.id == station_id, Station.active == True).first()
    if not station:
        raise HTTPException(404, "Estación no encontrada")
    existing = db.query(Screen).filter(Screen.station_id == station.id, Screen.active == True).order_by(Screen.name.asc()).first()
    if existing:
        return {"code": existing.code, "name": existing.name, "station_id": str(station.id), "created": False}
    base = "TV-" + "".join(ch if ch.isalnum() else "-" for ch in station.name.upper()).strip("-")
    code = base
    n = 1
    while db.query(Screen).filter(Screen.code == code).first():
        n += 1
        code = f"{base}-{n:02d}"
    screen = Screen(station_id=station.id, name=f"Pantalla {station.name}", code=code, active=True)
    db.add(screen); db.commit(); db.refresh(screen)
    return {"code": screen.code, "name": screen.name, "station_id": str(station.id), "created": True}

@router.post("/{code}/heartbeat")
def heartbeat(code: str, db: Session = Depends(get_db)):
    screen = db.query(Screen).filter(Screen.code == code, Screen.active == True).first()
    if not screen: raise HTTPException(404, "Pantalla no encontrada")
    screen.last_seen_at = datetime.utcnow(); db.commit()
    return {"ok": True}

@router.get("/{code}/queue")
def screen_queue(code: str, db: Session = Depends(get_db)):
    from app.modules.kitchen_queue.model import KitchenQueue
    from app.modules.order_items.model import OrderItem
    from sqlalchemy.orm import joinedload
    screen = db.query(Screen).filter(Screen.code == code, Screen.active == True).first()
    if not screen: raise HTTPException(404, "Pantalla no encontrada")
    screen.last_seen_at = datetime.utcnow()
    rows = db.query(KitchenQueue).filter(KitchenQueue.station_id == screen.station_id, KitchenQueue.status.in_(["WAITING", "PREPARING"])).options(joinedload(KitchenQueue.order_item).joinedload(OrderItem.dish), joinedload(KitchenQueue.order_item).joinedload(OrderItem.product)).order_by(KitchenQueue.created_at.asc()).all()
    db.commit()
    result=[]
    from app.modules.orders.model import Order
    from app.modules.sessions.model import Session as RestaurantSession
    from app.modules.tables.model import Table
    for q in rows:
        item=q.order_item; source=(item.dish if item and item.dish else item.product)
        table_number = None
        if item:
            order = db.query(Order).filter(Order.id == item.order_id).first()
            if order:
                sess = db.query(RestaurantSession).filter(RestaurantSession.id == order.session_id).first()
                if sess:
                    table = db.query(Table).filter(Table.id == sess.table_id).first()
                    table_number = table.number if table else None
        result.append({"id":str(q.id),"name":source.name if source else "Producto","quantity":item.quantity if item else 1,"status":q.status,"created_at":q.created_at,"started_at":q.started_at,"order_id":str(item.order_id) if item else None,"table":table_number})
    return {"screen": screen.name, "station_id":str(screen.station_id), "items":result}
