from sqlalchemy.orm import Session

from .repository import KitchenQueueRepository
from .model import KitchenQueue

repository = KitchenQueueRepository()


class KitchenQueueService:


    def create(self, db: Session, data):

        queue = KitchenQueue(

            station_id=data.station_id,

            order_item_id=data.order_item_id

        )

        return repository.create(db, queue)


    def list(self, db: Session):

        return repository.get_all(db)


    def waiting(self, db: Session):

        return repository.get_waiting(db)