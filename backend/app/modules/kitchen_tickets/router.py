from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.core.database import get_db

from .service import KitchenTicketService

router = APIRouter(

    prefix="/kitchen-tickets",

    tags=["Kitchen Tickets"]

)

service = KitchenTicketService()


@router.get("/")

def list_ticket(

    db: Session = Depends(get_db)

):

    return service.list(db)