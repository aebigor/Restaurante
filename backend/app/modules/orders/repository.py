from sqlalchemy.orm import Session

from .model import Order


class OrderRepository:

    def create(self, db: Session, order: Order):

        db.add(order)

        db.commit()

        db.refresh(order)

        return order


    def get_all(self, db: Session):

        return db.query(Order).all()


    def get_by_id(self, db, id):

        return db.query(Order).filter(
            Order.id == id
        ).first()