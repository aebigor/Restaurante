"""
=========================================================
Configuración de la Base de Datos.

Este archivo crea el motor de conexión con PostgreSQL,
la sesión de base de datos y la clase Base que heredarán
todos los modelos del proyecto.
=========================================================
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{settings.DATABASE_USER}:"
    f"{settings.DATABASE_PASSWORD}@"
    f"{settings.DATABASE_HOST}:"
    f"{settings.DATABASE_PORT}/"
    f"{settings.DATABASE_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    """
    Clase base para todos los modelos.
    """
    pass


def get_db():
    """
    Generador de sesiones para FastAPI.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()