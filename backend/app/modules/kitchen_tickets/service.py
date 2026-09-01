from sqlalchemy.orm import Session

from .repository import KitchenTicketRepository

from .model import KitchenTicket

repository = KitchenTicketRepository()


class KitchenTicketService:


    def create(

        self,

        db,

        batch_id,

        station_id

    ):

        ticket = KitchenTicket(

            batch_id=batch_id,

            station_id=station_id

        )

        return repository.create(

            db,

            ticket

        )


    def list(self, db):

        return repository.get_all(db)