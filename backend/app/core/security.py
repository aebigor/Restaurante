"""
=========================================================
Seguridad Global

Toda la autenticación del ERP pasa por aquí.

Funciones:

- Hash de contraseñas
- Verificación
- JWT
=========================================================
"""

from datetime import datetime, timedelta, UTC

from jose import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# =====================================================
# Configuración del algoritmo de hash
# =====================================================

password_hash = PasswordHash.recommended()


# =====================================================
# Crear hash
# =====================================================

def hash_password(password: str) -> str:
    return password_hash.hash(password)


# =====================================================
# Verificar contraseña
# =====================================================

def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return password_hash.verify(
        plain_password,
        hashed_password
    )


# =====================================================
# Crear Access Token
# =====================================================

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
):

    payload = data.copy()

    if expires_delta:

        expire = datetime.now(UTC) + expires_delta

    else:

        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload.update(
        {
            "exp": expire
        }
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )