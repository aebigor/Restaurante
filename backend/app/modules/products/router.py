from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db

from .model import Product
from .schemas import ProductCreate, ProductResponse
from .service import ProductService

router = APIRouter(prefix="/api/products", tags=["Products"])
service = ProductService()


def serialize_product(product: Product):
    return {
        "id": product.id,
        "name": product.name,
        "code": product.code,
        "description": product.description,
        "price": product.price,
        "preparation_time": product.preparation_time,
        "stock": product.stock,
        "active": product.active,
        "category_id": product.category_id,
        "station_id": product.station_id,
        "category": product.category.name if product.category else None,
        "station": product.station.name if product.station else None,
    }


@router.post("/", response_model=ProductResponse)
def create(data: ProductCreate, db: Session = Depends(get_db)):
    return serialize_product(service.create(db, data))


@router.get("/", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.station))
        .order_by(Product.name.asc())
        .all()
    )
    return [serialize_product(product) for product in products]
