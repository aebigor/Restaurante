from sqlalchemy.orm import Session

from .model import KitchenTicket


class KitchenTicketRepository:


    def create(self, db: Session, ticket: KitchenTicket):

        db.add(ticket)

        db.commit()

        db.refresh(ticket)

        return ticket


    def get_all(self, db: Session):

        return db.query(KitchenTicket).all()