from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.modules.inventory.model import InventoryItem
from .model import Product
from .schemas import ProductCreate, ProductResponse
from .service import ProductService
from .inventory_recipe_service import get_recipe

router = APIRouter(prefix="/api/products", tags=["Products"])
service = ProductService()

def serialize_product(product: Product):
    return {
        "id": product.id, "name": product.name, "code": product.code, "description": product.description,
        "price": product.price, "preparation_time": product.preparation_time, "stock": product.stock,
        "active": product.active, "category_id": product.category_id, "station_id": product.station_id,
        "category": product.category.name if product.category else None,
        "station": product.station.name if product.station else None,
    }

def _payload(product, db):
    data = serialize_product(product)
    data["inventory_recipe"] = [
        {"id": str(r.id), "inventory_item_id": str(r.inventory_item_id), "name": r.inventory_item.name,
         "category": r.inventory_item.category, "unit": r.inventory_item.unit,
         "quantity_per_sale": float(r.quantity_per_sale), "quantity": float(r.quantity_per_sale)}
        for r in get_recipe(db, product.id)
    ]
    data["inventory_controlled"] = bool(data["inventory_recipe"])
    return data

@router.post("/", response_model=ProductResponse)
def create(data: ProductCreate, db: Session = Depends(get_db)):
    return _payload(service.create(db, data), db)

@router.put("/{product_id}", response_model=ProductResponse)
def update(product_id: UUID, data: ProductCreate, db: Session = Depends(get_db)):
    return _payload(service.update(db, product_id, data), db)

@router.get("/inventory-options")
def inventory_options(db: Session = Depends(get_db)):
    items = db.query(InventoryItem).filter(InventoryItem.active.is_(True)).order_by(InventoryItem.category, InventoryItem.name).all()
    return [{"id": str(i.id), "name": i.name, "category": i.category, "unit": i.unit,
             "quantity": float(i.quantity), "min_quantity": float(i.min_quantity),
             "status": "SIN STOCK" if float(i.quantity) <= 0 else "POR AGOTARSE" if float(i.min_quantity) > 0 and float(i.quantity) <= float(i.min_quantity) else "OK"}
            for i in items]

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    product = db.query(Product).options(joinedload(Product.category), joinedload(Product.station)).filter(Product.id == product_id).first()
    if not product: from fastapi import HTTPException; raise HTTPException(404, "Producto no encontrado.")
    return _payload(product, db)

@router.get("/", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).options(joinedload(Product.category), joinedload(Product.station)).order_by(Product.name.asc()).all()
    return [_payload(product, db) for product in products]
