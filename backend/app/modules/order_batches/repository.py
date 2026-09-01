from sqlalchemy.orm import Session

from .model import OrderBatch


class OrderBatchRepository:


    def create(self, db: Session, batch: OrderBatch):

        db.add(batch)

        db.commit()

        db.refresh(batch)

        return batch


    def get_all(self, db: Session):

        return db.query(OrderBatch).all()

    def find_by_order_station(
        self,
        db,
        order_id: UUID,
        station_id: UUID
    ):

        return (

            db.query(OrderBatch)

            .filter(

                OrderBatch.order_id == order_id,

                OrderBatch.station_id == station_id

            )

            .first()

        )