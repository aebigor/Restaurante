import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String


def gen_uuid():
    return str(uuid.uuid4())


# String(36) en vez del tipo UUID nativo de Postgres: portable entre SQLite (dev)
# y Postgres (prod) sin cambiar codigo al cambiar DATABASE_URL.
class AuditMixin:
    """Campos de auditoria estandar (seccion 7.3 del documento de arquitectura)."""

    id = Column(String(36), primary_key=True, default=gen_uuid)
    creado_por = Column(String(36), nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_por = Column(String(36), nullable=True)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    eliminado_en = Column(DateTime, nullable=True)
