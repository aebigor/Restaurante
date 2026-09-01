from sqlalchemy.orm import Session

from .repository import OrderBatchRepository
from .model import OrderBatch

from app.modules.kitchen_tickets.service import KitchenTicketService

repository = OrderBatchRepository()

ticket_service = KitchenTicketService()


class OrderBatchService:

    def create(self, db: Session, data):

        batch = OrderBatch(

            order_id=data.order_id,

            station_id=data.station_id

        )

        return repository.create(db, batch)


    def list(self, db: Session):

        return repository.get_all(db)


    def get_or_create(

        self,

        db: Session,

        order_id,

        station_id

    ):

        batch = repository.find_by_order_station(

            db,

            order_id,

            station_id

        )

        if batch:

            return batch

        batch = OrderBatch(

            order_id=order_id,

            station_id=station_id

        )

        batch = repository.create(

            db,

            batch

        )

        ticket_service.create(

            db,

            batch.id,

            station_id

        )

        return batch