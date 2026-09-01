from sqlalchemy.orm import Session

from .model import OrderItem


class OrderItemRepository:

    def create(self, db: Session, item: OrderItem):

        db.add(item)

        db.commit()

        db.refresh(item)

        return item

    def get_by_order(self, db: Session, order_id):

        return db.query(OrderItem).filter(
            OrderItem.order_id == order_id
        ).all()