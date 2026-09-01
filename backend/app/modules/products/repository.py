from sqlalchemy.orm import Session

from .model import Product


class ProductRepository:

    def create(self,db:Session,product:Product):

        db.add(product)

        db.commit()

        db.refresh(product)

        return product


    def get_all(self,db:Session):

        return db.query(Product).all()
    
    def get_by_id(self, db, id):

        return db.query(Product).filter(
            Product.id == id
        ).first()