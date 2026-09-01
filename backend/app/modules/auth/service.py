from fastapi import HTTPException, status

from app.core.security import create_access_token
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


class AuthService:

    def __init__(self, db):

        self.user_service = UserService(
            UserRepository(db)
        )

    # ==========================================
    # LOGIN
    # ==========================================

    def login(
        self,
        email: str,
        password: str
    ):

        user = self.user_service.authenticate(

            email,

            password

        )

        if not user:

            raise HTTPException(

                status_code=status.HTTP_401_UNAUTHORIZED,

                detail="Correo o contraseña incorrectos."

            )

        token = create_access_token(

            {

                "sub": str(user.id),

                "email": user.email,

                "role": user.role.name

            }

        )

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