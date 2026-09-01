from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.core.database import get_db

from .schemas import (
    OrderBatchCreate,
    OrderBatchResponse
)

from .service import OrderBatchService

router = APIRouter(
    prefix="/order-batches",
    tags=["Order Batches"]
)

service = OrderBatchService()


@router.post(
    "/",
    response_model=OrderBatchResponse
)
def create(
    data: OrderBatchCreate,
    db: Session = Depends(get_db)
):

    return service.create(db, data)


@router.get(
    "/",
    response_model=list[OrderBatchResponse]
)
def list_batches(
    db: Session = Depends(get_db)
):

    return service.list(db)