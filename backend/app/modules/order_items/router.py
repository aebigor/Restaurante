from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.core.database import get_db

from .schemas import OrderItemCreate

from .service import OrderItemService


router = APIRouter(

    prefix="/order-items",

    tags=["Order Items"]

)

service = OrderItemService()


@router.post("/")

def create(

    data: OrderItemCreate,

    db: Session = Depends(get_db)

):

    return service.create(db, data)


@router.get("/")

def list_items(

    db: Session = Depends(get_db)

):

    return service.list(db)