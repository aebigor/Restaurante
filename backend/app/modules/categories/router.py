from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.modules.categories.repository import CategoryRepository
from app.modules.categories.service import CategoryService
from app.modules.categories.schema import (
    CategoryCreate,
    CategoryUpdate
)

router = APIRouter(

    prefix="/api/categories",

    tags=["Categories"]

)


# ==========================================
# LISTAR
# ==========================================

@router.get("/")
def get_categories(

    db: Session = Depends(get_db)

):

    service = CategoryService(

        CategoryRepository(db)

    )

    return service.get_all()


# ==========================================
# SOLO ACTIVAS
# ==========================================

@router.get("/active")
def get_active_categories(

    db: Session = Depends(get_db)

):

    service = CategoryService(

        CategoryRepository(db)

    )

    return service.get_active()


# ==========================================
# DASHBOARD
# ==========================================

@router.get("/dashboard")
def dashboard(

    db: Session = Depends(get_db)

):

    service = CategoryService(

        CategoryRepository(db)

    )

    return service.dashboard()


# ==========================================
# OBTENER
# ==========================================

@router.get("/{category_id}")
def get_category(

    category_id: UUID,

    db: Session = Depends(get_db)

):

    service = CategoryService(

        CategoryRepository(db)

    )

    return service.get(category_id)


# ==========================================
# CREAR
# ==========================================

@router.post("/")
def create_category(

    data: CategoryCreate,

    db: Session = Depends(get_db)

):

    service = CategoryService(

        CategoryRepository(db)

    )

    return service.create(data)


# ==========================================
# ACTUALIZAR
# ==========================================

@router.put("/{category_id}")
def update_category(

    category_id: UUID,

    data: CategoryUpdate,

    db: Session = Depends(get_db)

):

    service = CategoryService(

        CategoryRepository(db)

    )

    return service.update(

        category_id,

        data

    )


# ==========================================
# ELIMINAR
# ==========================================

@router.delete("/{category_id}")
def delete_category(

    category_id: UUID,

    db: Session = Depends(get_db)

):

    service = CategoryService(

        CategoryRepository(db)

    )

    return service.delete(category_id)