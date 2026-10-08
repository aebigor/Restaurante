from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.modules.categories.model import Category
from app.modules.stations.model import Station
from .repository import ProductRepository
from .model import Product
from .inventory_recipe_service import save_recipe

repository = ProductRepository()

class ProductService:
    def _validate_refs(self, db, data):
        category = db.query(Category).filter(Category.id == data.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="La categoría no existe.")
        station = db.query(Station).filter(Station.id == data.station_id, Station.active.is_(True)).first()
        if not station:
            raise HTTPException(status_code=404, detail="La estación no existe o está inactiva.")

    def create(self, db: Session, data):
        self._validate_refs(db, data)
        product = Product(name=data.name.strip(), code=data.code.strip() if data.code else None,
                          description=data.description.strip() if data.description else None,
                          price=data.price, preparation_time=data.preparation_time, stock=data.stock,
                          active=data.active, category_id=data.category_id, station_id=data.station_id)
        db.add(product); db.flush()
        save_recipe(db, product.id, data.inventory_recipe)
        db.commit(); db.refresh(product)
        return product

    def update(self, db: Session, product_id, data):
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(404, "Producto no encontrado.")
        self._validate_refs(db, data)
        for field in ("name", "code", "description", "price", "preparation_time", "stock", "active", "category_id", "station_id"):
            value = getattr(data, field)
            if field in ("name", "code", "description") and value:
                value = value.strip()
            setattr(product, field, value)
        save_recipe(db, product.id, data.inventory_recipe)
        db.commit(); db.refresh(product)
        return product

    def list(self, db: Session):
        return repository.get_all(db)
