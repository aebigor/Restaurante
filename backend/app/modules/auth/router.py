from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, hash_password
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.auth.service import AuthService
from app.modules.roles.model import Role
from app.modules.users.model import User

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(data.email, data.password)


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Crea únicamente cuentas públicas con rol Cliente."""
    email = str(data.email).lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo.")

    role = db.query(Role).filter(Role.name == "Cliente").first()
    if not role:
        role = Role(name="Cliente", description="Cliente frecuente del restaurante")
        db.add(role)
        db.flush()

    user = User(
        full_name=data.full_name.strip(),
        email=email,
        password=hash_password(data.password),
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": role.name,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "role": role.name,
        },
    }


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return {
        "user": {
            "id": str(current_user.id),
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role.name if current_user.role else None,
            "is_active": current_user.is_active,
        }
    }
