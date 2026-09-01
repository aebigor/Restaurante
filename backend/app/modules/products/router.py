from fastapi import APIRouter,Depends

from sqlalchemy.orm import Session

from app.core.database import get_db

from .schemas import ProductCreate

from .service import ProductService

router=APIRouter(prefix="/api/products",tags=["Products"])

service=ProductService()


@router.post("/")

def create(data:ProductCreate,db:Session=Depends(get_db)):

    return service.create(db,data)


@router.get("/")

def list_products(db:Session=Depends(get_db)):

    return service.list(db)