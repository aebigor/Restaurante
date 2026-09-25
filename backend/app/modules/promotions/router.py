from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from .model import Promotion
from .schemas import PromotionCreate, PromotionUpdate, PromotionResponse

router = APIRouter(prefix="/promotions", tags=["Promotions"])

@router.get("/", response_model=list[PromotionResponse])
def list_promotions(active_only: bool = True, db: Session = Depends(get_db)):
    q = db.query(Promotion)
    if active_only:
        q = q.filter(Promotion.active == True)
    return q.order_by(Promotion.display_order.asc(), Promotion.created_at.desc()).all()

@router.post("/", response_model=PromotionResponse)
def create_promotion(data: PromotionCreate, db: Session = Depends(get_db)):
    item = Promotion(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/{promotion_id}", response_model=PromotionResponse)
def update_promotion(promotion_id: UUID, data: PromotionUpdate, db: Session = Depends(get_db)):
    item = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not item: raise HTTPException(404, "Promoción no encontrada.")
    for key, value in data.model_dump().items(): setattr(item, key, value)
    db.commit(); db.refresh(item)
    return item

@router.delete("/{promotion_id}")
def delete_promotion(promotion_id: UUID, db: Session = Depends(get_db)):
    item = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not item: raise HTTPException(404, "Promoción no encontrada.")
    item.active = False; db.commit()
    return {"ok": True}
