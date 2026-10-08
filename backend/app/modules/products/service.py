from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.categories.model import Category
from app.modules.stations.model import Station

from .repository import ProductRepository
from .model import Product


repository = ProductRepository()


class ProductService:
    def create(self, db: Session, data):
        category = db.query(Category).filter(Category.id == data.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="La categoría no existe.")

        station = db.query(Station).filter(Station.id == data.station_id, Station.active.is_(True)).first()
        if not station:
            raise HTTPException(status_code=404, detail="La estación no existe o está inactiva.")

        product = Product(
            name=data.name.strip(),
            code=data.code.strip() if data.code else None,
            description=data.description.strip() if data.description else None,
            price=data.price,
            preparation_time=data.preparation_time,
            stock=data.stock,
            active=data.active,
            category_id=data.category_id,
            station_id=data.station_id,
        )
        return repository.create(db, product)

    def list(self, db: Session):
        return repository.get_all(db)
