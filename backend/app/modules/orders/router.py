from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.core.database import get_db

from .schemas import OrderCreate

from .service import OrderService

router = APIRouter(

    prefix="/orders",

    tags=["Orders"]

)

service = OrderService()


@router.post("/")

def create_order(

    data: OrderCreate,

    db: Session = Depends(get_db)

):

    return service.create(db, data)


@router.get("/")

def list_orders(

    db: Session = Depends(get_db)

):

    return service.list(db)