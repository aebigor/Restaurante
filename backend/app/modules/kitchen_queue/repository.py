from sqlalchemy.orm import Session

from .model import KitchenQueue


class KitchenQueueRepository:


    def create(self, db: Session, queue):

        db.add(queue)

        db.commit()

        db.refresh(queue)

        return queue


    def get_all(self, db: Session):

        return db.query(KitchenQueue).all()


    def get_waiting(self, db: Session):

        return (

            db.query(KitchenQueue)

            .filter(KitchenQueue.status == "WAITING")

            .all()

        )


    def update(self, db: Session, queue):

        db.commit()

        db.refresh(queue)

        return queue