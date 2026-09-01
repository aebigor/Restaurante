from sqlalchemy.orm import Session

from .repository import OrderRepository
from .model import Order

repository = OrderRepository()


class OrderService:

    def create(self, db: Session, data):

        order = Order(

            session_id=data.session_id,

            status="OPEN"

        )

        return repository.create(db, order)


    def list(self, db: Session):

        return repository.get_all(db)