from sqlalchemy.orm import Session

from .repository import ProductRepository

from .model import Product


repository=ProductRepository()


class ProductService:


    def create(self,db,data):

        product=Product(

            name=data.name,

            description=data.description,

            price=data.price,

            station_id=data.station_id

        )

        return repository.create(db,product)


    def list(self,db):

        return repository.get_all(db)