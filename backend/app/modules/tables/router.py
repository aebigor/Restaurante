from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.modules.tables.schema import (
    TableCreate,
    TableUpdate
)

from app.modules.tables.service import TableService


router = APIRouter(
    prefix="/api/tables",
    tags=["Tables"]
)


# ===========================================
# LISTAR
# ===========================================

@router.get("/")
def get_tables(db: Session = Depends(get_db)):

    service = TableService(db)

    return service.get_all()


# ===========================================
# DASHBOARD
# ===========================================

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):

    service = TableService(db)

    return service.dashboard()


# ===========================================
# OBTENER
# ===========================================

@router.get("/{table_id}")
def get_table(
    table_id: int,
    db: Session = Depends(get_db)
):

    service = TableService(db)

    return service.get(table_id)


# ===========================================
# CREAR
# ===========================================

@router.post("/")
def create_table(
    data: TableCreate,
    db: Session = Depends(get_db)
):

    service = TableService(db)

    return service.create(data)


# ===========================================
# ACTUALIZAR
# ===========================================

@router.put("/{table_id}")
def update_table(
    table_id: int,
    data: TableUpdate,
    db: Session = Depends(get_db)
):

    service = TableService(db)

    return service.update(table_id, data)


# ===========================================
# ELIMINAR
# ===========================================

@router.delete("/{table_id}")
def delete_table(
    table_id: int,
    db: Session = Depends(get_db)
):

    service = TableService(db)

    return service.delete(table_id)