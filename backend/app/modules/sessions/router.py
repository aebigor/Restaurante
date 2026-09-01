from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.core.database import get_db

from .schemas import SessionCreate

from .service import SessionService

from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)

service = SessionService()


@router.post("/")
def create_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return service.create(
        db,
        data,
        current_user
    )

@router.get("/")
def open_sessions(

    db: Session = Depends(get_db)

):

    return service.list_open(db)