from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.schemas import LoginRequest
from app.modules.auth.service import AuthService
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    service = AuthService(db)

    return service.login(
        data.email,
        data.password
    )
@router.get("/me")
def me(
    current_user=Depends(get_current_user),
):

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role.name
        }
    }